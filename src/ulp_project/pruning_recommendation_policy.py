"""Recommendation policy from ETA and clearance zones."""

from __future__ import annotations

from typing import Any


def recommend_pruning_action(eta_expected_days: float | None, distance_zone_status: str | None = None) -> dict[str, Any]:
    if distance_zone_status in {"CONTACT_OR_OVERLAP", "UNSAFE_WITHIN_3M"}:
        return {"risk_priority": "CRITICAL", "action_recommendation": "PRIORITY_PRUNING_REVIEW"}
    if eta_expected_days is None:
        return {"risk_priority": "INSUFFICIENT_DATA", "action_recommendation": "COMPLETE_MEASUREMENT_AND_ENVIRONMENT_DATA"}
    if eta_expected_days <= 30:
        return {"risk_priority": "CRITICAL", "action_recommendation": "CRITICAL_PRUNE_REVIEW"}
    if eta_expected_days <= 90:
        return {"risk_priority": "HIGH", "action_recommendation": "HIGH_PRIORITY_REVIEW"}
    if eta_expected_days <= 180:
        return {"risk_priority": "MEDIUM", "action_recommendation": "SCHEDULED_MONITORING"}
    return {"risk_priority": "LOW", "action_recommendation": "NORMAL_MONITORING"}
