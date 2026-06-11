"""False-positive filtering and detection context summary for Plan C."""

from __future__ import annotations

from typing import Any

from .plan_c_free_vision_schema import apply_detection_nms, reason_has_strong_negative, validate_bbox

TARGET_CLASSES = {"struktur_penyangga", "konduktor", "pohon_sono", "pohon_non_sono"}


def apply_plan_c_quality_layer(detection_result: dict[str, Any], *, image_width: int, image_height: int) -> dict[str, Any]:
    detections = []
    rejected = list(detection_result.get("rejected_detections_redacted") or [])
    for item in detection_result.get("detections") or []:
        if not isinstance(item, dict):
            continue
        class_name = str(item.get("class_name") or "")
        if class_name not in TARGET_CLASSES:
            rejected.append({"raw_label": class_name, "reason": "CLASS_NOT_ALLOWED"})
            continue
        bbox = item.get("bbox_xyxy")
        if not isinstance(bbox, list) or len(bbox) != 4:
            rejected.append({"raw_label": class_name, "reason": "BBOX_MISSING"})
            continue
        validity = validate_bbox([float(value) for value in bbox], image_width=image_width, image_height=image_height, class_name=class_name)
        if not validity.get("valid"):
            rejected.append({"raw_label": class_name, "reason": validity.get("reason")})
            continue
        reason = str(item.get("reason") or "")
        if reason_has_strong_negative(reason, class_name=class_name):
            rejected.append({"raw_label": class_name, "reason": "FALSE_POSITIVE_REASON_REJECTED"})
            continue
        cleaned = dict(item)
        cleaned["review_status"] = _normalize_review(cleaned.get("review_status"))
        detections.append(cleaned)

    detections = apply_detection_nms(detections)
    classes = {item.get("class_name") for item in detections}
    has_tree = bool(classes & {"pohon_sono", "pohon_non_sono"})
    if not has_tree:
        rejected.extend({"raw_label": item.get("class_name"), "reason": "TREE_NOT_CONFIRMED_REJECT_FALSE_POSITIVE"} for item in detections)
        detections = []
        classes = set()

    if len(detections) == 1:
        detections[0]["review_status"] = "REVIEW"
    context = summarize_detection_context(detections)
    result = dict(detection_result)
    result.update(
        {
            "status": "YOLO_COMPATIBLE_DETECTION_READY" if detections else "DATA_TIDAK_CUKUP",
            "detections": detections,
            "detection_count": len(detections),
            "rejected_detections_redacted": rejected[:80],
            "manual_review_required": not detections or any(item.get("review_status") != "ACCEPT" for item in detections),
            "quality_layer_status": "PLAN_C_QUALITY_LAYER_READY",
            **context,
        }
    )
    return result


def summarize_detection_context(detections: list[dict[str, Any]]) -> dict[str, Any]:
    classes = {str(item.get("class_name") or "") for item in detections}
    tree_species_status = "pohon_sono" if "pohon_sono" in classes else "pohon_non_sono" if "pohon_non_sono" in classes else "unknown"
    conductor_status = "tervalidasi" if "konduktor" in classes else "tidak tervalidasi"
    structure_status = "tervalidasi" if "struktur_penyangga" in classes else "tidak tervalidasi"
    zone_status = "unavailable" if conductor_status != "tervalidasi" else "approximate"
    conductor_lines = _conductor_lines(detections)
    return {
        "tree_species_status": tree_species_status,
        "conductor_status": conductor_status,
        "structure_status": structure_status,
        "zone_status": zone_status,
        "conductor_group_count": len(conductor_lines),
        "conductor_lines": conductor_lines,
        "target_tree_detected": tree_species_status != "unknown",
        "conductor_validated": conductor_status == "tervalidasi",
        "structure_validated": structure_status == "tervalidasi",
    }


def _conductor_lines(detections: list[dict[str, Any]]) -> list[dict[str, Any]]:
    lines: list[dict[str, Any]] = []
    for item in detections:
        if item.get("class_name") != "konduktor":
            continue
        bbox = item.get("bbox_xyxy")
        if not isinstance(bbox, list) or len(bbox) != 4:
            continue
        try:
            x1, y1, x2, y2 = [float(value) for value in bbox]
        except (TypeError, ValueError):
            continue
        lines.append(
            {
                "bbox_xyxy": [round(x1, 2), round(y1, 2), round(x2, 2), round(y2, 2)],
                "line_y": round((y1 + y2) / 2.0, 2),
                "confidence": item.get("confidence"),
                "review_status": item.get("review_status"),
            }
        )
    return sorted(lines, key=lambda item: float(item.get("line_y") or 0.0))


def _normalize_review(value: Any) -> str:
    text = str(value or "").strip().upper()
    if text in {"ACCEPT", "REVIEW", "REJECT"}:
        return text
    if text in {"ACCEPTED", "OK"}:
        return "ACCEPT"
    if text in {"REJECTED", "INVALID"}:
        return "REJECT"
    return "REVIEW"


def finalize_session(session_id: str) -> dict[str, Any]:
    """Compatibility shim for older local Plan C UI patches.

    Progress 8.3 finalization is performed inside ``plan_c_processor``. This
    function intentionally avoids rewriting append-only storage or moving
    session files.
    """

    return {"ok": True, "status": "PLAN_C_QUALITY_LAYER_ALREADY_APPLIED", "session_id": session_id}


def compact_active_map_markers(latest_session_id: str | None = None) -> dict[str, Any]:
    """Compatibility shim; active map filtering is handled at read time."""

    return {"ok": True, "status": "PLAN_C_MAP_FILTER_READ_TIME", "session_id": latest_session_id}


def record_operator_feedback(session_id: str, verdict: str, note: str = "") -> dict[str, Any]:
    from .plan_c_feedback_learning import save_operator_feedback

    return save_operator_feedback({"session_id": session_id, "verdict": verdict, "note": note})
