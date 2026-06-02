"""Action recommendation policy based on ETA and clearance."""

from __future__ import annotations


def classify_eta_action(clearance_m: float | None, eta_days: float | None) -> dict[str, str]:
    if clearance_m is not None and clearance_m <= 0:
        return {
            "risk_priority": "CRITICAL",
            "action_recommendation": "IMMEDIATE_ACTION",
            "reason": "Vegetation is at or beyond clearance boundary.",
        }
    if eta_days is None:
        return {
            "risk_priority": "INSUFFICIENT_DATA",
            "action_recommendation": "INSUFFICIENT_DATA_RECHECK",
            "reason": "ETA cannot be calculated until clearance and growth rate are provided.",
        }
    if eta_days <= 30:
        return {"risk_priority": "CRITICAL", "action_recommendation": "CRITICAL_PRUNE_REVIEW", "reason": "ETA <= 30 days."}
    if eta_days <= 90:
        return {"risk_priority": "HIGH", "action_recommendation": "HIGH_PRIORITY_REVIEW", "reason": "ETA <= 90 days."}
    if eta_days <= 180:
        return {"risk_priority": "MEDIUM", "action_recommendation": "SCHEDULED_MONITORING", "reason": "ETA <= 180 days."}
    return {"risk_priority": "LOW", "action_recommendation": "SCHEDULED_MONITORING", "reason": "ETA > 180 days."}
