"""Progress 5.2 field trial prediction, report, and map helpers.

This module is intentionally manual/provisional friendly. It never creates
fake detections and writes official monitoring output only on snapshot submit.
"""

from __future__ import annotations

import csv
import html
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from .eta_uncertainty import calculate_eta_to_unsafe_zone
from .map_report_policy import marker_color
from .measurement_quality import build_measurement_quality_report
from .model_handoff import check_model_handoff
from .paths import PROJECT_ROOT
from .report_snapshot_policy import should_write_snapshot_report
from .safety_clearance_policy import floor_display_meter

CLEARANCE_THRESHOLD_M = 3.0
REPORT_DIR = PROJECT_ROOT / "outputs" / "reports"
PHASE5_2_REPORT_CSV = REPORT_DIR / "phase5_2_field_trial_snapshot.csv"
PHASE5_2_MAP_HTML = REPORT_DIR / "phase5_2_field_trial_map.html"

PHASE5_2_REPORT_COLUMNS = [
    "report_id",
    "timestamp",
    "point_id",
    "species",
    "asset_type",
    "latitude",
    "longitude",
    "gps_accuracy_m",
    "gps_source",
    "model_status",
    "inference_source",
    "measurement_source",
    "confidence_status",
    "calibration_status",
    "environment_status",
    "clearance_raw_m",
    "clearance_stabilized_m",
    "clearance_display_m",
    "clearance_threshold_m",
    "growth_rate_m_per_day",
    "adjusted_growth_rate_m_per_day",
    "eta_days",
    "eta_months",
    "risk_status",
    "action_priority",
    "measurement_quality_score",
    "measurement_quality_label",
    "reason_codes",
    "image_reference",
    "map_marker_status",
    "operator_notes",
]


def build_manual_prediction(payload: dict[str, Any]) -> dict[str, Any]:
    model = check_model_handoff()
    model_status = str(model.get("model_status") or "MODEL_NOT_READY")
    clearance_raw = _to_float(payload.get("clearance_raw_m") or payload.get("clearance_m") or payload.get("selected_clearance_m_raw"))
    clearance_stable = _to_float(
        payload.get("clearance_stabilized_m")
        or payload.get("selected_clearance_m_stable")
        or payload.get("stabilized_selected_clearance_m")
        or clearance_raw
    )
    growth_rate = _to_float(payload.get("growth_rate_m_per_day"))
    adjusted_growth_rate = _to_float(payload.get("adjusted_growth_rate_m_per_day")) or growth_rate
    gps = _gps_payload(payload)
    calibration_status = _text(payload.get("calibration_status"), "CALIBRATION_NOT_READY")
    measurement_source = _text(payload.get("measurement_source"), "manual")
    confidence_status = _confidence_status(measurement_source, calibration_status)
    environment_status = _environment_status(payload)

    eta = calculate_eta_to_unsafe_zone(clearance_stable, adjusted_growth_rate, CLEARANCE_THRESHOLD_M)
    eta_days = eta.get("eta_expected_days")
    eta_months = eta.get("eta_expected_months")
    risk_status, action_priority = _risk_and_action(clearance_stable, eta_days, eta.get("eta_status"))
    quality = build_measurement_quality_report(
        {
            "model_status": model_status,
            "calibration_status": calibration_status,
            "tree_detected": model_status != "MODEL_NOT_READY",
            "asset_detected": model_status != "MODEL_NOT_READY",
            "gps_ready": gps["valid"],
            "environmental_data_status": environment_status,
            "latency_ms": payload.get("latency_ms"),
            "structure_reference_ready": measurement_source != "model" or model_status != "MODEL_NOT_READY",
        }
    )
    reason_codes = _reason_codes(quality.get("reason_codes", []), eta.get("eta_status"), model_status, calibration_status, gps)
    status = "MANUAL_PROVISIONAL_PREDICTION_READY" if eta_days is not None else "MANUAL_PROVISIONAL_INSUFFICIENT_DATA"
    if risk_status == "ALREADY_WITHIN_UNSAFE_ZONE":
        status = "MANUAL_PROVISIONAL_UNSAFE_ZONE_REVIEW"
    return {
        "status": status,
        "point_id": _text(payload.get("point_id"), "V001_pohon_sono"),
        "species": _text(payload.get("species"), "pohon_sono"),
        "asset_type": _text(payload.get("asset_type"), "span"),
        "latitude": gps["latitude"],
        "longitude": gps["longitude"],
        "gps_accuracy_m": gps["accuracy_m"],
        "gps_source": gps["source"],
        "gps_status": gps["status"],
        "model_status": model_status,
        "model_handoff": model,
        "inference_source": _inference_source(model_status, measurement_source),
        "detections": [],
        "confidence_status": confidence_status,
        "measurement_source": measurement_source,
        "calibration_status": calibration_status,
        "environment_status": environment_status,
        "clearance_raw_m": clearance_raw,
        "clearance_stabilized_m": clearance_stable,
        "clearance_display_m_integer_floor": floor_display_meter(clearance_stable),
        "clearance_threshold_m": CLEARANCE_THRESHOLD_M,
        "growth_rate_m_per_day": growth_rate,
        "adjusted_growth_rate_m_per_day": adjusted_growth_rate,
        "eta_days": eta_days,
        "eta_months": eta_months,
        "risk_status": risk_status,
        "risk_priority": action_priority,
        "action_priority": action_priority,
        "measurement_quality_score": quality["measurement_quality_score"],
        "measurement_quality_label": quality["measurement_quality_label"],
        "reason_codes": reason_codes,
        "image_reference": _text(payload.get("image_reference") or payload.get("image_path") or payload.get("photo_path")),
        "map_marker_status": _map_marker_status(gps),
        "operator_notes": _text(payload.get("operator_notes") or payload.get("notes") or payload.get("operator_note")),
        "eta_formula": "(clearance_m - 3.0) / adjusted_growth_rate_m_per_day when clearance_m > 3.0",
        "not_accuracy_claim": True,
        "no_fake_detection": True,
    }


def write_field_trial_snapshot_report(payload: dict[str, Any], output: Path = PHASE5_2_REPORT_CSV, map_output: Path = PHASE5_2_MAP_HTML) -> dict[str, Any]:
    trigger_payload = {"report_trigger": payload.get("report_trigger") or "MANUAL_SNAPSHOT"}
    policy = should_write_snapshot_report(trigger_payload)
    if not policy["write_report"]:
        return {"status": policy["status"], "report_written": False, "policy": policy}
    prediction = build_manual_prediction(payload)
    report_id = _text(payload.get("report_id"), f"P52_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}")
    row = build_report_row(prediction, report_id=report_id, timestamp=_text(payload.get("timestamp"), datetime.now().isoformat()))
    output.parent.mkdir(parents=True, exist_ok=True)
    exists = output.exists()
    with output.open("a", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=PHASE5_2_REPORT_COLUMNS)
        if not exists:
            writer.writeheader()
        writer.writerow(row)
    map_result = write_field_trial_map(row, map_output)
    return {
        **prediction,
        "status": "FIELD_TRIAL_SNAPSHOT_REPORT_WRITTEN",
        "report_id": report_id,
        "report_written": True,
        "report_csv_path": str(output),
        "report_csv_url": f"/field-reports/{output.name}",
        "google_sheets_status": "GOOGLE_SHEETS_NOT_CONFIGURED_LOCAL_CSV_READY",
        "map_status": map_result["status"],
        "map_marker_written": map_result["written"],
        "map_path": map_result["path"],
        "map_url": f"/field-reports/{Path(map_result['path']).name}" if map_result["written"] else None,
        "report_trigger": policy["report_trigger"],
        "row": row,
    }


def build_report_row(prediction: dict[str, Any], *, report_id: str, timestamp: str) -> dict[str, Any]:
    return {
        "report_id": report_id,
        "timestamp": timestamp,
        "point_id": prediction.get("point_id", ""),
        "species": prediction.get("species", ""),
        "asset_type": prediction.get("asset_type", ""),
        "latitude": _csv_value(prediction.get("latitude")),
        "longitude": _csv_value(prediction.get("longitude")),
        "gps_accuracy_m": _csv_value(prediction.get("gps_accuracy_m")),
        "gps_source": prediction.get("gps_source", ""),
        "model_status": prediction.get("model_status", ""),
        "inference_source": prediction.get("inference_source", ""),
        "measurement_source": prediction.get("measurement_source", ""),
        "confidence_status": prediction.get("confidence_status", ""),
        "calibration_status": prediction.get("calibration_status", ""),
        "environment_status": prediction.get("environment_status", ""),
        "clearance_raw_m": _csv_value(prediction.get("clearance_raw_m")),
        "clearance_stabilized_m": _csv_value(prediction.get("clearance_stabilized_m")),
        "clearance_display_m": _csv_value(prediction.get("clearance_display_m_integer_floor")),
        "clearance_threshold_m": _csv_value(prediction.get("clearance_threshold_m")),
        "growth_rate_m_per_day": _csv_value(prediction.get("growth_rate_m_per_day")),
        "adjusted_growth_rate_m_per_day": _csv_value(prediction.get("adjusted_growth_rate_m_per_day")),
        "eta_days": _csv_value(prediction.get("eta_days")),
        "eta_months": _csv_value(prediction.get("eta_months")),
        "risk_status": prediction.get("risk_status", ""),
        "action_priority": prediction.get("action_priority", ""),
        "measurement_quality_score": _csv_value(prediction.get("measurement_quality_score")),
        "measurement_quality_label": prediction.get("measurement_quality_label", ""),
        "reason_codes": ";".join(str(item) for item in prediction.get("reason_codes", [])),
        "image_reference": prediction.get("image_reference", ""),
        "map_marker_status": prediction.get("map_marker_status", ""),
        "operator_notes": prediction.get("operator_notes", ""),
    }


def write_field_trial_map(row: dict[str, Any], output: Path = PHASE5_2_MAP_HTML) -> dict[str, Any]:
    lat = _to_float(row.get("latitude"))
    lon = _to_float(row.get("longitude"))
    if lat is None or lon is None:
        return {"status": "NO_GPS_NO_MARKER", "written": False, "path": str(output), "reason": "NO_GPS_NO_MARKER"}
    output.parent.mkdir(parents=True, exist_ok=True)
    marker_status = "TEST_INTERNAL_NOT_FIELD_DATA" if row.get("gps_source") == "TEST_INTERNAL_NOT_FIELD_DATA" else "MAP_MARKER_WRITTEN"
    popup = "<br>".join(
        html.escape(str(item))
        for item in [
            f"report_id: {row.get('report_id')}",
            f"point_id: {row.get('point_id')}",
            f"species: {row.get('species')}",
            f"asset_type: {row.get('asset_type')}",
            f"clearance_raw_m: {row.get('clearance_raw_m')}",
            f"clearance_display_m: {row.get('clearance_display_m')}",
            f"eta_days: {row.get('eta_days')}",
            f"risk_status: {row.get('risk_status')}",
            f"action_priority: {row.get('action_priority')}",
            f"model_status: {row.get('model_status')}",
            f"gps_source: {row.get('gps_source')}",
            f"notes: {row.get('operator_notes')}",
        ]
    )
    color = marker_color(row.get("action_priority"))
    output.write_text(
        (
            "<!doctype html><html><body>"
            "<h1>Progress 5.2 Field Trial Map</h1>"
            f"<p>marker_status={html.escape(marker_status)} color={html.escape(color)}</p>"
            f"<p>lat={lat} lon={lon}</p>"
            f"<div>{popup}</div>"
            "</body></html>"
        ),
        encoding="utf-8",
    )
    return {"status": marker_status, "written": True, "path": str(output), "marker_color": color}


def phase5_2_runtime_contract_status() -> dict[str, Any]:
    model = check_model_handoff()
    return {
        "status": "PROGRESS_5_2_FIELD_TRIAL_CONTRACT_READY",
        "model_status": model["model_status"],
        "field_capture": "/field-capture",
        "manual_prediction_endpoint": "/api/field/manual-prediction",
        "snapshot_report_endpoint": "/api/field/snapshot-report",
        "report_csv": str(PHASE5_2_REPORT_CSV),
        "map_html": str(PHASE5_2_MAP_HTML),
        "clearance_threshold_m": CLEARANCE_THRESHOLD_M,
        "no_fake_detection": True,
        "not_accuracy_claim": True,
    }


def _risk_and_action(clearance_m: float | None, eta_days: Any, eta_status: Any) -> tuple[str, str]:
    if clearance_m is None or eta_status in {"INSUFFICIENT_CLEARANCE_DATA", "INSUFFICIENT_GROWTH_RATE"}:
        return "INSUFFICIENT_DATA", "INSUFFICIENT_DATA"
    if clearance_m <= CLEARANCE_THRESHOLD_M:
        return "ALREADY_WITHIN_UNSAFE_ZONE", "CRITICAL"
    eta = _to_float(eta_days)
    if eta is None:
        return "INSUFFICIENT_DATA", "INSUFFICIENT_DATA"
    if eta <= 30:
        return "ETA_TO_3M_THRESHOLD_READY", "CRITICAL"
    if eta <= 90:
        return "ETA_TO_3M_THRESHOLD_READY", "HIGH"
    if eta <= 180:
        return "ETA_TO_3M_THRESHOLD_READY", "MEDIUM"
    return "ETA_TO_3M_THRESHOLD_READY", "LOW"


def _gps_payload(payload: dict[str, Any]) -> dict[str, Any]:
    lat = _to_float(payload.get("latitude") or payload.get("lat") or payload.get("gps_lat"))
    lon = _to_float(payload.get("longitude") or payload.get("lon") or payload.get("gps_lon"))
    source = _text(payload.get("gps_source"))
    if str(source).lower() in {"test_internal", "dummy", "dummy_test", "test_internal_not_field_data"}:
        source = "TEST_INTERNAL_NOT_FIELD_DATA"
    elif not source and lat is not None and lon is not None:
        source = "GPS_SOURCE_MANUAL"
    elif not source:
        source = "GPS_NOT_PROVIDED"
    valid = lat is not None and lon is not None
    return {
        "latitude": lat,
        "longitude": lon,
        "accuracy_m": _to_float(payload.get("gps_accuracy_m")),
        "source": source,
        "valid": valid,
        "status": "GPS_VALID" if valid else "GPS_NOT_READY",
    }


def _map_marker_status(gps: dict[str, Any]) -> str:
    if not gps["valid"]:
        return "NO_GPS_NO_MARKER"
    if gps["source"] == "TEST_INTERNAL_NOT_FIELD_DATA":
        return "TEST_INTERNAL_NOT_FIELD_DATA"
    return "MAP_MARKER_READY"


def _confidence_status(measurement_source: str, calibration_status: str) -> str:
    if measurement_source == "manual":
        return "MANUAL_PROVISIONAL"
    if str(calibration_status).startswith("CALIBRATION_NOT"):
        return "CALIBRATION_NOT_READY"
    return "PROVISIONAL"


def _environment_status(payload: dict[str, Any]) -> str:
    source = _text(payload.get("environment_source") or payload.get("environmental_source"))
    if source == "manual_csv":
        return "ENVIRONMENT_MANUAL_CSV_DECLARED"
    return "ENVIRONMENT_NOT_AVAILABLE"


def _inference_source(model_status: str, measurement_source: str) -> str:
    if model_status == "MODEL_NOT_READY":
        return "MANUAL_PROVISIONAL_NO_MODEL" if measurement_source == "manual" else "MODEL_NOT_READY"
    if model_status == "MODEL_PRESENT_CLASS_ORDER_UNVERIFIED":
        return "REAL_MODEL_PRESENT_CLASS_ORDER_UNVERIFIED"
    return "REAL_MODEL_AVAILABLE_VALIDATION_REQUIRED"


def _reason_codes(base: Any, eta_status: Any, model_status: str, calibration_status: str, gps: dict[str, Any]) -> list[str]:
    codes: list[str] = [str(item) for item in base if item]
    if eta_status and eta_status not in {"ETA_TO_3M_THRESHOLD_READY"}:
        codes.append(str(eta_status))
    if model_status == "MODEL_PRESENT_CLASS_ORDER_UNVERIFIED":
        codes.append("MODEL_PRESENT_CLASS_ORDER_UNVERIFIED")
    if str(calibration_status).startswith("CALIBRATION_NOT"):
        codes.append("CALIBRATION_NOT_READY")
    if not gps["valid"]:
        codes.append("NO_GPS_NO_MARKER")
    codes.append("PROVISIONAL_NOT_FINAL_ACCURACY")
    deduped: list[str] = []
    for code in codes:
        if code not in deduped:
            deduped.append(code)
    return deduped


def _csv_value(value: Any) -> Any:
    if value is None:
        return ""
    return value


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
