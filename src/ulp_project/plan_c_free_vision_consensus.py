"""Consensus and de-duplication for YOLO-compatible Plan C detections."""

from __future__ import annotations

from typing import Any

from .plan_c_free_vision_schema import empty_detection_result


def build_detection_consensus(candidates: list[dict[str, Any]], *, image_width: int, image_height: int) -> dict[str, Any]:
    valid_candidates = [candidate for candidate in candidates if candidate.get("detections")]
    if not valid_candidates:
        return empty_detection_result(
            status="DATA_TIDAK_CUKUP",
            image_width=image_width,
            image_height=image_height,
            consensus_status="disabled",
            provider_status_redacted=[_candidate_status(candidate) for candidate in candidates],
        )
    if len(valid_candidates) == 1:
        detections = _nms(valid_candidates[0]["detections"])
        return _result(
            detections,
            image_width=image_width,
            image_height=image_height,
            consensus_status="single_provider",
            provider_status_redacted=[_candidate_status(candidate) for candidate in candidates],
        )

    selected = _nms([detection for candidate in valid_candidates for detection in candidate.get("detections", [])])
    verified_classes = set()
    for left_index, left in enumerate(valid_candidates):
        for right in valid_candidates[left_index + 1 :]:
            for left_box in left.get("detections", []):
                for right_box in right.get("detections", []):
                    if left_box.get("class_name") == right_box.get("class_name") and bbox_iou(left_box.get("bbox_xyxy"), right_box.get("bbox_xyxy")) >= 0.5:
                        verified_classes.add(left_box.get("class_name"))
    consensus_status = "verified" if verified_classes else "fallback_used"
    for detection in selected:
        if detection.get("class_name") not in verified_classes:
            detection["review_status"] = "needs_review"
    return _result(
        selected,
        image_width=image_width,
        image_height=image_height,
        consensus_status=consensus_status,
        provider_status_redacted=[_candidate_status(candidate) for candidate in candidates],
    )


def bbox_iou(left: Any, right: Any) -> float:
    if not isinstance(left, list) or not isinstance(right, list) or len(left) != 4 or len(right) != 4:
        return 0.0
    lx1, ly1, lx2, ly2 = [float(value) for value in left]
    rx1, ry1, rx2, ry2 = [float(value) for value in right]
    ix1, iy1 = max(lx1, rx1), max(ly1, ry1)
    ix2, iy2 = min(lx2, rx2), min(ly2, ry2)
    inter = max(ix2 - ix1, 0.0) * max(iy2 - iy1, 0.0)
    left_area = max(lx2 - lx1, 0.0) * max(ly2 - ly1, 0.0)
    right_area = max(rx2 - rx1, 0.0) * max(ry2 - ry1, 0.0)
    union = left_area + right_area - inter
    return inter / union if union > 0 else 0.0


def _nms(detections: list[dict[str, Any]], iou_threshold: float = 0.55) -> list[dict[str, Any]]:
    selected: list[dict[str, Any]] = []
    ordered = sorted(detections, key=lambda item: float(item.get("confidence") or 0), reverse=True)
    for detection in ordered:
        if any(detection.get("class_name") == kept.get("class_name") and bbox_iou(detection.get("bbox_xyxy"), kept.get("bbox_xyxy")) >= iou_threshold for kept in selected):
            continue
        selected.append(dict(detection))
    return selected


def _result(
    detections: list[dict[str, Any]],
    *,
    image_width: int,
    image_height: int,
    consensus_status: str,
    provider_status_redacted: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "status": "YOLO_COMPATIBLE_DETECTION_READY" if detections else "DATA_TIDAK_CUKUP",
        "operator_detection_label": "Detection",
        "operator_output_format": "YOLO-compatible",
        "image_width": int(image_width or 0),
        "image_height": int(image_height or 0),
        "detections": detections,
        "detection_count": len(detections),
        "consensus_status": consensus_status,
        "manual_review_required": not detections or any(item.get("review_status") != "accepted" for item in detections),
        "no_fake_detection": True,
        "provider_status_redacted": provider_status_redacted,
    }


def _candidate_status(candidate: dict[str, Any]) -> dict[str, Any]:
    return {
        "role": candidate.get("role", ""),
        "status": candidate.get("status"),
        "configured": bool(candidate.get("configured")),
        "detection_count": len(candidate.get("detections", []) or []),
        "source_internal": "redacted_provider",
    }
