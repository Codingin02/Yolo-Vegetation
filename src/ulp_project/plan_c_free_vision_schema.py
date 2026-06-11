"""Normalize free vision detections into YOLO-compatible Plan C schema."""

from __future__ import annotations

import json
import re
from typing import Any

CLASS_ORDER = {
    "struktur_penyangga": 0,
    "konduktor": 1,
    "pohon_sono": 2,
}
CLASS_BY_ID = {value: key for key, value in CLASS_ORDER.items()}
CLASS_SYNONYMS = {
    "pohon_sono": {"pohon_sono", "pohon sono", "sono", "pohon", "tree", "vegetation", "angsana", "pterocarpus indicus"},
    "konduktor": {"konduktor", "conductor", "cable", "wire", "line", "power line", "kabel"},
    "struktur_penyangga": {"struktur_penyangga", "struktur penyangga", "support", "structure", "pole", "tiang", "utility pole"},
}


def empty_detection_result(
    *,
    status: str = "DATA_TIDAK_CUKUP",
    image_width: int = 0,
    image_height: int = 0,
    consensus_status: str = "disabled",
    manual_review_required: bool = True,
    provider_status_redacted: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    return {
        "status": status,
        "operator_detection_label": "Detection",
        "operator_output_format": "YOLO-compatible",
        "image_width": int(image_width or 0),
        "image_height": int(image_height or 0),
        "detections": [],
        "detection_count": 0,
        "consensus_status": consensus_status,
        "manual_review_required": manual_review_required,
        "no_fake_detection": True,
        "provider_status_redacted": provider_status_redacted or [],
        "provider_errors_redacted": [],
        "raw_response_redacted": [],
    }


def normalize_detection_payload(
    payload: Any,
    *,
    image_width: int,
    image_height: int,
    source_internal: str = "redacted_provider",
) -> dict[str, Any]:
    data = _coerce_json(payload)
    raw_detections = _extract_detection_list(data)
    detections: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    for item in raw_detections:
        normalized = normalize_detection(item, image_width=image_width, image_height=image_height, source_internal=source_internal)
        if normalized:
            detections.append(normalized)
        else:
            rejected.append({"reason": "INVALID_OR_UNSUPPORTED_DETECTION", "raw_label": _raw_label(item)})
    status = "YOLO_COMPATIBLE_DETECTION_READY" if detections else "DATA_TIDAK_CUKUP"
    return {
        "status": status,
        "operator_detection_label": "Detection",
        "operator_output_format": "YOLO-compatible",
        "image_width": int(image_width or 0),
        "image_height": int(image_height or 0),
        "detections": detections,
        "detection_count": len(detections),
        "rejected_detections_redacted": rejected,
        "consensus_status": "single_provider" if detections else "disabled",
        "manual_review_required": not detections or any(item.get("review_status") != "accepted" for item in detections),
        "no_fake_detection": True,
    }


def normalize_detection(
    item: Any,
    *,
    image_width: int,
    image_height: int,
    source_internal: str = "redacted_provider",
) -> dict[str, Any] | None:
    if not isinstance(item, dict):
        return None
    class_name = normalize_class_name(item.get("class_name") or item.get("label") or item.get("name") or item.get("class"))
    if not class_name:
        return None
    bbox = _extract_bbox(item, image_width=image_width, image_height=image_height)
    if not bbox:
        return None
    validity = validate_bbox(bbox, image_width=image_width, image_height=image_height, class_name=class_name)
    if not validity["valid"]:
        return None
    confidence = _to_float(item.get("confidence") or item.get("score") or item.get("probability"))
    confidence = max(0.0, min(confidence if confidence is not None else 0.5, 1.0))
    review_status = str(item.get("review_status") or "").strip().lower()
    if review_status not in {"accepted", "needs_review", "rejected"}:
        review_status = "needs_review" if validity.get("needs_review") or confidence < 0.55 else "accepted"
    return {
        "class_id": CLASS_ORDER[class_name],
        "class_name": class_name,
        "bbox_xyxy": [round(value, 2) for value in bbox],
        "confidence": round(confidence, 4),
        "review_status": review_status,
        "source_internal": source_internal or "redacted_provider",
        "operator_source_label": "Detection Engine",
    }


def normalize_yolo_detections(
    detections: list[dict[str, Any]],
    *,
    image_width: int,
    image_height: int,
    source_internal: str = "local_yolo",
) -> dict[str, Any]:
    normalized = [
        item
        for item in (
            normalize_detection(detection, image_width=image_width, image_height=image_height, source_internal=source_internal)
            for detection in detections or []
        )
        if item
    ]
    return {
        "status": "YOLO_COMPATIBLE_DETECTION_READY" if normalized else "DATA_TIDAK_CUKUP",
        "operator_detection_label": "Detection",
        "operator_output_format": "YOLO-compatible",
        "image_width": int(image_width or 0),
        "image_height": int(image_height or 0),
        "detections": normalized,
        "detection_count": len(normalized),
        "consensus_status": "single_provider" if normalized else "disabled",
        "manual_review_required": not normalized or any(item.get("review_status") != "accepted" for item in normalized),
        "no_fake_detection": True,
    }


def normalize_class_name(value: Any) -> str | None:
    text = re.sub(r"[_-]+", " ", str(value or "").strip().lower())
    if not text:
        return None
    for canonical, aliases in CLASS_SYNONYMS.items():
        if text in aliases:
            return canonical
    for canonical, aliases in CLASS_SYNONYMS.items():
        if any(alias in text for alias in aliases if len(alias) >= 4):
            return canonical
    return None


def validate_bbox(bbox: list[float], *, image_width: int, image_height: int, class_name: str) -> dict[str, Any]:
    if len(bbox) != 4 or image_width <= 0 or image_height <= 0:
        return {"valid": False, "reason": "BBOX_DIMENSION_INVALID"}
    x1, y1, x2, y2 = bbox
    if x2 <= x1 or y2 <= y1:
        return {"valid": False, "reason": "BBOX_ORDER_INVALID"}
    area = (x2 - x1) * (y2 - y1)
    image_area = image_width * image_height
    if area < max(9.0, image_area * 0.00005):
        return {"valid": False, "reason": "BBOX_TOO_SMALL"}
    if area > image_area * 0.95:
        if class_name == "struktur_penyangga":
            return {"valid": True, "needs_review": True, "reason": "BBOX_TOO_LARGE_REVIEW"}
        return {"valid": False, "reason": "BBOX_TOO_LARGE"}
    return {"valid": True, "needs_review": False}


def parse_json_from_text(text: str) -> Any:
    cleaned = str(text or "").strip()
    if not cleaned:
        return {}
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass
    fenced = re.search(r"```(?:json)?\s*(.*?)```", cleaned, flags=re.IGNORECASE | re.DOTALL)
    if fenced:
        try:
            return json.loads(fenced.group(1).strip())
        except json.JSONDecodeError:
            pass
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start >= 0 and end > start:
        try:
            return json.loads(cleaned[start : end + 1])
        except json.JSONDecodeError:
            return {}
    return {}


def _extract_detection_list(data: Any) -> list[Any]:
    if isinstance(data, list):
        return data
    if not isinstance(data, dict):
        return []
    for key in ["detections", "objects", "bounding_boxes", "boxes"]:
        value = data.get(key)
        if isinstance(value, list):
            return value
    return []


def _extract_bbox(item: dict[str, Any], *, image_width: int, image_height: int) -> list[float] | None:
    bbox = item.get("bbox_xyxy") or item.get("box_xyxy") or item.get("bbox") or item.get("box")
    if isinstance(bbox, dict):
        if all(key in bbox for key in ["x1", "y1", "x2", "y2"]):
            bbox = [bbox.get("x1"), bbox.get("y1"), bbox.get("x2"), bbox.get("y2")]
        elif all(key in bbox for key in ["xmin", "ymin", "xmax", "ymax"]):
            bbox = [bbox.get("xmin"), bbox.get("ymin"), bbox.get("xmax"), bbox.get("ymax")]
        elif all(key in bbox for key in ["left", "top", "right", "bottom"]):
            bbox = [bbox.get("left"), bbox.get("top"), bbox.get("right"), bbox.get("bottom")]
    if not bbox and all(key in item for key in ["x1", "y1", "x2", "y2"]):
        bbox = [item.get("x1"), item.get("y1"), item.get("x2"), item.get("y2")]
    if not bbox and all(key in item for key in ["xmin", "ymin", "xmax", "ymax"]):
        bbox = [item.get("xmin"), item.get("ymin"), item.get("xmax"), item.get("ymax")]
    if not isinstance(bbox, list) or len(bbox) != 4:
        return None
    values = [_to_float(value) for value in bbox]
    if any(value is None for value in values):
        return None
    numeric = [float(value) for value in values if value is not None]
    if max(numeric) <= 1.0:
        numeric = [numeric[0] * image_width, numeric[1] * image_height, numeric[2] * image_width, numeric[3] * image_height]
    bbox_format = item.get("bbox_format") or item.get("format") or item.get("coordinate_format")
    if isinstance(bbox_format, str):
        bbox_format = bbox_format.strip().lower()
    if bbox_format in {"xywh", "pixel_xywh"}:
        numeric = [numeric[0], numeric[1], numeric[0] + numeric[2], numeric[1] + numeric[3]]
    elif bbox_format in {"xywh_1000", "normalized_xywh_1000"}:
        numeric = [
            numeric[0] / 1000.0 * image_width,
            numeric[1] / 1000.0 * image_height,
            (numeric[0] + numeric[2]) / 1000.0 * image_width,
            (numeric[1] + numeric[3]) / 1000.0 * image_height,
        ]
    elif max(numeric) <= 1000.0 and (bbox_format in {"0_1000", "normalized_1000"} or max(numeric) > max(image_width, image_height)):
        numeric = [numeric[0] / 1000.0 * image_width, numeric[1] / 1000.0 * image_height, numeric[2] / 1000.0 * image_width, numeric[3] / 1000.0 * image_height]
    return clamp_bbox(numeric, image_width=image_width, image_height=image_height)


def clamp_bbox(bbox: list[float], *, image_width: int, image_height: int) -> list[float]:
    x1, y1, x2, y2 = bbox
    return [
        max(0.0, min(float(x1), float(image_width))),
        max(0.0, min(float(y1), float(image_height))),
        max(0.0, min(float(x2), float(image_width))),
        max(0.0, min(float(y2), float(image_height))),
    ]


def _coerce_json(payload: Any) -> Any:
    if isinstance(payload, str):
        return parse_json_from_text(payload)
    return payload


def _to_float(value: Any) -> float | None:
    if value in {None, ""}:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _raw_label(item: Any) -> str:
    if isinstance(item, dict):
        return str(item.get("class_name") or item.get("label") or item.get("name") or "")
    return ""
