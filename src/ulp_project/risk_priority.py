"""PLN operational risk priority classification."""

from __future__ import annotations

from typing import Any

from .vegetation_eta import estimate_vegetation_eta

RECOMMENDED_ACTION = {
    "DANGER_NOW": "Pangkas/evakuasi segera",
    "CRITICAL": "Pangkas/evakuasi segera",
    "HIGH": "Jadwalkan pemangkasan prioritas",
    "MEDIUM": "Masuk rencana pemeliharaan",
    "LOW": "Aman sementara, tetap monitor",
    "INSUFFICIENT_DATA": "Lengkapi data kalibrasi/lingkungan",
}


def classify_priority_from_eta(clearance_m: float | None, eta_days: float | None) -> str:
    if clearance_m is not None and clearance_m <= 0:
        return "DANGER_NOW"
    if eta_days is None:
        return "INSUFFICIENT_DATA"
    if eta_days <= 30:
        return "CRITICAL"
    if eta_days <= 90:
        return "HIGH"
    if eta_days <= 180:
        return "MEDIUM"
    return "LOW"


def evaluate_pln_vegetation_risk(
    minimum_clearance_m: float | None,
    species_name: str,
    environment: dict[str, Any] | None = None,
    allow_provisional: bool = False,
    base_growth_rate_override: float | None = None,
) -> dict[str, Any]:
    eta = estimate_vegetation_eta(
        minimum_clearance_m,
        species_name,
        environment=environment,
        allow_provisional=allow_provisional,
        base_growth_rate_override=base_growth_rate_override,
    )
    risk = classify_priority_from_eta(minimum_clearance_m, eta["days_to_contact_p50"])
    return {
        "risk_priority": risk,
        "recommended_action": RECOMMENDED_ACTION[risk],
        "recommended_trim_deadline": "IMMEDIATE" if risk in {"DANGER_NOW", "CRITICAL"} else "SCHEDULED_REVIEW" if risk in {"HIGH", "MEDIUM"} else "ROUTINE_MONITORING" if risk == "LOW" else "DATA_REQUIRED",
        **eta,
    }
