"""Electrical clearance zone facade using Phase 16 3m prototype policy."""

from __future__ import annotations

from typing import Any

from .safety_clearance_policy import classify_distance_zone


def evaluate_clearance_zone(clearance_m: float | None) -> dict[str, Any]:
    result = classify_distance_zone(clearance_m)
    return {**result, "status": result["distance_zone_status"]}
