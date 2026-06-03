"""Progress 5.4 realtime camera geometry and shutter/report runtime."""

from __future__ import annotations

import base64
import csv
import html
import os
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from .environment import build_environment_status
from .inference_model_adapter import run_model_inference
from .model_handoff import check_model_handoff
from .paths import PROJECT_ROOT
from .progress5_4_clearance_estimator import estimate_clearance_from_detections
from .progress5_4_geometry_config import load_geometry_config, load_stability_config
from .progress5_4_measurement_quality import build_progress5_4_quality
from .progress5_4_temporal_smoothing import Progress54TemporalSmoother
from .progress5_4_zone_policy import classify_progress5_4_zone

FIELD_CAPTURE_DIRNAME = "field_captures"
PROGRESS5_4_REPORT_CSV = PROJECT_ROOT / "outputs" / "reports" / "progress5_4_shutter_report.csv"
PROGRESS5_4_MAP_HTML = PROJECT_ROOT / "outputs" / "maps" / "progress5_4_latest_map.html"
MAX_SHUTTER_IMAGE_BYTES = 1_500_000

PROGRESS5_4_REPORT_COLUMNS = [
    "report_id",
    "timestamp",
    "point_id",
    "gps_lat",
    "gps_lon",
    "gps_accuracy_m",
    "gps_source",
    "model_status",
    "debug_mode",
    "detected_classes",
    "pole_detected",
    "conductor_detected",
    "tree_detected",
    "pole_reference_height_m",
    "pole_pixel_height",
    "meter_per_px",
    "tree_top_px",
    "cable_px",
    "tree_height_m",
    "cable_height_m",
    "clearance_m",
    "zone_status",
    "eta_days",
    "risk_level",
    "action_recommendation",
    "latency_ms",
    "smoothing_status",
    "calibration_status",
    "confidence_status",
    "environment_status",
    "rainfall_source",
    "soil_source",
    "season_source",
    "notes",
    "snapshot_path",
    "map_status",
    "reason_codes",
]

_SMOOTHER = Progress54TemporalSmoother()
_LATEST_MEASUREMENT: dict[str, Any] = {"status": "NO_PROGRESS5_4_MEASUREMENT_YET"}
_LATEST_GPS: dict[str, Any] = {"status": "GPS_NOT_READY"}
_LATEST_REPORT: dict[str, Any] = {"status": "NO_PROGRESS5_4_REPORT_YET"}
_LATEST_MAP: dict[str, Any] = {"status": "NO_PROGRESS5_4_MAP_YET"}


def progress5_4_realtime_status() -> dict[str, Any]:
    model = check_model_handoff()
    stability = load_stability_config()
    return {
        "status": "PROGRESS5_4_REALTIME_CAMERA_STATUS_READY",
        "model_status": model["model_status"],
        "debug_coco_status": "DEBUG_COCO_AVAILABLE_ONLY_WITH_EXPLICIT_OPERATOR_OPT_IN",
        "camera_workflow": "BROWSER_CAMERA_OVERLAY_SHUTTER",
        "frame_process_fps": stability["frame_process_fps"],
        "result_update_interval_ms": stability["result_update_interval_ms"],
        "max_allowed_latency_ms": stability["max_allowed_latency_ms"],
        "shutter_endpoint": "/api/field/shutter-capture",
        "realtime_frame_endpoint": "/api/field/realtime-frame",
        "no_fake_detection": True,
        "not_accuracy_claim": True,
    }


def process_progress5_4_realtime_frame(payload: dict[str, Any], *, runtime_root: Path, debug_coco: bool = False) -> dict[str, Any]:
    started = time.perf_counter()
    client_latency = _latency_ms(payload)
    image_status = _image_payload_status(payload)
    if image_status in {"FRAME_TOO_LARGE_DROPPED", "IMAGE_BASE64_INVALID"}:
        result = _base_result(payload, started, status=image_status, detections=[], model_status=check_model_handoff()["model_status"])
        result.update({"reason_codes": [image_status], "no_fake_detection": True})
        _store_latest(result)
        return result

    detections = _run_detection_for_payload(payload, runtime_root=runtime_root, debug_coco=debug_coco)
    measurement = estimate_clearance_from_detections(detections["detections"], geometry_config=load_geometry_config(), latency_ms=client_latency)
    if detections["model_status"] == "MODEL_NOT_READY":
        measurement["reason_codes"] = _dedupe([*measurement.get("reason_codes", []), "MODEL_NOT_READY"])
    smoothing = _SMOOTHER.update(measurement.get("clearance_m"), object_seen=bool(detections["detections"]))
    clearance_for_zone = smoothing.get("stable_clearance_m") if smoothing.get("stable_clearance_m") is not None else measurement.get("clearance_m")
    zone = classify_progress5_4_zone(clearance_for_zone)
    env = build_environment_status()
    quality = build_progress5_4_quality({**measurement, "model_status": detections["model_status"]}, latency_ms=client_latency, gps_accuracy_m=_to_float(payload.get("gps_accuracy_m")))
    latency_status = "HIGH_LATENCY" if client_latency is not None and client_latency > int(load_stability_config()["max_allowed_latency_ms"]) else "LATENCY_OK"
    reason_codes = _dedupe([*measurement.get("reason_codes", []), *smoothing.get("reason_codes", []), *quality.get("reason_codes", []), latency_status])
    result = {
        **_base_result(payload, started, status="PROGRESS5_4_REALTIME_FRAME_PROCESSED", detections=detections["detections"], model_status=detections["model_status"]),
        "debug_mode": detections["debug_mode"],
        "detection_source": detections["source"],
        "detected_classes": measurement.get("detected_classes", []),
        "overlay_json": _overlay_json(detections["detections"], measurement, zone, smoothing, latency_status),
        "measurement_result": {
            **measurement,
            "clearance_m": clearance_for_zone,
            "raw_clearance_m": measurement.get("clearance_m"),
            "smoothing_status": smoothing.get("smoothing_status"),
            "zone_status": zone["zone_status"],
            "risk_level": zone["risk_level"],
            "action_recommendation": zone["action_recommendation"],
            "eta_days": None if zone["zone_status"] != "TEBANG" else 0,
            "environment_status": env["environment_status"],
            "rainfall_source": env["rainfall_source"],
            "soil_source": env["soil_source"],
            "season_source": env["season_source"],
            "measurement_quality_score": quality["measurement_quality_score"],
            "measurement_quality_label": quality["measurement_quality_label"],
            "reason_codes": reason_codes,
        },
        "object_detected": {
            "pole": bool(measurement.get("pole_detected")),
            "conductor": bool(measurement.get("conductor_detected")),
            "tree": bool(measurement.get("tree_detected")),
        },
        "latency_status": latency_status,
        "reason_codes": reason_codes,
        "no_autosave_on_realtime_frame": True,
        "no_fake_detection": True,
    }
    _store_latest(result)
    return result


def write_progress5_4_shutter_capture(payload: dict[str, Any], *, runtime_root: Path) -> dict[str, Any]:
    report_id = f"P54_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
    measurement = _sanitize_measurement_result(payload.get("measurement_result") or payload.get("latest_measurement") or _LATEST_MEASUREMENT.get("measurement_result") or {})
    model_status = _text(payload.get("model_status") or measurement.get("model_status") or _LATEST_MEASUREMENT.get("model_status"), "MODEL_NOT_READY")
    debug_mode = _bool(payload.get("debug_mode") or measurement.get("debug_mode"))
    if model_status == "MODEL_NOT_READY" and not debug_mode:
        measurement = _force_insufficient_without_model(measurement)
    snapshot = _write_shutter_image(payload, runtime_root=runtime_root, report_id=report_id)
    gps = _gps_status_from_payload(payload)
    env = build_environment_status()
    row = _build_report_row(
        report_id=report_id,
        payload=payload,
        measurement=measurement,
        gps=gps,
        env=env,
        snapshot_path=snapshot.get("snapshot_path", ""),
        model_status=model_status,
        debug_mode=debug_mode,
    )
    map_result = _write_latest_map(row)
    row["map_status"] = map_result["status"]
    _append_report_row(row)
    global _LATEST_REPORT, _LATEST_MAP
    _LATEST_REPORT = {
        "status": "PROGRESS5_4_SHUTTER_REPORT_WRITTEN",
        "report_id": report_id,
        "report_csv_path": str(PROGRESS5_4_REPORT_CSV),
        "report_csv_url": f"/field-reports/{PROGRESS5_4_REPORT_CSV.name}",
        "google_sheets_status": "GOOGLE_SHEETS_NOT_CONFIGURED_LOCAL_CSV_READY",
    }
    _LATEST_MAP = map_result
    return {
        **_LATEST_REPORT,
        "snapshot_status": snapshot["status"],
        "snapshot_path": snapshot.get("snapshot_path"),
        "map_status": map_result["status"],
        "map_path": map_result.get("path"),
        "map_url": f"/field-maps/{Path(map_result['path']).name}" if map_result.get("written") else None,
        "row": row,
        "no_fake_detection": True,
    }


def latest_progress5_4_measurement() -> dict[str, Any]:
    return _LATEST_MEASUREMENT


def latest_progress5_4_report() -> dict[str, Any]:
    return {**_LATEST_REPORT, "report_exists": PROGRESS5_4_REPORT_CSV.exists()}


def latest_progress5_4_map() -> dict[str, Any]:
    return {**_LATEST_MAP, "map_exists": PROGRESS5_4_MAP_HTML.exists()}


def latest_progress5_4_gps_status() -> dict[str, Any]:
    return _LATEST_GPS


def progress5_4_calibration_status() -> dict[str, Any]:
    cfg = load_geometry_config()
    return {
        "status": "CALIBRATION_CONFIG_READY_REFERENCE_STILL_FIELD_DEFAULT"
        if cfg.get("source_status") == "FIELD_DEFAULT_NEEDS_PLN_CONFIRMATION"
        else "CALIBRATION_CONFIG_READY",
        "pole_reference_height_m": cfg.get("default_pole_total_height_m"),
        "visible_height_m": cfg.get("default_pole_visible_height_m"),
        "source_status": cfg.get("source_status"),
        "operator_note": "Tinggi tiang tidak di-hardcode sebagai kebenaran mutlak; dapat diganti dari config atau calibration profile.",
    }


def _run_detection_for_payload(payload: dict[str, Any], *, runtime_root: Path, debug_coco: bool) -> dict[str, Any]:
    if debug_coco:
        return _run_debug_coco(payload, runtime_root=runtime_root)
    model = check_model_handoff()
    if model["model_status"] == "MODEL_NOT_READY":
        return {"model_status": "MODEL_NOT_READY", "source": "MODEL_NOT_READY", "debug_mode": False, "detections": []}
    temp_path = _write_temp_image(payload, runtime_root=runtime_root)
    if temp_path is None:
        return {"model_status": model["model_status"], "source": "REAL_MODEL_IMAGE_NOT_PROVIDED", "debug_mode": False, "detections": []}
    try:
        inference = run_model_inference(temp_path)
        return {
            "model_status": inference.get("status") if inference.get("source") != "REAL_MODEL" else "REAL_MODEL",
            "source": inference.get("source", "REAL_MODEL"),
            "debug_mode": False,
            "detections": inference.get("detections", []),
        }
    finally:
        temp_path.unlink(missing_ok=True)


def _run_debug_coco(payload: dict[str, Any], *, runtime_root: Path) -> dict[str, Any]:
    model_path = os.environ.get("ULP_DEBUG_COCO_MODEL_PATH", "").strip()
    if not model_path:
        local = PROJECT_ROOT / "yolov8n.pt"
        model_path = str(local) if local.exists() else ""
    if not model_path:
        return {
            "model_status": "DEBUG_COCO_YOLO_NOT_FIELD_MODEL_MODEL_FILE_NOT_AVAILABLE",
            "source": "DEBUG_COCO_YOLO_NOT_FIELD_MODEL",
            "debug_mode": True,
            "detections": [],
        }
    temp_path = _write_temp_image(payload, runtime_root=runtime_root)
    if temp_path is None:
        return {
            "model_status": "DEBUG_COCO_YOLO_NOT_FIELD_MODEL_IMAGE_NOT_PROVIDED",
            "source": "DEBUG_COCO_YOLO_NOT_FIELD_MODEL",
            "debug_mode": True,
            "detections": [],
        }
    try:
        inference = run_model_inference(temp_path, model_path=model_path)
        detections = []
        for item in inference.get("detections", []):
            detections.append({**item, "source": "DEBUG_COCO_YOLO_NOT_FIELD_MODEL"})
        return {
            "model_status": "DEBUG_COCO_YOLO_NOT_FIELD_MODEL",
            "source": "DEBUG_COCO_YOLO_NOT_FIELD_MODEL",
            "debug_mode": True,
            "detections": detections,
        }
    finally:
        temp_path.unlink(missing_ok=True)


def _write_temp_image(payload: dict[str, Any], *, runtime_root: Path) -> Path | None:
    data = _decode_image(payload.get("image_jpeg_base64") or payload.get("frame_jpeg_base64"))
    if data is None:
        return None
    temp_dir = runtime_root / "progress5_4_temp"
    temp_dir.mkdir(parents=True, exist_ok=True)
    path = temp_dir / f"frame_{uuid.uuid4().hex[:10]}.jpg"
    path.write_bytes(data)
    return path


def _write_shutter_image(payload: dict[str, Any], *, runtime_root: Path, report_id: str) -> dict[str, Any]:
    data = _decode_image(payload.get("image_jpeg_base64") or payload.get("frame_jpeg_base64"))
    if data is None:
        return {"status": "SNAPSHOT_IMAGE_NOT_PROVIDED_METADATA_ONLY", "snapshot_path": ""}
    if len(data) > MAX_SHUTTER_IMAGE_BYTES:
        return {"status": "SNAPSHOT_IMAGE_TOO_LARGE_DROPPED_METADATA_ONLY", "snapshot_path": ""}
    output_dir = runtime_root / FIELD_CAPTURE_DIRNAME
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / f"{report_id}.jpg"
    path.write_bytes(data)
    return {"status": "SNAPSHOT_IMAGE_WRITTEN_RUNTIME_ONLY", "snapshot_path": str(path)}


def _image_payload_status(payload: dict[str, Any]) -> str:
    encoded = payload.get("image_jpeg_base64") or payload.get("frame_jpeg_base64") or ""
    if not encoded:
        return "NO_IMAGE_PAYLOAD_PREVIEW_ONLY"
    data = _decode_image(encoded)
    if data is None:
        return "IMAGE_BASE64_INVALID"
    if len(data) > MAX_SHUTTER_IMAGE_BYTES:
        return "FRAME_TOO_LARGE_DROPPED"
    return "IMAGE_PAYLOAD_ACCEPTED"


def _decode_image(value: Any) -> bytes | None:
    if value in (None, ""):
        return None
    text = str(value)
    if "," in text and text.startswith("data:"):
        text = text.split(",", 1)[1]
    try:
        return base64.b64decode(text, validate=False)
    except Exception:
        return None


def _base_result(payload: dict[str, Any], started: float, *, status: str, detections: list[dict[str, Any]], model_status: str) -> dict[str, Any]:
    gps = _gps_status_from_payload(payload)
    return {
        "status": status,
        "timestamp": datetime.now().isoformat(),
        "point_id": _text(payload.get("point_id"), "V001_pohon_sono"),
        "model_status": model_status,
        "detections": detections,
        "latency_ms": _latency_ms(payload),
        "processing_time_ms": int((time.perf_counter() - started) * 1000),
        "gps": gps,
        "not_accuracy_claim": True,
    }


def _overlay_json(detections: list[dict[str, Any]], measurement: dict[str, Any], zone: dict[str, Any], smoothing: dict[str, Any], latency_status: str) -> dict[str, Any]:
    boxes = []
    for item in detections:
        bbox = item.get("bbox_xyxy") or item.get("bbox") or []
        if len(bbox) != 4:
            continue
        boxes.append(
            {
                "label": item.get("class_name", ""),
                "bbox": bbox,
                "confidence": item.get("confidence", 0),
                "color": _label_color(str(item.get("class_name", ""))),
            }
        )
    return {
        "status": "PROGRESS5_4_OVERLAY_READY",
        "boxes": boxes,
        "measurement_line": {
            "status": "AVAILABLE" if measurement.get("clearance_m") is not None else "NOT_AVAILABLE",
            "tree_top_px": measurement.get("tree_top_px"),
            "cable_px": measurement.get("cable_px"),
            "clearance_m": smoothing.get("stable_clearance_m") or measurement.get("clearance_m"),
        },
        "zone_status": zone["zone_status"],
        "latency_status": latency_status,
        "draw_client_side": True,
    }


def _build_report_row(
    *,
    report_id: str,
    payload: dict[str, Any],
    measurement: dict[str, Any],
    gps: dict[str, Any],
    env: dict[str, Any],
    snapshot_path: str,
    model_status: str,
    debug_mode: bool,
) -> dict[str, Any]:
    zone = classify_progress5_4_zone(measurement.get("clearance_m"))
    reasons = _dedupe([*measurement.get("reason_codes", []), *([] if gps["status"] == "GPS_ACTIVE" else [gps["status"]])])
    return {
        "report_id": report_id,
        "timestamp": _text(payload.get("timestamp"), datetime.now().isoformat()),
        "point_id": _text(payload.get("point_id"), "V001_pohon_sono"),
        "gps_lat": _csv_value(gps.get("gps_lat")),
        "gps_lon": _csv_value(gps.get("gps_lon")),
        "gps_accuracy_m": _csv_value(gps.get("gps_accuracy_m")),
        "gps_source": gps.get("gps_source"),
        "model_status": model_status,
        "debug_mode": str(bool(debug_mode)).lower(),
        "detected_classes": ";".join(str(item) for item in measurement.get("detected_classes", [])),
        "pole_detected": measurement.get("pole_detected", False),
        "conductor_detected": measurement.get("conductor_detected", False),
        "tree_detected": measurement.get("tree_detected", False),
        "pole_reference_height_m": _csv_value(measurement.get("pole_reference_height_m")),
        "pole_pixel_height": _csv_value(measurement.get("pole_pixel_height")),
        "meter_per_px": _csv_value(measurement.get("meter_per_px")),
        "tree_top_px": _csv_value(measurement.get("tree_top_px")),
        "cable_px": _csv_value(measurement.get("cable_px")),
        "tree_height_m": _csv_value(measurement.get("tree_height_m")),
        "cable_height_m": _csv_value(measurement.get("cable_height_m")),
        "clearance_m": _csv_value(measurement.get("clearance_m")),
        "zone_status": measurement.get("zone_status") or zone["zone_status"],
        "eta_days": _csv_value(measurement.get("eta_days")),
        "risk_level": measurement.get("risk_level") or zone["risk_level"],
        "action_recommendation": measurement.get("action_recommendation") or zone["action_recommendation"],
        "latency_ms": _csv_value(payload.get("latency_ms")),
        "smoothing_status": measurement.get("smoothing_status", ""),
        "calibration_status": measurement.get("calibration_status", "CALIBRATION_NOT_READY"),
        "confidence_status": measurement.get("confidence_status", "CALIBRATION_NOT_READY"),
        "environment_status": env["environment_status"],
        "rainfall_source": env["rainfall_source"],
        "soil_source": env["soil_source"],
        "season_source": env["season_source"],
        "notes": _text(payload.get("notes") or payload.get("operator_notes")),
        "snapshot_path": snapshot_path,
        "map_status": "MAP_PENDING",
        "reason_codes": ";".join(reasons),
    }


def _append_report_row(row: dict[str, Any]) -> None:
    PROGRESS5_4_REPORT_CSV.parent.mkdir(parents=True, exist_ok=True)
    exists = PROGRESS5_4_REPORT_CSV.exists()
    with PROGRESS5_4_REPORT_CSV.open("a", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=PROGRESS5_4_REPORT_COLUMNS)
        if not exists:
            writer.writeheader()
        writer.writerow({key: row.get(key, "") for key in PROGRESS5_4_REPORT_COLUMNS})


def _write_latest_map(row: dict[str, Any]) -> dict[str, Any]:
    lat = _to_float(row.get("gps_lat"))
    lon = _to_float(row.get("gps_lon"))
    if lat is None or lon is None:
        return {"status": "NO_GPS_NO_MARKER", "written": False, "path": str(PROGRESS5_4_MAP_HTML)}
    PROGRESS5_4_MAP_HTML.parent.mkdir(parents=True, exist_ok=True)
    PROGRESS5_4_MAP_HTML.write_text(
        (
            "<!doctype html><html><body>"
            "<h1>Progress 5.4 Latest Field Capture Map</h1>"
            f"<p>lat={lat} lon={lon}</p>"
            f"<p>report_id={html.escape(str(row.get('report_id')))}</p>"
            f"<p>zone_status={html.escape(str(row.get('zone_status')))}</p>"
            f"<p>clearance_m={html.escape(str(row.get('clearance_m')))}</p>"
            "</body></html>"
        ),
        encoding="utf-8",
    )
    return {"status": "MAP_MARKER_WRITTEN", "written": True, "path": str(PROGRESS5_4_MAP_HTML)}


def _gps_status_from_payload(payload: dict[str, Any]) -> dict[str, Any]:
    lat = _to_float(payload.get("gps_lat") or payload.get("latitude") or payload.get("lat"))
    lon = _to_float(payload.get("gps_lon") or payload.get("longitude") or payload.get("lon"))
    accuracy = _to_float(payload.get("gps_accuracy_m"))
    source = _text(payload.get("gps_source"), "GPS_NOT_PROVIDED")
    if lat is None or lon is None:
        status = "GPS_NOT_READY"
    elif accuracy is not None and accuracy > 20:
        status = "LOW_ACCURACY"
    else:
        status = "GPS_ACTIVE"
    result = {"status": status, "gps_lat": lat, "gps_lon": lon, "gps_accuracy_m": accuracy, "gps_source": source}
    global _LATEST_GPS
    _LATEST_GPS = result
    return result


def _sanitize_measurement_result(value: Any) -> dict[str, Any]:
    return dict(value) if isinstance(value, dict) else {}


def _force_insufficient_without_model(measurement: dict[str, Any]) -> dict[str, Any]:
    zone = classify_progress5_4_zone(None)
    return {
        **measurement,
        "detected_classes": [],
        "pole_detected": False,
        "conductor_detected": False,
        "tree_detected": False,
        "clearance_m": None,
        "tree_height_m": None,
        "cable_height_m": None,
        "zone_status": zone["zone_status"],
        "risk_level": zone["risk_level"],
        "action_recommendation": zone["action_recommendation"],
        "calibration_status": "CALIBRATION_NOT_READY",
        "confidence_status": "MODEL_NOT_READY",
        "reason_codes": _dedupe([*measurement.get("reason_codes", []), "MODEL_NOT_READY", "NO_FAKE_DETECTION"]),
    }


def _store_latest(result: dict[str, Any]) -> None:
    global _LATEST_MEASUREMENT
    _LATEST_MEASUREMENT = result


def _latency_ms(payload: dict[str, Any]) -> int | None:
    try:
        client_ms = float(payload.get("timestamp_client_ms"))
        return int(time.time() * 1000 - client_ms)
    except (TypeError, ValueError):
        return _to_int(payload.get("latency_ms"))


def _label_color(label: str) -> str:
    if label == "pohon_sono":
        return "#178447"
    if label == "konduktor":
        return "#d18a00"
    if label == "struktur_penyangga":
        return "#2563eb"
    return "#6b7280"


def _dedupe(items: list[Any]) -> list[str]:
    result: list[str] = []
    for item in items:
        text = str(item)
        if text and text not in result:
            result.append(text)
    return result


def _csv_value(value: Any) -> Any:
    return "" if value is None else value


def _bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"true", "1", "yes", "ya", "on"}


def _text(value: Any, default: str = "") -> str:
    if value in (None, ""):
        return default
    return str(value)


def _to_float(value: Any) -> float | None:
    try:
        if value in (None, ""):
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _to_int(value: Any) -> int | None:
    try:
        if value in (None, ""):
            return None
        return int(float(value))
    except (TypeError, ValueError):
        return None
