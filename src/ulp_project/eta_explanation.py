"""Explain ETA and confidence without claiming final accuracy."""

from __future__ import annotations

from typing import Any


def explain_eta(eta: dict[str, Any], context: dict[str, Any] | None = None) -> dict[str, Any]:
    context = context or {}
    confidence = "FIELD_TRIAL_READY_NOT_FINAL_ACCURACY"
    if str(context.get("calibration_status", "")).startswith("CALIBRATION_NOT"):
        confidence = "PROVISIONAL_CALIBRATION_NOT_READY"
    elif context.get("environmental_data_status") in {"ENVIRONMENT_PARTIAL", "ENVIRONMENT_NOT_READY"}:
        confidence = "PROVISIONAL_ENVIRONMENT_PARTIAL"
    return {
        "eta_status": eta.get("eta_status"),
        "confidence_status": confidence,
        "explanation": "ETA dihitung menuju ambang 3m, bukan jarak sampai kontak langsung.",
        "not_accuracy_claim": True,
    }
