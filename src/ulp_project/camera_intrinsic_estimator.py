"""Simple camera scale helper for field calibration."""

from __future__ import annotations

from typing import Any


def estimate_scale_m_per_px(known_height_m: float | None, reference_bbox_height_px: float | None) -> dict[str, Any]:
    if known_height_m is None or reference_bbox_height_px is None:
        return {"status": "CALIBRATION_NOT_READY", "estimated_m_per_px": None}
    if known_height_m <= 0 or reference_bbox_height_px <= 0:
        return {"status": "CALIBRATION_REJECTED_BAD_REFERENCE", "estimated_m_per_px": None}
    return {"status": "CALIBRATION_READY_MANUAL_REFERENCE", "estimated_m_per_px": known_height_m / reference_bbox_height_px}
