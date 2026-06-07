"""Candidate geometry from visual reference scaling.

This module is intentionally conservative. It can produce a candidate
clearance only when tree, pole, and conductor boxes are available; otherwise it
returns a blocked status and never invents pole/conductor geometry.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .paths import PROJECT_ROOT

CONFIG_PATH = PROJECT_ROOT / "configs" / "ulp_geometry_reference.yaml"

DEFAULT_CONFIG = {
    "reference_policy": "CONFIGURABLE_FIELD_REFERENCE_NOT_FINAL",
    "voltage_level": "20kV",
    "pole_height_candidates_m": [9, 11, 12, 13],
    "default_reference_pole_height_m": 12.0,
    "default_reference_status": "NEEDS_PLN_CONFIRMATION",
    "clearance_threshold_m": 3.0,
    "measurement_mode": "MONOCULAR_REFERENCE_SCALING_CANDIDATE",
}


def load_geometry_reference_config(path: Path | None = None) -> dict[str, Any]:
    target = path or CONFIG_PATH
    config = dict(DEFAULT_CONFIG)
    if not target.exists():
        return {**config, "config_status": "GEOMETRY_REFERENCE_DEFAULT_CONFIG_USED"}
    for raw_line in target.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or ":" not in line:
            continue
        key, value = line.split(":", 1)
        key = key.strip()
        value = value.strip()
        if key in {"default_reference_pole_height_m", "clearance_threshold_m"}:
            try:
                config[key] = float(value)
            except ValueError:
                config[key] = DEFAULT_CONFIG[key]
        elif key not in {"notes", "pole_height_candidates_m"}:
            config[key] = value
    return {**config, "config_status": "GEOMETRY_REFERENCE_CONFIG_READY", "config_path": str(target)}


def compute_reference_geometry(
    detections: dict[str, Any] | list[dict[str, Any]],
    *,
    frame_width: int | float | None = None,
    frame_height: int | float | None = None,
    reference_pole_height_m: float | None = None,
    config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    cfg = config or load_geometry_reference_config()
    boxes = _extract_boxes(detections)
    tree = boxes.get("pohon_sono")
    pole = boxes.get("struktur_penyangga")
    conductor = boxes.get("konduktor")
    missing = []
    if not tree:
        missing.append("GEOMETRY_BLOCKED_NO_TREE")
    if not pole:
        missing.append("GEOMETRY_BLOCKED_NO_POLE")
    if not conductor:
        missing.append("GEOMETRY_BLOCKED_NO_CONDUCTOR")
    if missing:
        return {
            "geometry_status": "GEOMETRY_BLOCKED_NO_POLE_CONDUCTOR" if tree and {"GEOMETRY_BLOCKED_NO_POLE", "GEOMETRY_BLOCKED_NO_CONDUCTOR"}.issubset(set(missing)) else missing[0],
            "reason_codes": missing + ["NO_FAKE_CLEARANCE", "GPS_NOT_USED_FOR_PIXEL_SCALING"],
            "estimated_tree_height_m": None,
            "estimated_conductor_height_m": None,
            "estimated_clearance_m": None,
            "confidence": "LOW",
            "measurement_mode": cfg.get("measurement_mode", "MONOCULAR_REFERENCE_SCALING_CANDIDATE"),
            "reference_status": cfg.get("default_reference_status", "NEEDS_PLN_CONFIRMATION"),
            "no_fake_clearance": True,
        }
    pole_height_px = _height_px(pole)
    if pole_height_px <= 0:
        return {
            "geometry_status": "GEOMETRY_BLOCKED_NO_VALID_POLE_BOX",
            "reason_codes": ["GEOMETRY_BLOCKED_NO_VALID_POLE_BOX", "NO_FAKE_CLEARANCE"],
            "estimated_clearance_m": None,
            "no_fake_clearance": True,
        }
    pole_height_m = float(reference_pole_height_m or cfg.get("default_reference_pole_height_m") or 12.0)
    pixel_per_meter = pole_height_px / pole_height_m
    tree_height_m = _height_px(tree) / pixel_per_meter
    conductor_height_m = max(0.0, (_bottom_y(pole) - _center_y(conductor)) / pixel_per_meter)
    clearance_m = conductor_height_m - tree_height_m
    return {
        "geometry_status": "GEOMETRY_READY_CANDIDATE",
        "pixel_per_meter_candidate": round(pixel_per_meter, 6),
        "estimated_tree_height_m": round(tree_height_m, 3),
        "estimated_conductor_height_m": round(conductor_height_m, 3),
        "estimated_clearance_m": round(clearance_m, 3),
        "confidence": "LOW",
        "measurement_mode": cfg.get("measurement_mode", "MONOCULAR_REFERENCE_SCALING_CANDIDATE"),
        "reference_pole_height_m": pole_height_m,
        "reference_status": cfg.get("default_reference_status", "NEEDS_PLN_CONFIRMATION"),
        "frame_width": frame_width,
        "frame_height": frame_height,
        "reason_codes": [
            "GEOMETRY_CANDIDATE_NOT_FINAL",
            "NEEDS_PLN_CONFIRMATION",
            "CALIBRATION_NOT_FINAL",
            "GPS_NOT_USED_FOR_PIXEL_SCALING",
        ],
        "no_fake_clearance": True,
    }


def _extract_boxes(detections: dict[str, Any] | list[dict[str, Any]]) -> dict[str, dict[str, float]]:
    items: list[dict[str, Any]]
    if isinstance(detections, dict):
        items = list(detections.get("detections") or [])
    else:
        items = list(detections or [])
    boxes: dict[str, dict[str, float]] = {}
    for item in items:
        name = str(item.get("class_name") or item.get("label") or "").strip()
        bbox = _normalize_box(item.get("bbox_xyxy") or item.get("bbox") or item.get("box"))
        if name and bbox:
            boxes[name] = bbox
    return boxes


def _normalize_box(box: Any) -> dict[str, float]:
    if isinstance(box, dict):
        if {"x1", "y1", "x2", "y2"}.issubset(box):
            return {key: float(box[key]) for key in ["x1", "y1", "x2", "y2"]}
        if {"x", "y", "width", "height"}.issubset(box):
            x = float(box["x"])
            y = float(box["y"])
            return {"x1": x, "y1": y, "x2": x + float(box["width"]), "y2": y + float(box["height"])}
    if isinstance(box, (list, tuple)) and len(box) >= 4:
        return {"x1": float(box[0]), "y1": float(box[1]), "x2": float(box[2]), "y2": float(box[3])}
    return {}


def _height_px(box: dict[str, float]) -> float:
    return max(0.0, float(box.get("y2", 0.0)) - float(box.get("y1", 0.0)))


def _center_y(box: dict[str, float]) -> float:
    return (float(box.get("y1", 0.0)) + float(box.get("y2", 0.0))) / 2.0


def _bottom_y(box: dict[str, float]) -> float:
    return max(float(box.get("y1", 0.0)), float(box.get("y2", 0.0)))
