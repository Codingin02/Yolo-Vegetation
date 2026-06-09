from __future__ import annotations

from copy import deepcopy
from typing import Any


TREE_CLASS = "pohon_sono"


def build_live_yolo_canonical_output(response: dict[str, Any]) -> dict[str, Any]:
    """Normalize live frame output so the browser, report, and tracking agree.

    Progress 6.20 appended YOLO detections under progress6_20_gps_yolo after
    older measurement/tracking payloads were already built. This function is the
    final pass that copies real tree detections into every operator-facing field
    without inventing pole, conductor, clearance, GPS, or precision values.
    """

    data = deepcopy(response) if isinstance(response, dict) else {}
    progress = data.get("progress6_20_gps_yolo") if isinstance(data.get("progress6_20_gps_yolo"), dict) else {}
    yolo = progress.get("yolo_detection") if isinstance(progress.get("yolo_detection"), dict) else {}
    detections = _normalize_tree_detections(yolo.get("detections") or data.get("detections") or [])
    tree_detected = bool(yolo.get("tree_detected") or detections)

    if tree_detected:
        best = max(detections, key=lambda item: float(item.get("confidence") or 0.0))
        tree_confidence = float(best.get("confidence") or 0.0)
        tree_bbox = list(best.get("bbox_xyxy") or best.get("bbox") or [])

        data.update(
            {
                "tree_detected": True,
                "detected_classes": [TREE_CLASS],
                "detections": detections,
                "tree_confidence": tree_confidence,
                "tree_bbox": tree_bbox,
                "tree_bbox_xyxy": tree_bbox,
                "model_status": "TREE_MODEL_READY_CANDIDATE",
                "tree_model_status": "TREE_MODEL_READY_CANDIDATE",
                "yolo_detection_status": "YOLO_TREE_DETECTED",
                "tracking_status": "YOLO_TREE_DETECTED",
                "tree_tracking_status": "YOLO_TREE_DETECTED",
                "track_id_seen": any(item.get("track_id") is not None for item in detections),
                "tree_track_ids": _tree_track_ids(detections),
            }
        )

        measurement = _measurement(data)
        measurement.update(
            {
                "tree_detected": True,
                "detected_classes": [TREE_CLASS],
                "tree_bbox": tree_bbox,
                "tree_confidence": tree_confidence,
                "pole_detected": False,
                "conductor_detected": False,
            }
        )
        measurement["reason_codes"] = [
            code
            for code in _reason_codes(measurement)
            if code != "TREE_NOT_DETECTED_BY_CANDIDATE_MODEL"
        ]
        if "TREE_MODEL_READY_CANDIDATE_NOT_FINAL" not in measurement["reason_codes"]:
            measurement["reason_codes"].append("TREE_MODEL_READY_CANDIDATE_NOT_FINAL")
        data["measurement_result"] = measurement

        tracking = dict(data.get("progress6_18_tracking") or {})
        tracking.update(
            {
                "tracking_status": "YOLO_TREE_DETECTED",
                "tree_tracking_status": "YOLO_TREE_DETECTED",
                "tree_detected": True,
                "detection_count": len(detections),
                "model_status": "TREE_MODEL_READY_CANDIDATE",
                "track_id_seen": data["track_id_seen"],
                "tree_track_ids": data["tree_track_ids"],
                "no_fake_detection": True,
                "note": "Tree detection comes from live YOLO candidate output; no fake track id is created.",
            }
        )
        data["progress6_18_tracking"] = tracking

        data["overlay_json"] = {
            **(data.get("overlay_json") if isinstance(data.get("overlay_json"), dict) else {}),
            "status": "FIELD_SESSION_OVERLAY_READY",
            "message": "YOLO_TREE_DETECTED",
            "boxes": _overlay_boxes(detections),
            "draw_client_side": True,
        }
    else:
        data["tree_detected"] = False
        data["detected_classes"] = []
        data["detections"] = []
        data["tree_confidence"] = 0.0
        data["tree_bbox"] = None
        data["tree_bbox_xyxy"] = None
        data["yolo_detection_status"] = (
            "YOLO_READY_NO_TREE_DETECTED"
            if yolo.get("model_status") == "TREE_MODEL_READY_CANDIDATE" or data.get("tree_model_status") == "TREE_MODEL_READY_CANDIDATE"
            else data.get("yolo_detection_status", "YOLO_READY_NO_TREE_DETECTED")
        )
        data["overlay_json"] = {
            **(data.get("overlay_json") if isinstance(data.get("overlay_json"), dict) else {}),
            "message": data["yolo_detection_status"],
            "boxes": [],
            "draw_client_side": True,
        }

    data.update(
        {
            "pole_detected": False,
            "conductor_detected": False,
            "pole_model_status": "POLE_MODEL_NOT_READY",
            "conductor_model_status": "CONDUCTOR_MODEL_NOT_READY",
            "no_fake_detection": True,
            "no_fake_pole_conductor_detection": True,
            "canonical_yolo_output_status": "PROGRESS_6_21_CANONICAL_OUTPUT_READY",
        }
    )
    return data


def _normalize_tree_detections(raw: Any) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    if not isinstance(raw, list):
        return out
    for idx, item in enumerate(raw):
        if not isinstance(item, dict):
            continue
        class_name = str(item.get("class_name") or item.get("label") or item.get("class") or TREE_CLASS)
        class_id = int(item.get("class_id") or 0)
        if class_id != 0 and class_name.lower() not in {"pohon_sono", "tree_sono", "sono"}:
            continue
        bbox = _bbox(item)
        if bbox is None:
            continue
        confidence = _float(item.get("confidence", item.get("conf", item.get("score", 0.0))), 0.0)
        track_id = item.get("track_id")
        out.append(
            {
                "class_id": class_id,
                "class_name": TREE_CLASS,
                "confidence": round(confidence, 4),
                "bbox_xyxy": bbox,
                "bbox": bbox,
                "track_id": int(track_id) if isinstance(track_id, (int, float)) else None,
                "detection_index": idx,
            }
        )
    return out


def _bbox(item: dict[str, Any]) -> list[float] | None:
    for key in ("bbox_xyxy", "bbox", "box", "xyxy"):
        value = item.get(key)
        if isinstance(value, list) and len(value) >= 4:
            return [round(_float(v, 0.0), 2) for v in value[:4]]
    coords = [item.get("x1"), item.get("y1"), item.get("x2"), item.get("y2")]
    if all(v is not None for v in coords):
        return [round(_float(v, 0.0), 2) for v in coords]
    return None


def _overlay_boxes(detections: list[dict[str, Any]]) -> list[dict[str, Any]]:
    boxes = []
    for item in detections:
        bbox = list(item.get("bbox_xyxy") or [])
        boxes.append(
            {
                "bbox_xyxy": bbox,
                "bbox": bbox,
                "class_id": item.get("class_id", 0),
                "class_name": TREE_CLASS,
                "label": TREE_CLASS,
                "confidence": item.get("confidence", 0.0),
                "track_id": item.get("track_id"),
            }
        )
    return boxes


def _measurement(data: dict[str, Any]) -> dict[str, Any]:
    measurement = data.get("measurement_result")
    return dict(measurement) if isinstance(measurement, dict) else {}


def _reason_codes(measurement: dict[str, Any]) -> list[str]:
    raw = measurement.get("reason_codes")
    return list(raw) if isinstance(raw, list) else []


def _tree_track_ids(detections: list[dict[str, Any]]) -> list[int]:
    ids = []
    for item in detections:
        track_id = item.get("track_id")
        if isinstance(track_id, int):
            ids.append(track_id)
    return sorted(set(ids))


def _float(value: Any, default: float) -> float:
    try:
        return float(value)
    except Exception:
        return default
