"""Render Plan C single-class YOLOv8 pohon_sono annotations."""

from __future__ import annotations

from pathlib import Path
import shutil
from typing import Any

TREE_COLOR = (22, 163, 74)
REVIEW_COLOR = (31, 41, 55)
TEBANG_COLOR = (220, 38, 38)
PANTAU_COLOR = (202, 138, 4)
AMAN_COLOR = (22, 101, 52)


def render_yolo_compatible_annotation(
    original_path: Path,
    annotated_path: Path,
    detections: list[dict[str, Any]],
    *,
    geometry: dict[str, Any] | None = None,
    growth: dict[str, Any] | None = None,
    risk_status: str = "",
    prediction_window: str = "",
) -> dict[str, Any]:
    annotated_path.parent.mkdir(parents=True, exist_ok=True)
    geometry = geometry or {}
    growth = growth or {}
    pohon_detections = [
        detection
        for detection in detections
        if isinstance(detection, dict) and str(detection.get("class_name") or "") == "pohon_sono"
    ]
    zone_summary = _single_class_zone_summary(geometry, risk_status=risk_status)
    try:
        from PIL import Image, ImageDraw, ImageFont

        image = Image.open(original_path).convert("RGB")
        draw = ImageDraw.Draw(image, "RGBA")
        font = ImageFont.load_default()
        if pohon_detections:
            for detection in pohon_detections:
                _draw_tree_detection(draw, detection, font)
        else:
            _draw_badge(
                draw,
                image.size,
                "YOLOV8_POHON_SONO_NOT_DETECTED - manual review required",
                font,
                fill=(*REVIEW_COLOR, 225),
                y=10,
            )
        _draw_status_card(
            draw,
            image.size,
            geometry,
            growth,
            zone_summary,
            risk_status=risk_status,
            prediction_window=prediction_window,
            font=font,
        )
        image.save(annotated_path, quality=92)
        return {
            "status": "YOLOV8_SINGLE_CLASS_ANNOTATION_READY",
            "annotated_path": str(annotated_path),
            "detection_count": len(pohon_detections),
            "zone_overlay_status": "REFERENCE_ZONE_BADGE_READY",
            "zone_summary": zone_summary,
        }
    except Exception as exc:
        shutil.copy2(original_path, annotated_path)
        return {
            "status": "YOLOV8_SINGLE_CLASS_ANNOTATION_FALLBACK_COPY",
            "annotated_path": str(annotated_path),
            "detection_count": len(pohon_detections),
            "zone_overlay_status": "REFERENCE_ZONE_BADGE_FALLBACK",
            "zone_summary": zone_summary,
            "error": f"{type(exc).__name__}: {exc}",
        }


def _single_class_zone_summary(geometry: dict[str, Any], *, risk_status: str) -> dict[str, Any]:
    zone_status = str(geometry.get("zone_status") or "manual_review_required")
    if risk_status in {"ZONA_TEBANG_REVIEW", "ZONA_TEBANG_MANUAL_REVIEW"}:
        zone_label = risk_status
    elif str(geometry.get("geometry_status") or "") == "INSUFFICIENT_GEOMETRY_DATA":
        zone_label = "REFERENCE_ZONE_MANUAL_REVIEW"
    else:
        zone_label = risk_status or "DATA_TIDAK_CUKUP"
    return {
        "runtime_mode": "PLAN_C_SINGLE_CLASS_POHON_SONO",
        "detector": "YOLOv8",
        "zone_status": zone_status,
        "zone_precision": geometry.get("zone_precision") or "manual_review",
        "zone_label": zone_label,
        "conductor_required_for_detection": False,
        "multi_class_runtime": False,
        "ground_reference_status": geometry.get("ground_reference_status") or "GROUND_REFERENCE_REQUIRES_MANUAL_REVIEW",
    }


def _draw_tree_detection(draw: Any, detection: dict[str, Any], font: Any) -> None:
    bbox = detection.get("bbox_xyxy") or []
    if not isinstance(bbox, list) or len(bbox) != 4:
        return
    x1, y1, x2, y2 = [float(value) for value in bbox]
    for offset in range(3):
        draw.rectangle([x1 - offset, y1 - offset, x2 + offset, y2 + offset], outline=(*TREE_COLOR, 255))
    confidence = detection.get("confidence")
    label_conf = f"{float(confidence):.2f}" if isinstance(confidence, (int, float)) else "review"
    label = f"YOLOv8 pohon_sono {label_conf}"
    text_box = draw.textbbox((x1, y1), label, font=font)
    text_w = text_box[2] - text_box[0]
    text_h = text_box[3] - text_box[1]
    label_y = max(y1 - text_h - 8, 0)
    draw.rectangle([x1, label_y, x1 + text_w + 10, label_y + text_h + 8], fill=(*TREE_COLOR, 230))
    draw.text((x1 + 5, label_y + 4), label, fill=(255, 255, 255, 255), font=font)


def _draw_status_card(
    draw: Any,
    size: tuple[int, int],
    geometry: dict[str, Any],
    growth: dict[str, Any],
    zone_summary: dict[str, Any],
    *,
    risk_status: str,
    prediction_window: str,
    font: Any,
) -> None:
    width, height = size
    clearance = geometry.get("clearance_estimate_m")
    tree_height = geometry.get("tree_height_estimate_m")
    growth_rate = growth.get("growth_rate_m_per_quarter")
    gps_distance = geometry.get("gps_distance_from_anchor_m")
    parts = [
        f"Risk Zone: {risk_status or 'DATA_TIDAK_CUKUP'}",
        f"Prediction: {prediction_window or 'data tidak cukup'}",
        f"Review: {zone_summary.get('zone_label')}",
    ]
    if clearance is not None:
        parts.append(f"Clearance: {clearance} m")
    if tree_height is not None:
        parts.append(f"Tree: {tree_height} m")
    if growth_rate is not None:
        parts.append(f"Growth: {growth_rate} m/q")
    if gps_distance is not None:
        parts.append(f"GPS: {gps_distance} m")
    text_lines = _wrap_parts(parts, max_chars=48)
    card_w = min(width - 20, 520)
    line_h = 14
    card_h = 18 + (line_h * len(text_lines))
    x1 = 10
    y1 = max(10, height - card_h - 10)
    fill = _zone_fill(risk_status)
    draw.rectangle([x1, y1, x1 + card_w, y1 + card_h], fill=fill, outline=(255, 255, 255, 160))
    for idx, line in enumerate(text_lines):
        draw.text((x1 + 8, y1 + 8 + idx * line_h), line, fill=(255, 255, 255, 255), font=font)


def _draw_badge(
    draw: Any,
    size: tuple[int, int],
    text: str,
    font: Any,
    *,
    fill: tuple[int, int, int, int],
    y: int,
) -> None:
    width, _height = size
    text_box = draw.textbbox((0, 0), text, font=font)
    text_w = min(text_box[2] - text_box[0], max(width - 32, 0))
    text_h = text_box[3] - text_box[1]
    draw.rectangle([10, y, min(28 + text_w, width - 10), y + text_h + 16], fill=fill)
    draw.text((18, y + 8), text[:96], fill=(255, 255, 255, 255), font=font)


def _wrap_parts(parts: list[str], *, max_chars: int) -> list[str]:
    lines: list[str] = []
    current = ""
    for part in parts:
        candidate = part if not current else f"{current} | {part}"
        if len(candidate) <= max_chars:
            current = candidate
        else:
            if current:
                lines.append(current)
            current = part
    if current:
        lines.append(current)
    return lines[:5]


def _zone_fill(risk_status: str) -> tuple[int, int, int, int]:
    if risk_status in {"ZONA_TEBANG", "ZONA_TEBANG_REVIEW", "ZONA_TEBANG_MANUAL_REVIEW"}:
        return (*TEBANG_COLOR, 218)
    if risk_status in {"PANTAU", "POHON_SONO_DETECTED_REVIEW_REQUIRED"}:
        return (*PANTAU_COLOR, 218)
    if risk_status == "AMAN":
        return (*AMAN_COLOR, 218)
    return (*REVIEW_COLOR, 218)
