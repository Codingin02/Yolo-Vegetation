"""Prototype 3 meter clearance policy for realtime field display.

The policy is intentionally config-driven so the 3 m threshold can be
reviewed later against PLN/ULP field rules without rewriting the runtime.
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import Any

from .paths import PROJECT_ROOT

DEFAULT_POLICY_PATH = PROJECT_ROOT / "configs" / "safety_clearance_policy.yaml"


def load_safety_clearance_policy(path: Path = DEFAULT_POLICY_PATH) -> dict[str, Any]:
    default = {
        "safe_clearance_min_m": 3.0,
        "warning_clearance_m": 4.0,
        "distance_zone_actions": {
            "CONTACT_OR_OVERLAP": "EMERGENCY_FIELD_REVIEW",
            "UNSAFE_WITHIN_3M": "PRIORITY_PRUNING_REVIEW",
            "WARNING_APPROACHING_3M": "SCHEDULED_MONITORING",
            "SAFE": "NORMAL_MONITORING",
        },
    }
    if not path.exists():
        return default
    try:
        import yaml
    except ImportError:
        return default
    loaded = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return {**default, **loaded}


def floor_display_meter(value: float | int | str | None) -> int | None:
    numeric = _to_float(value)
    if numeric is None:
        return None
    return math.floor(numeric)


def classify_distance_zone(clearance_m: float | int | str | None, policy: dict[str, Any] | None = None) -> dict[str, Any]:
    policy = policy or load_safety_clearance_policy()
    clearance = _to_float(clearance_m)
    safe_min = float(policy.get("safe_clearance_min_m", 3.0))
    warning = float(policy.get("warning_clearance_m", 4.0))
    actions = policy.get("distance_zone_actions", {})
    if clearance is None:
        zone = "INSUFFICIENT_CLEARANCE_DATA"
        action = "COMPLETE_CLEARANCE_MEASUREMENT"
    elif clearance <= 0:
        zone = "CONTACT_OR_OVERLAP"
        action = actions.get(zone, "EMERGENCY_FIELD_REVIEW")
    elif clearance <= safe_min:
        zone = "UNSAFE_WITHIN_3M"
        action = actions.get(zone, "PRIORITY_PRUNING_REVIEW")
    elif clearance < warning:
        zone = "WARNING_APPROACHING_3M"
        action = actions.get(zone, "SCHEDULED_MONITORING")
    else:
        zone = "SAFE"
        action = actions.get(zone, "NORMAL_MONITORING")
    return {
        "distance_zone_status": zone,
        "distance_zone_action": action,
        "selected_clearance_display_m": floor_display_meter(clearance),
        "safe_clearance_min_m": safe_min,
        "warning_clearance_m": warning,
        "not_legal_clearance_claim": True,
    }


def eta_status_from_days(eta_days: float | int | str | None) -> dict[str, Any]:
    eta = _to_float(eta_days)
    if eta is None:
        return {"eta_status": "INSUFFICIENT_GROWTH_OR_CLEARANCE_DATA", "risk_priority": "INSUFFICIENT_DATA"}
    if eta <= 30:
        return {"eta_status": "ETA_AVAILABLE", "risk_priority": "CRITICAL"}
    if eta <= 90:
        return {"eta_status": "ETA_AVAILABLE", "risk_priority": "HIGH"}
    if eta <= 180:
        return {"eta_status": "ETA_AVAILABLE", "risk_priority": "MEDIUM"}
    return {"eta_status": "ETA_AVAILABLE", "risk_priority": "LOW"}


def _to_float(value: Any) -> float | None:
    try:
        if value in (None, ""):
            return None
        return float(value)
    except (TypeError, ValueError):
        return None
