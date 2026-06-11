"""Render YOLO-compatible Plan C detections on snapshot images."""

from __future__ import annotations

from pathlib import Path
import shutil
from typing import Any

from .plan_c_zone_overlay import build_zone_overlay_summary, draw_zone_overlay

COLORS = {
    "struktur_penyangga": (37, 99, 235),
    "konduktor": (234, 179, 8),
    "pohon_sono": (22, 163, 74),
    "pohon_non_sono": (34, 197, 94),
}


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
    try:
        from PIL import Image, ImageDraw, ImageFont

        image = Image.open(original_path).convert("RGB")
        draw = ImageDraw.Draw(image, "RGBA")
        font = ImageFont.load_default()
        font_small = ImageFont.load_default()
        zone_summary = build_zone_overlay_summary(
            detections,
            geometry or {},
            image_width=int(image.width),
            image_height=int(image.height),
        )
        draw_zone_overlay(draw, image.size, zone_summary, font=font, font_small=font_small)
        if not detections:
            _draw_watermark(draw, image.size, "DATA_TIDAK_CUKUP", font)
        for detection in detections:
            _draw_detection(draw, detection, font)
        _draw_footer(draw, image.size, geometry or {}, growth or {}, zone_summary, risk_status=risk_status, prediction_window=prediction_window, font=font)
        image.save(annotated_path, quality=92)
        return {
            "status": "YOLO_COMPATIBLE_ANNOTATION_READY",
            "annotated_path": str(annotated_path),
            "detection_count": len(detections),
            "zone_overlay_status": "ZONE_OVERLAY_READY",
            "zone_summary": zone_summary,
        }
    except Exception as exc:
        shutil.copy2(original_path, annotated_path)
        return {
            "status": "YOLO_COMPATIBLE_ANNOTATION_FALLBACK_COPY",
            "annotated_path": str(annotated_path),
            "detection_count": len(detections),
            "error": f"{type(exc).__name__}: {exc}",
        }


def _draw_detection(draw: Any, detection: dict[str, Any], font: Any) -> None:
    class_name = str(detection.get("class_name") or "unknown")
    bbox = detection.get("bbox_xyxy") or []
    if len(bbox) != 4:
        return
    color = COLORS.get(class_name, (255, 255, 255))
    x1, y1, x2, y2 = [float(value) for value in bbox]
    width = max(2, int(max(x2 - x1, y2 - y1) / 120))
    for offset in range(width):
        draw.rectangle([x1 - offset, y1 - offset, x2 + offset, y2 + offset], outline=color)
    confidence = detection.get("confidence")
    label = f"{class_name} {float(confidence):.2f}" if isinstance(confidence, (int, float)) else class_name
    text_box = draw.textbbox((x1, y1), label, font=font)
    text_w = text_box[2] - text_box[0]
    text_h = text_box[3] - text_box[1]
    label_y = max(y1 - text_h - 6, 0)
    draw.rectangle([x1, label_y, x1 + text_w + 8, label_y + text_h + 6], fill=(*color, 220) if len(color) == 3 else color)
    draw.text((x1 + 4, label_y + 3), label, fill=(0, 0, 0), font=font)


def _draw_watermark(draw: Any, size: tuple[int, int], text: str, font: Any) -> None:
    width, _height = size
    box_w = min(width - 16, 220)
    draw.rectangle([8, 8, 8 + box_w, 34], fill=(255, 255, 255), outline=(45, 45, 45))
    draw.text((14, 15), text, fill=(45, 45, 45), font=font)


def _draw_footer(
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
    conductor_height = geometry.get("conductor_height_m")
    gps_distance = geometry.get("gps_distance_from_anchor_m")
    growth_rate = growth.get("growth_rate_m_per_quarter")
    prediction_days = growth.get("prediction_days")
    prediction_months_days = growth.get("prediction_months_days") or prediction_window
    zone_status = zone_summary.get("zone_status", "unavailable")
    parts = [
        f"Risk: {risk_status or 'DATA_TIDAK_CUKUP'}",
        f"Window: {prediction_months_days or 'data tidak cukup'}",
        f"Zone: {zone_status}",
    ]
    if clearance is not None:
        parts.append(f"Clearance: {clearance} m")
    if tree_height is not None:
        parts.append(f"Tree: {tree_height} m")
    if conductor_height is not None:
        parts.append(f"Conductor: {conductor_height} m")
    if prediction_days is not None:
        parts.append(f"Days: {prediction_days}")
    if gps_distance is not None:
        parts.append(f"GPS: {gps_distance} m")
    if growth_rate is not None:
        parts.append(f"Growth: {growth_rate} m/q")
    text = " | ".join(parts)
    draw.rectangle([0, max(0, height - 44), width, height], fill=(0, 0, 0, 190))
    draw.text((10, max(0, height - 30)), text, fill=(255, 255, 255, 255), font=font)
