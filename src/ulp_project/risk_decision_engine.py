"""Operational risk decision engine for cable/span/trafo clearance."""

from __future__ import annotations

from typing import Any

from .time_to_contact import estimate_time_to_contact
from .vegetation_clearance import classify_operational_risk

ACTION_BY_STATUS = {
    "KRITIS_SEGERA": "Pangkas/evakuasi segera",
    "PRIORITAS_TINGGI": "Jadwalkan pemangkasan prioritas",
    "JADWALKAN_PEMANGKASAN": "Masuk rencana pemeliharaan",
    "PERLU_MONITORING": "Pantau ulang berkala",
    "AMAN_MONITOR": "Aman sementara, tetap monitor",
    "NEEDS_CALIBRATION_OR_ENVIRONMENTAL_DATA": "Lengkapi data kalibrasi/lingkungan",
}

PRIORITY_BY_STATUS = {
    "KRITIS_SEGERA": 1,
    "PRIORITAS_TINGGI": 2,
    "JADWALKAN_PEMANGKASAN": 3,
    "PERLU_MONITORING": 4,
    "AMAN_MONITOR": 5,
    "NEEDS_CALIBRATION_OR_ENVIRONMENTAL_DATA": 99,
}


def build_risk_decision(clearance_m: float | None, growth_inputs: dict[str, Any], nearest_asset_type: str | None = None) -> dict[str, Any]:
    risk_status = classify_operational_risk(clearance_m)
    eta = estimate_time_to_contact(clearance_m, growth_inputs)
    if eta["status"] == "NEEDS_CALIBRATION_OR_ENVIRONMENTAL_DATA":
        risk_status = "NEEDS_CALIBRATION_OR_ENVIRONMENTAL_DATA"
    return {
        "status": eta["status"],
        "risk_status": risk_status,
        "nearest_electrical_asset": nearest_asset_type or "unknown",
        "eta_days": eta["eta_days"],
        "eta_months": eta["eta_months"],
        "eta_days_min": eta["eta_days_min"],
        "eta_days_mid": eta["eta_days_mid"],
        "eta_days_max": eta["eta_days_max"],
        "eta_months_mid": round(eta["eta_days_mid"] / 30.44, 2) if eta["eta_days_mid"] is not None else None,
        "confidence_level": eta["confidence_level"],
        "data_quality_flags": eta["data_quality_flags"],
        "recommended_action": ACTION_BY_STATUS[risk_status],
        "priority_rank": PRIORITY_BY_STATUS[risk_status],
        "not_accuracy_claim": True,
    }
