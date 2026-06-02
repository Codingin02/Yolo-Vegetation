"""Phase 4 environmental risk skeleton without external-data claims."""

from __future__ import annotations

from typing import Any

RISK_INPUT_FIELDS = [
    "soil_ph",
    "rainfall_mm",
    "humidity_percent",
    "temperature_c",
    "season_label",
    "tree_species",
    "distance_to_conductor_m",
    "growth_stage",
    "maintenance_history",
]


def score_environmental_risk(input_dict: dict[str, Any]) -> dict[str, Any]:
    missing = [field for field in RISK_INPUT_FIELDS if input_dict.get(field) in (None, "")]
    if missing:
        return {
            "status": "DATA_NOT_READY",
            "risk_score": None,
            "risk_level": "UNKNOWN",
            "missing_inputs": missing,
            "explanation": "Environmental scoring waits for real field data and verified external sources.",
        }
    return {
        "status": "RULE_BASED_STUB",
        "risk_score": None,
        "risk_level": "PENDING_DEEP_RESEARCH",
        "missing_inputs": [],
        "explanation": "Inputs are present, but final weights require Deep Research and cited sources.",
    }
