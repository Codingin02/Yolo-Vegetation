"""Zone overlay calculation and drawing helpers for Plan C result images."""

from __future__ import annotations

from typing import Any

from .plan_c_geometry import DEFAULT_GEOMETRY_PARAMETERS


def build_zone_overlay_summary(
    detections: list[dict[str, Any]],
    geometry: dict[str, Any],
    *,
    image_width: int,
    image_height: int,
) -> dict[str, Any]:
    conductor = _best_detection(detections, "konduktor")
    if not conductor:
        return {
            "zone_status": "unavailable",
            "conductor_status": "tidak tervalidasi",
            "message": "DATA TIDAK CUKUP - KONDUKTOR TIDAK TERVALIDASI",
            "zones": [],
        }

    meter_per_px = geometry.get("meter_per_px")
    scale_status = str(geometry.get("scale_status") or "APPROXIMATE_VISUAL_ZONE")
    precise = scale_status in {"SCALE_FROM_STRUCTURE", "SCALE_FROM_MANUAL_INPUT"}
    if not meter_per_px:
        meter_per_px = DEFAULT_GEOMETRY_PARAMETERS["pole_height_default_m"] / max(float(image_height or 1), 1.0)
        scale_status = "APPROXIMATE_VISUAL_ZONE"
        precise = False

    x1, y1, x2, y2 = [float(value) for value in conductor.get("bbox_xyxy", [0, 0, 0, 0])]
    conductor_y = int(round((y1 + y2) / 2))
    danger_px = max(12, int(round(DEFAULT_GEOMETRY_PARAMETERS["vegetation_clearance_threshold_m"] / max(float(meter_per_px), 0.0001))))
    watch_px = max(12, int(round(3.0 / max(float(meter_per_px), 0.0001))))
    danger_end = min(int(image_height), conductor_y + danger_px)
    watch_end = min(int(image_height), danger_end + watch_px)
    zones = [
        {"name": "Zona tebang", "label": "ZONA TEBANG 0-3 m di bawah konduktor", "y1": conductor_y, "y2": danger_end, "color": "red"},
        {"name": "Zona pantau", "label": "ZONA PANTAU", "y1": danger_end, "y2": watch_end, "color": "yellow"},
        {"name": "Zona aman", "label": "ZONA AMAN", "y1": watch_end, "y2": int(image_height), "color": "green"},
    ]
    return {
        "zone_status": "precise" if precise else "approximate",
        "conductor_status": "tervalidasi",
        "scale_status": scale_status,
        "meter_per_px": round(float(meter_per_px), 6),
        "conductor_y_px": conductor_y,
        "zones": zones,
    }


def draw_zone_overlay(draw: Any, image_size: tuple[int, int], zone_summary: dict[str, Any], *, font: Any, font_small: Any) -> None:
    width, height = image_size
    if zone_summary.get("conductor_status") != "tervalidasi":
        draw.rectangle([0, 0, width, 56], fill=(0, 0, 0, 190))
        draw.text((12, 11), "DATA TIDAK CUKUP - KONDUKTOR TIDAK TERVALIDASI", fill=(255, 255, 255, 255), font=font)
        draw.text((12, 31), "ZONA BELUM PRESISI", fill=(255, 220, 130, 255), font=font_small)
        return

    colors = {
        "red": (220, 38, 38, 56),
        "yellow": (234, 179, 8, 50),
        "green": (22, 163, 74, 42),
    }
    label_colors = {
        "red": (255, 255, 255, 255),
        "yellow": (30, 30, 30, 255),
        "green": (255, 255, 255, 255),
    }
    for zone in zone_summary.get("zones", []):
        y1 = int(zone.get("y1") or 0)
        y2 = int(zone.get("y2") or 0)
        if y2 <= y1:
            continue
        color_name = str(zone.get("color") or "")
        draw.rectangle([0, y1, width, y2], fill=colors.get(color_name, (255, 255, 255, 30)))
        label = str(zone.get("label") or zone.get("name") or "")
        label_y = min(max(y1 + 8, 6), max(height - 28, 6))
        draw.rectangle([8, label_y - 4, min(width - 8, 420), label_y + 24], fill=(0, 0, 0, 130))
        draw.text((14, label_y), label, fill=label_colors.get(color_name, (255, 255, 255, 255)), font=font_small)


def _best_detection(detections: list[dict[str, Any]], class_name: str) -> dict[str, Any] | None:
    candidates = [item for item in detections if item.get("class_name") == class_name and isinstance(item.get("bbox_xyxy"), list)]
    if not candidates:
        return None
    return max(candidates, key=lambda item: float(item.get("confidence") or 0))
