"""Normalize detection payloads into Plan C YOLO-compatible schema."""

from __future__ import annotations

import json
import re
from typing import Any

CLASS_ORDER = {
    "struktur_penyangga": 0,
    "konduktor": 1,
    "pohon_sono": 2,
    "pohon_non_sono": 3,
}
CLASS_BY_ID = {value: key for key, value in CLASS_ORDER.items()}

SONO_TERMS = {"pohon_sono", "pohon sono", "sono", "angsana", "pterocarpus indicus"}
TREE_TERMS = {"tree", "vegetation", "pohon", "tanaman", "daun", "canopy", "vegetasi"}
CONDUCTOR_TERMS = {"konduktor", "conductor", "cable", "wire", "line", "power line", "overhead line", "kabel", "jaringan listrik"}
STRUCTURE_TERMS = {"struktur_penyangga", "struktur penyangga", "support", "structure", "pole", "tiang", "utility pole", "electric pole", "crossarm", "bracket"}
NEGATIVE_TERMS = {
    "person",
    "people",
    "human",
    "face",
    "head",
    "chin",
    "hand",
    "body",
    "car",
    "motorcycle",
    "motor",
    "bicycle",
    "wall",
    "roof",
    "ceiling",
    "floor",
    "cabinet",
    "door",
    "window",
    "lamp",
    "picture frame",
    "furniture",
    "shadow",
    "sky",
    "background",
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
        "image_quality": "invalid" if not image_width or not image_height else "partial",
        "detections": [],
        "detection_count": 0,
        "negative_findings": [],
        "warnings": [],
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
    negative_findings = _extract_negative_findings(data)

    for item in raw_detections:
        normalized = normalize_detection(item, image_width=image_width, image_height=image_height, source_internal=source_internal)
        if normalized:
            detections.append(normalized)
        else:
            rejected.append({"reason": "INVALID_OR_UNSUPPORTED_DETECTION", "raw_label": _raw_label(item)})

    detections = apply_detection_nms(detections)
    status = "YOLO_COMPATIBLE_DETECTION_READY" if detections else "DATA_TIDAK_CUKUP"
    return {
        "status": status,
        "operator_detection_label": "Detection",
        "operator_output_format": "YOLO-compatible",
        "image_width": int(image_width or 0),
        "image_height": int(image_height or 0),
        "image_quality": _image_quality(data),
        "detections": detections,
        "detection_count": len(detections),
        "negative_findings": negative_findings,
        "warnings": _warnings(data),
        "rejected_detections_redacted": rejected,
        "consensus_status": "single_provider" if detections else "disabled",
        "manual_review_required": not detections or any(item.get("review_status") != "ACCEPT" for item in detections),
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
    label = item.get("class_name") or item.get("label") or item.get("name") or item.get("class") or item.get("operator_label")
    class_name = normalize_class_name(label)
    if not class_name:
        return None
    reason = str(item.get("reason") or item.get("description") or "").strip()
    if reason_has_strong_negative(reason, class_name=class_name):
        return None
    bbox = extract_bbox_xyxy(item, image_width=image_width, image_height=image_height)
    if not bbox:
        return None
    validity = validate_bbox(bbox, image_width=image_width, image_height=image_height, class_name=class_name)
    if not validity["valid"]:
        return None
    confidence = _to_float(item.get("confidence") if item.get("confidence") is not None else item.get("score") or item.get("probability"))
    confidence = max(0.0, min(confidence if confidence is not None else 0.5, 1.0))
    review_status = normalize_review_status(item.get("review_status"), confidence=confidence, needs_review=bool(validity.get("needs_review")))
    species_guess = item.get("species_guess")
    if class_name == "pohon_sono":
        species_guess = species_guess or "pohon_sono"
        is_target_species = True
    elif class_name == "pohon_non_sono":
        species_guess = species_guess or "unknown_tree"
        is_target_species = False
        if review_status == "ACCEPT":
            review_status = "REVIEW"
    else:
        is_target_species = None
    return {
        "class_id": CLASS_ORDER[class_name],
        "class_name": class_name,
        "bbox_format": "xyxy",
        "bbox_xyxy": [round(value, 2) for value in bbox],
        "confidence": round(confidence, 4),
        "source_internal": source_internal or "redacted_provider",
        "operator_source_label": "Detection Engine",
        "operator_label": class_name,
        "species_guess": species_guess,
        "is_target_species": is_target_species,
        "review_status": review_status,
        "reason": reason[:180] if reason else "target object candidate",
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
    normalized = apply_detection_nms(normalized)
    return {
        "status": "YOLO_COMPATIBLE_DETECTION_READY" if normalized else "DATA_TIDAK_CUKUP",
        "operator_detection_label": "Detection",
        "operator_output_format": "YOLO-compatible",
        "image_width": int(image_width or 0),
        "image_height": int(image_height or 0),
        "detections": normalized,
        "detection_count": len(normalized),
        "negative_findings": [],
        "warnings": [],
        "consensus_status": "single_provider" if normalized else "disabled",
        "manual_review_required": not normalized or any(item.get("review_status") != "ACCEPT" for item in normalized),
        "no_fake_detection": True,
    }


def normalize_class_name(value: Any) -> str | None:
    text = _clean_label(value)
    if not text:
        return None
    if _contains_any(text, NEGATIVE_TERMS):
        return None
    if text in SONO_TERMS or any(term in text for term in SONO_TERMS if len(term) >= 4):
        return "pohon_sono"
    if text in CONDUCTOR_TERMS or any(term in text for term in CONDUCTOR_TERMS if len(term) >= 4):
        return "konduktor"
    if text in STRUCTURE_TERMS or any(term in text for term in STRUCTURE_TERMS if len(term) >= 4):
        return "struktur_penyangga"
    if text in TREE_TERMS or any(term in text for term in TREE_TERMS if len(term) >= 4):
        return "pohon_non_sono"
    return None


def extract_bbox_xyxy(item: dict[str, Any], *, image_width: int, image_height: int) -> list[float] | None:
    if "box_2d" in item:
        box = item.get("box_2d")
        if isinstance(box, (list, tuple)) and len(box) == 4:
            values = [_to_float(value) for value in box]
            if all(value is not None for value in values):
                ymin, xmin, ymax, xmax = [float(value) for value in values if value is not None]
                return clamp_bbox(
                    [xmin / 1000.0 * image_width, ymin / 1000.0 * image_height, xmax / 1000.0 * image_width, ymax / 1000.0 * image_height],
                    image_width=image_width,
                    image_height=image_height,
                )

    bbox = item.get("bbox_xyxy") or item.get("box_xyxy") or item.get("bbox") or item.get("box") or item.get("xyxy")
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
    if not isinstance(bbox, (list, tuple)) or len(bbox) != 4:
        return None
    values = [_to_float(value) for value in bbox]
    if any(value is None for value in values):
        return None
    numeric = [float(value) for value in values if value is not None]
    bbox_format = str(item.get("bbox_format") or item.get("format") or item.get("coordinate_format") or "").strip().lower()
    if max(numeric) <= 1.0:
        numeric = [numeric[0] * image_width, numeric[1] * image_height, numeric[2] * image_width, numeric[3] * image_height]
    elif bbox_format in {"xywh", "pixel_xywh"}:
        numeric = [numeric[0], numeric[1], numeric[0] + numeric[2], numeric[1] + numeric[3]]
    elif bbox_format in {"xywh_1000", "normalized_xywh_1000"}:
        numeric = [
            numeric[0] / 1000.0 * image_width,
            numeric[1] / 1000.0 * image_height,
            (numeric[0] + numeric[2]) / 1000.0 * image_width,
            (numeric[1] + numeric[3]) / 1000.0 * image_height,
        ]
    elif bbox_format in {"0_1000", "normalized_1000", "box_2d_1000"} or max(numeric) > max(image_width, image_height):
        numeric = [numeric[0] / 1000.0 * image_width, numeric[1] / 1000.0 * image_height, numeric[2] / 1000.0 * image_width, numeric[3] / 1000.0 * image_height]
    return clamp_bbox(numeric, image_width=image_width, image_height=image_height)


def validate_bbox(bbox: list[float], *, image_width: int, image_height: int, class_name: str) -> dict[str, Any]:
    if len(bbox) != 4 or image_width <= 0 or image_height <= 0:
        return {"valid": False, "reason": "BBOX_DIMENSION_INVALID"}
    x1, y1, x2, y2 = bbox
    if x2 <= x1 or y2 <= y1:
        return {"valid": False, "reason": "BBOX_ORDER_INVALID"}
    area = (x2 - x1) * (y2 - y1)
    image_area = image_width * image_height
    if area < max(24.0, image_area * 0.00008):
        return {"valid": False, "reason": "BBOX_TOO_SMALL"}
    if area > image_area * 0.95:
        if class_name == "struktur_penyangga":
            return {"valid": True, "needs_review": True, "reason": "BBOX_TOO_LARGE_REVIEW"}
        return {"valid": False, "reason": "BBOX_TOO_LARGE"}
    return {"valid": True, "needs_review": False}


def normalize_review_status(value: Any, *, confidence: float, needs_review: bool = False) -> str:
    text = str(value or "").strip().lower()
    if text in {"accept", "accepted", "ok", "valid"}:
        return "REVIEW" if needs_review else "ACCEPT"
    if text in {"reject", "rejected", "invalid"}:
        return "REJECT"
    if needs_review or confidence < 0.65:
        return "REVIEW"
    return "ACCEPT"


def apply_detection_nms(detections: list[dict[str, Any]], *, iou_threshold: float = 0.55) -> list[dict[str, Any]]:
    kept: list[dict[str, Any]] = []
    for detection in sorted(detections, key=lambda item: float(item.get("confidence") or 0), reverse=True):
        if detection.get("review_status") == "REJECT":
            continue
        if any(detection.get("class_name") == item.get("class_name") and bbox_iou(detection.get("bbox_xyxy"), item.get("bbox_xyxy")) >= iou_threshold for item in kept):
            continue
        kept.append(dict(detection))
    return kept


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


def reason_has_strong_negative(reason: str, *, class_name: str) -> bool:
    text = _clean_label(reason)
    if not text:
        return False
    if not _contains_any(text, NEGATIVE_TERMS):
        return False
    positive = {
        "konduktor": CONDUCTOR_TERMS,
        "struktur_penyangga": STRUCTURE_TERMS,
        "pohon_sono": SONO_TERMS,
        "pohon_non_sono": TREE_TERMS,
    }.get(class_name, set())
    return not _contains_any(text, positive)


def parse_json_from_text(text: str) -> Any:
    cleaned = str(text or "").strip()
    if not cleaned:
        return {}
    cleaned = re.sub(r"^```(?:json)?", "", cleaned, flags=re.IGNORECASE).strip()
    cleaned = re.sub(r"```$", "", cleaned).strip()
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


def clamp_bbox(bbox: list[float], *, image_width: int, image_height: int) -> list[float]:
    x1, y1, x2, y2 = bbox
    return [
        max(0.0, min(float(x1), float(image_width))),
        max(0.0, min(float(y1), float(image_height))),
        max(0.0, min(float(x2), float(image_width))),
        max(0.0, min(float(y2), float(image_height))),
    ]


def _extract_detection_list(data: Any) -> list[Any]:
    if isinstance(data, list):
        return data
    if not isinstance(data, dict):
        return []
    found: list[Any] = []
    for key in ["detections", "objects", "bounding_boxes", "boxes", "results"]:
        value = data.get(key)
        if isinstance(value, list):
            found.extend(value)
    return found


def _extract_negative_findings(data: Any) -> list[dict[str, Any]]:
    if not isinstance(data, dict):
        return []
    value = data.get("negative_findings") or data.get("rejected_objects") or []
    if not isinstance(value, list):
        return []
    items = []
    for item in value:
        if isinstance(item, dict):
            items.append(
                {
                    "object": str(item.get("object") or item.get("label") or item.get("name") or "other")[:80],
                    "action": str(item.get("action") or "ignored")[:40],
                    "reason": str(item.get("reason") or "not a target object")[:160],
                }
            )
    return items[:40]


def _image_quality(data: Any) -> str:
    text = str(data.get("image_quality") if isinstance(data, dict) else "").strip().lower()
    return text if text in {"clear", "blurry", "dark", "partial", "invalid"} else "partial"


def _warnings(data: Any) -> list[str]:
    if not isinstance(data, dict):
        return []
    value = data.get("warnings") or []
    if not isinstance(value, list):
        return []
    return [str(item)[:180] for item in value[:20]]


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


def _clean_label(value: Any) -> str:
    return re.sub(r"[_-]+", " ", str(value or "").strip().lower())


def _contains_any(text: str, needles: set[str]) -> bool:
    return any(needle in text for needle in needles if needle)
