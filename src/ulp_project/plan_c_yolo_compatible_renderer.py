"""Render YOLO-compatible Plan C detections on snapshot images."""

from __future__ import annotations

from pathlib import Path
import shutil
from typing import Any

COLORS = {
    "struktur_penyangga": (37, 99, 235),
    "konduktor": (234, 179, 8),
    "pohon_sono": (22, 163, 74),
}


def render_yolo_compatible_annotation(original_path: Path, annotated_path: Path, detections: list[dict[str, Any]]) -> dict[str, Any]:
    annotated_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        from PIL import Image, ImageDraw, ImageFont

        image = Image.open(original_path).convert("RGB")
        draw = ImageDraw.Draw(image)
        font = ImageFont.load_default()
        if not detections:
            _draw_watermark(draw, image.size, "DATA_TIDAK_CUKUP", font)
        for detection in detections:
            _draw_detection(draw, detection, font)
        image.save(annotated_path, quality=92)
        return {
            "status": "YOLO_COMPATIBLE_ANNOTATION_READY",
            "annotated_path": str(annotated_path),
            "detection_count": len(detections),
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
    draw.rectangle([x1, label_y, x1 + text_w + 8, label_y + text_h + 6], fill=color)
    draw.text((x1 + 4, label_y + 3), label, fill=(0, 0, 0), font=font)


def _draw_watermark(draw: Any, size: tuple[int, int], text: str, font: Any) -> None:
    width, _height = size
    box_w = min(width - 16, 220)
    draw.rectangle([8, 8, 8 + box_w, 34], fill=(255, 255, 255), outline=(45, 45, 45))
    draw.text((14, 15), text, fill=(45, 45, 45), font=font)
