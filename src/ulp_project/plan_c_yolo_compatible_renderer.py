"""Render Plan C YOLOv8 System C annotations."""

from __future__ import annotations

from pathlib import Path
import shutil
from typing import Any

TREE_COLOR = (22, 163, 74)
CONDUCTOR_COLOR = (245, 158, 11)
STRUCTURE_COLOR = (37, 99, 235)
NON_SONO_COLOR = (132, 204, 22)
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
    zone_bands: list[dict[str, Any]] | None = None,
    final_detection_source: str = "NONE",
    zone_method: str = "heuristic_band_without_manual_clearance",
    zone_final: str = "REVIEW_REQUIRED",
) -> dict[str, Any]:
    return render_plan_c_annotated_image(
        original_path,
        annotated_path,
        final_tree_bbox=_best_tree_bbox(detections),
        detections=detections,
        risk_status=risk_status,
        prediction_window=prediction_window,
        growth_rate=(growth or {}).get("growth_rate_m_per_quarter"),
        zone_bands=zone_bands,
        zone_final=zone_final,
        zone_method=zone_method,
        manual_review_required=bool((geometry or {}).get("manual_review_required")),
        final_detection_source=final_detection_source,
        geometry=geometry or {},
        growth=growth or {},
    )


def render_plan_c_annotated_image(
    original_path: Path,
    output_path: Path,
    *,
    final_tree_bbox: list[float] | None,
    detections: list[dict[str, Any]],
    risk_status: str,
    prediction_window: str,
    growth_rate: Any,
    zone_bands: list[dict[str, Any]] | None,
    zone_final: str,
    zone_method: str,
    manual_review_required: bool,
    final_detection_source: str,
    geometry: dict[str, Any] | None = None,
    growth: dict[str, Any] | None = None,
) -> dict[str, Any]:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    geometry = geometry or {}
    growth = growth or {}
    target_detections = [
        detection
        for detection in detections
        if isinstance(detection, dict)
        and str(detection.get("class_name") or "") in {"pohon_sono", "konduktor", "struktur_penyangga", "pohon_non_sono"}
    ]
    zone_summary = _single_class_zone_summary(
        geometry,
        risk_status=risk_status,
        zone_bands=zone_bands,
        zone_method=zone_method,
        zone_final=zone_final,
    )
    try:
        from PIL import Image, ImageDraw, ImageFont

        image = Image.open(original_path).convert("RGB")
        draw = ImageDraw.Draw(image, "RGBA")
        font = ImageFont.load_default()
        zone_summary["zone_bands"] = _ensure_zone_bands(zone_bands, int(image.width), int(image.height))
        _draw_zone_bands(draw, zone_summary["zone_bands"], font)
        if target_detections:
            for detection in target_detections:
                _draw_detection(draw, detection, font, final_detection_source=final_detection_source)
        elif final_tree_bbox:
            _draw_detection(
                draw,
                {"bbox_xyxy": final_tree_bbox, "confidence": None, "class_name": "pohon_sono"},
                font,
                final_detection_source=final_detection_source,
            )
        else:
            _draw_badge(
                draw,
                image.size,
                "POHON_SONO_NOT_DETECTED - REVIEW_REQUIRED",
                font,
                fill=(*REVIEW_COLOR, 225),
                y=42,
            )
        _draw_status_card(
            draw,
            image.size,
            geometry,
            growth,
            zone_summary,
            risk_status=risk_status,
            prediction_window=prediction_window,
            growth_rate=growth_rate,
            zone_method=zone_method,
            manual_review_required=manual_review_required,
            font=font,
        )
        image.save(output_path, quality=92)
        return {
            "status": "PLAN_C_ANNOTATED_IMAGE_READY",
            "annotated_path": str(output_path),
            "detection_count": len(target_detections),
            "zone_overlay_status": "ZONE_OVERLAY_RENDERED",
            "zone_summary": zone_summary,
        }
    except Exception as exc:
        shutil.copy2(original_path, output_path)
        return {
            "status": "PLAN_C_ANNOTATED_IMAGE_FALLBACK_COPY",
            "annotated_path": str(output_path),
            "detection_count": len(target_detections),
            "zone_overlay_status": "ZONE_OVERLAY_RENDER_FALLBACK",
            "zone_summary": zone_summary,
            "error": f"{type(exc).__name__}: {exc}",
        }


def _single_class_zone_summary(
    geometry: dict[str, Any],
    *,
    risk_status: str,
    zone_bands: list[dict[str, Any]] | None,
    zone_method: str,
    zone_final: str,
) -> dict[str, Any]:
    zone_status = str(geometry.get("zone_status") or "manual_review_required")
    if risk_status in {"ZONA_TEBANG_REVIEW", "ZONA_TEBANG_MANUAL_REVIEW"}:
        zone_label = risk_status
    elif str(geometry.get("geometry_status") or "") == "INSUFFICIENT_GEOMETRY_DATA":
        zone_label = "REFERENCE_ZONE_MANUAL_REVIEW"
    else:
        zone_label = risk_status or "DATA_TIDAK_CUKUP"
    return {
        "runtime_mode": "PLAN_C_SYSTEM_C",
        "detector": "YOLOv8",
        "zone_status": zone_status,
        "zone_precision": geometry.get("zone_precision") or "manual_review",
        "zone_label": zone_label,
        "zone_method": zone_method,
        "zone_final": zone_final,
        "zone_bands": zone_bands or geometry.get("zone_bands") or [],
        "conductor_required_for_detection": False,
        "multi_class_runtime": False,
        "ground_reference_status": geometry.get("ground_reference_status") or "GROUND_REFERENCE_REQUIRES_MANUAL_REVIEW",
    }


def _draw_zone_bands(draw: Any, zone_bands: list[dict[str, Any]], font: Any) -> None:
    colors = {
        "ZONA_TEBANG": (*TEBANG_COLOR, 76),
        "ZONA_PANTAU": (*PANTAU_COLOR, 72),
        "ZONA_AMAN": (*AMAN_COLOR, 66),
    }
    label_colors = {
        "ZONA_TEBANG": (*TEBANG_COLOR, 220),
        "ZONA_PANTAU": (*PANTAU_COLOR, 220),
        "ZONA_AMAN": (*AMAN_COLOR, 220),
    }
    for band in zone_bands:
        zone = str(band.get("zone") or "")
        x1, y1, x2, y2 = [float(band.get(key) or 0) for key in ("x1", "y1", "x2", "y2")]
        draw.rectangle([x1, y1, x2, y2], fill=colors.get(zone, (*REVIEW_COLOR, 56)))
        draw.line([x1, y2, x2, y2], fill=(255, 255, 255, 130), width=1)
        label = str(band.get("label") or zone)
        draw.rectangle([x1 + 8, y1 + 8, x1 + 150, y1 + 30], fill=label_colors.get(zone, (*REVIEW_COLOR, 220)))
        draw.text((x1 + 14, y1 + 14), label, fill=(255, 255, 255, 255), font=font)


def _draw_detection(draw: Any, detection: dict[str, Any], font: Any, *, final_detection_source: str) -> None:
    bbox = detection.get("bbox_xyxy") or []
    if not isinstance(bbox, list) or len(bbox) != 4:
        return
    x1, y1, x2, y2 = [float(value) for value in bbox]
    class_name = str(detection.get("class_name") or "pohon_sono")
    color = _class_color(class_name)
    for offset in range(3):
        draw.rectangle([x1 - offset, y1 - offset, x2 + offset, y2 + offset], outline=(*color, 255))
    confidence = detection.get("confidence")
    label_conf = f"{float(confidence):.2f}" if isinstance(confidence, (int, float)) else "review"
    prefix = "AI+YOLOv8" if final_detection_source == "AI_CONSENSUS" and class_name == "pohon_sono" else "YOLOv8"
    label = f"{prefix} {class_name} {label_conf}"
    text_box = draw.textbbox((x1, y1), label, font=font)
    text_w = text_box[2] - text_box[0]
    text_h = text_box[3] - text_box[1]
    label_y = max(y1 - text_h - 8, 0)
    draw.rectangle([x1, label_y, x1 + text_w + 10, label_y + text_h + 8], fill=(*color, 230))
    draw.text((x1 + 5, label_y + 4), label, fill=(255, 255, 255, 255), font=font)


def _class_color(class_name: str) -> tuple[int, int, int]:
    if class_name == "konduktor":
        return CONDUCTOR_COLOR
    if class_name == "struktur_penyangga":
        return STRUCTURE_COLOR
    if class_name == "pohon_non_sono":
        return NON_SONO_COLOR
    return TREE_COLOR


def _draw_status_card(
    draw: Any,
    size: tuple[int, int],
    geometry: dict[str, Any],
    growth: dict[str, Any],
    zone_summary: dict[str, Any],
    *,
    risk_status: str,
    prediction_window: str,
    growth_rate: Any,
    zone_method: str,
    manual_review_required: bool,
    font: Any,
) -> None:
    width, height = size
    clearance = geometry.get("clearance_estimate_m")
    tree_height = geometry.get("tree_height_estimate_m")
    gps_distance = geometry.get("gps_distance_from_anchor_m")
    parts = [
        f"Risk: {risk_status or 'DATA_TIDAK_CUKUP'}",
        f"Window: {prediction_window or 'data tidak cukup'}",
        f"Zone: {zone_method}",
    ]
    if clearance is not None:
        parts.append(f"Clearance: {clearance} m")
    if tree_height is not None:
        parts.append(f"Tree: {tree_height} m")
    if growth_rate is not None:
        parts.append(f"Growth: {growth_rate} m/q")
    if gps_distance is not None:
        parts.append(f"GPS: {gps_distance} m")
    if manual_review_required:
        parts.append("Review manual")
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
    if risk_status in {"PANTAU", "ZONA_PANTAU", "POHON_SONO_DETECTED_REVIEW_REQUIRED"}:
        return (*PANTAU_COLOR, 218)
    if risk_status in {"AMAN", "ZONA_AMAN"}:
        return (*AMAN_COLOR, 218)
    return (*REVIEW_COLOR, 218)


def _ensure_zone_bands(zone_bands: list[dict[str, Any]] | None, width: int, height: int) -> list[dict[str, Any]]:
    if zone_bands:
        return zone_bands
    tebang_y2 = int(round(height * 0.34))
    pantau_y2 = int(round(height * 0.67))
    return [
        {"zone": "ZONA_TEBANG", "label": "ZONA TEBANG", "x1": 0, "y1": 0, "x2": width, "y2": tebang_y2},
        {"zone": "ZONA_PANTAU", "label": "ZONA PANTAU", "x1": 0, "y1": tebang_y2, "x2": width, "y2": pantau_y2},
        {"zone": "ZONA_AMAN", "label": "ZONA AMAN", "x1": 0, "y1": pantau_y2, "x2": width, "y2": height},
    ]


def _best_tree_bbox(detections: list[dict[str, Any]]) -> list[float] | None:
    candidates = []
    for item in detections:
        if not isinstance(item, dict) or str(item.get("class_name") or "") != "pohon_sono":
            continue
        bbox = item.get("bbox_xyxy")
        if not isinstance(bbox, list) or len(bbox) != 4:
            continue
        try:
            candidates.append((float(item.get("confidence") or 0.0), [float(value) for value in bbox]))
        except (TypeError, ValueError):
            continue
    if not candidates:
        return None
    candidates.sort(key=lambda item: item[0], reverse=True)
    return candidates[0][1]
