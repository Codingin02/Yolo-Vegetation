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
    conductor = _select_conductor_reference(detections)
    conductor_y = _number(geometry.get("conductor_y") or geometry.get("conductor_y_px"))
    if conductor_y is None and conductor:
        conductor_y = _bbox_center_y(conductor.get("bbox_xyxy"))
    if not conductor or conductor_y is None:
        return {
            "zone_status": "unavailable",
            "zone_precision": "unavailable",
            "conductor_status": "tidak tervalidasi",
            "ground_reference_status": "GROUND_REFERENCE_NOT_AVAILABLE",
            "message": "DATA TIDAK CUKUP - KONDUKTOR TIDAK TERVALIDASI",
            "zones": [],
        }

    meter_per_px = _number(geometry.get("meter_per_pixel") or geometry.get("meter_per_px"))
    scale_status = str(geometry.get("scale_status") or geometry.get("meter_per_pixel_source") or "APPROXIMATE_VISUAL_ZONE")
    precise = scale_status in {"SCALE_FROM_STRUCTURE", "SCALE_FROM_MANUAL_INPUT"}
    if not meter_per_px:
        return {
            "zone_status": "approximate",
            "zone_precision": "approximate",
            "conductor_status": "tervalidasi",
            "ground_reference_status": "GROUND_REFERENCE_NOT_AVAILABLE",
            "message": "KONDUKTOR TERVERIFIKASI - SKALA BELUM TERSEDIA",
            "zones": [],
            "conductor_y": round(float(conductor_y), 2),
            "conductor_y_px": round(float(conductor_y), 2),
        }

    tree = _best_tree_reference(detections)
    ground_reference_y = _number(geometry.get("ground_reference_y"))
    ground_reference_status = str(geometry.get("ground_reference_status") or "")
    if ground_reference_y is None and tree:
        bbox = tree.get("bbox_xyxy") or []
        if isinstance(bbox, list) and len(bbox) == 4:
            ground_reference_y = _number(bbox[3])
            ground_reference_status = "VEGETATION_BASE_ESTIMATED_FROM_TREE_BBOX"
    if ground_reference_y is None:
        return {
            "zone_status": "unavailable",
            "zone_precision": "unavailable",
            "conductor_status": "tervalidasi",
            "ground_reference_status": "GROUND_REFERENCE_NOT_AVAILABLE",
            "message": "GROUND_REFERENCE_NOT_AVAILABLE - ZONA BELUM PRESISI",
            "zones": [],
            "conductor_y": round(float(conductor_y), 2),
            "conductor_y_px": round(float(conductor_y), 2),
            "meter_per_pixel": round(float(meter_per_px), 6),
            "meter_per_px": round(float(meter_per_px), 6),
        }

    zone_tebang_y1 = _number(geometry.get("zone_tebang_y1"))
    zone_tebang_y2 = _number(geometry.get("zone_tebang_y2"))
    zone_pantau_y1 = _number(geometry.get("zone_pantau_y1"))
    zone_pantau_y2 = _number(geometry.get("zone_pantau_y2"))
    zone_aman_y1 = _number(geometry.get("zone_aman_y1"))
    zone_aman_y2 = _number(geometry.get("zone_aman_y2"))

    if zone_tebang_y1 is None or zone_tebang_y2 is None:
        pixels_per_meter = 1.0 / max(float(meter_per_px), 0.0001)
        zone_tebang_y1 = float(conductor_y)
        zone_tebang_y2 = min(float(conductor_y) + (3.0 * pixels_per_meter), float(ground_reference_y))
        zone_pantau_y1 = float(conductor_y) + (3.0 * pixels_per_meter)
        zone_pantau_y2 = min(float(conductor_y) + (6.0 * pixels_per_meter), float(ground_reference_y)) if ground_reference_y > zone_pantau_y1 else None
        zone_aman_y1 = float(conductor_y) + (6.0 * pixels_per_meter) if ground_reference_y > float(conductor_y) + (6.0 * pixels_per_meter) else None
        zone_aman_y2 = float(ground_reference_y) if zone_aman_y1 is not None else None

    if not ground_reference_status:
        ground_reference_status = "VEGETATION_BASE_ESTIMATED_FROM_TREE_BBOX"
    if zone_aman_y1 is None or zone_aman_y2 is None:
        ground_reference_status = "GROUND_REFERENCE_NOT_ENOUGH_FOR_SAFE_ZONE"

    zone_status = str(geometry.get("zone_status") or ("precise" if precise else "approximate"))
    zone_precision = str(geometry.get("zone_precision") or zone_status)
    if not precise and zone_status == "precise":
        scale_status = "APPROXIMATE_VISUAL_ZONE"
        zone_status = "approximate"
        zone_precision = "approximate"

    zones = _zone_list(
        zone_tebang_y1=zone_tebang_y1,
        zone_tebang_y2=zone_tebang_y2,
        zone_pantau_y1=zone_pantau_y1,
        zone_pantau_y2=zone_pantau_y2,
        zone_aman_y1=zone_aman_y1,
        zone_aman_y2=zone_aman_y2,
        image_height=image_height,
    )
    return {
        "zone_status": zone_status,
        "zone_precision": zone_precision,
        "conductor_status": "tervalidasi",
        "scale_status": scale_status,
        "meter_per_pixel": round(float(meter_per_px), 6),
        "meter_per_px": round(float(meter_per_px), 6),
        "meter_per_pixel_source": geometry.get("meter_per_pixel_source"),
        "conductor_y": round(float(conductor_y), 2),
        "conductor_y_px": round(float(conductor_y), 2),
        "ground_reference_y": round(float(ground_reference_y), 2),
        "ground_reference_status": ground_reference_status,
        "zone_tebang_y1": zone_tebang_y1,
        "zone_tebang_y2": zone_tebang_y2,
        "zone_pantau_y1": zone_pantau_y1,
        "zone_pantau_y2": zone_pantau_y2,
        "zone_aman_y1": zone_aman_y1,
        "zone_aman_y2": zone_aman_y2,
        "zones": zones,
        "message": "ZONA BELUM PRESISI" if zone_status != "precise" else "ZONE_GEOMETRY_READY",
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

    if zone_summary.get("ground_reference_status") == "GROUND_REFERENCE_NOT_ENOUGH_FOR_SAFE_ZONE":
        draw.rectangle([8, max(6, height - 78), min(width - 8, 470), max(34, height - 50)], fill=(0, 0, 0, 145))
        draw.text((14, max(12, height - 72)), "GROUND_REFERENCE_NOT_ENOUGH_FOR_SAFE_ZONE", fill=(255, 220, 130, 255), font=font_small)


def _zone_list(
    *,
    zone_tebang_y1: float | None,
    zone_tebang_y2: float | None,
    zone_pantau_y1: float | None,
    zone_pantau_y2: float | None,
    zone_aman_y1: float | None,
    zone_aman_y2: float | None,
    image_height: int,
) -> list[dict[str, Any]]:
    candidates = [
        ("Zona tebang", "ZONA TEBANG 0-3 m di bawah konduktor", zone_tebang_y1, zone_tebang_y2, "red"),
        ("Zona pantau", "ZONA PANTAU", zone_pantau_y1, zone_pantau_y2, "yellow"),
        ("Zona aman", "ZONA AMAN", zone_aman_y1, zone_aman_y2, "green"),
    ]
    zones: list[dict[str, Any]] = []
    for name, label, y1, y2, color in candidates:
        if y1 is None or y2 is None:
            continue
        y1_clamped = max(0.0, min(float(y1), float(image_height)))
        y2_clamped = max(0.0, min(float(y2), float(image_height)))
        if y2_clamped <= y1_clamped:
            continue
        zones.append(
            {
                "name": name,
                "label": label,
                "y1": int(round(y1_clamped)),
                "y2": int(round(y2_clamped)),
                "color": color,
            }
        )
    return zones


def _best_detection(detections: list[dict[str, Any]], class_name: str) -> dict[str, Any] | None:
    candidates = [item for item in detections if item.get("class_name") == class_name and isinstance(item.get("bbox_xyxy"), list)]
    if not candidates:
        return None
    return max(candidates, key=lambda item: float(item.get("confidence") or 0))


def _select_conductor_reference(detections: list[dict[str, Any]]) -> dict[str, Any] | None:
    candidates = [item for item in detections if item.get("class_name") == "konduktor" and isinstance(item.get("bbox_xyxy"), list)]
    if not candidates:
        return None
    return max(candidates, key=lambda item: (_bbox_center_y(item.get("bbox_xyxy")), float(item.get("confidence") or 0.0)))


def _best_tree_reference(detections: list[dict[str, Any]]) -> dict[str, Any] | None:
    return _best_detection(detections, "pohon_sono") or _best_detection(detections, "pohon_non_sono")


def _bbox_center_y(box: Any) -> float | None:
    if not isinstance(box, list) or len(box) != 4:
        return None
    try:
        return (float(box[1]) + float(box[3])) / 2.0
    except (TypeError, ValueError):
        return None


def _number(value: Any) -> float | None:
    if value in {None, ""}:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
