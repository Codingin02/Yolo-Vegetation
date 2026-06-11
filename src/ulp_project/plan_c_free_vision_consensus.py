"""Consensus and de-duplication for Plan C YOLO-compatible detections."""

from __future__ import annotations

from typing import Any

from .plan_c_free_vision_schema import apply_detection_nms, bbox_iou, empty_detection_result


def build_detection_consensus(candidates: list[dict[str, Any]], *, image_width: int, image_height: int) -> dict[str, Any]:
    valid_candidates = [candidate for candidate in candidates if candidate.get("detections")]
    provider_status = [_candidate_status(candidate) for candidate in candidates]
    if not valid_candidates:
        return empty_detection_result(
            status="DATA_TIDAK_CUKUP",
            image_width=image_width,
            image_height=image_height,
            consensus_status="disabled",
            provider_status_redacted=provider_status,
        )

    selected = apply_detection_nms([dict(detection) for candidate in valid_candidates for detection in candidate.get("detections", [])])
    verified = _verified_classes(valid_candidates)
    if len(valid_candidates) == 1:
        consensus_status = "single_provider"
    elif verified:
        consensus_status = "verified"
    else:
        consensus_status = "fallback_used"

    for detection in selected:
        class_name = detection.get("class_name")
        if class_name in verified:
            detection["review_status"] = "ACCEPT"
        elif len(valid_candidates) == 1:
            detection["review_status"] = "REVIEW"
        else:
            detection["review_status"] = "REVIEW"

    return _result(
        selected,
        image_width=image_width,
        image_height=image_height,
        consensus_status=consensus_status,
        provider_status_redacted=provider_status,
    )


def _verified_classes(valid_candidates: list[dict[str, Any]]) -> set[str]:
    verified_classes: set[str] = set()
    for left_index, left in enumerate(valid_candidates):
        for right in valid_candidates[left_index + 1 :]:
            for left_box in left.get("detections", []):
                for right_box in right.get("detections", []):
                    if left_box.get("class_name") == right_box.get("class_name") and bbox_iou(left_box.get("bbox_xyxy"), right_box.get("bbox_xyxy")) >= 0.45:
                        verified_classes.add(str(left_box.get("class_name")))
    return verified_classes


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
        "image_quality": "partial",
        "detections": detections,
        "detection_count": len(detections),
        "negative_findings": [],
        "warnings": [],
        "consensus_status": consensus_status,
        "manual_review_required": not detections or any(item.get("review_status") != "ACCEPT" for item in detections),
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
