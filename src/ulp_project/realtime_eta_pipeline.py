"""Realtime ETA pipeline combining measurement, environment, and growth profile."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .environmental_feature_engine import build_environmental_features
from .species_profile import get_species_profile
from .temporal_stabilizer import hysteresis_priority

_LAST_PRIORITY = "INSUFFICIENT_DATA"


@dataclass(slots=True)
class EtaPipelineResult:
    selected_clearance_m: float | None
    hazard_target: str
    adjusted_growth_rate_m_per_day: float | None
    eta_days: float | None
    eta_months: float | None
    risk_priority: str
    action_recommendation: str
    confidence_status: str
    required_missing_inputs: list[str]
    reason: str
    environmental_features: dict[str, Any]
    not_accuracy_claim: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "selected_clearance_m": self.selected_clearance_m,
            "hazard_target": self.hazard_target,
            "adjusted_growth_rate_m_per_day": self.adjusted_growth_rate_m_per_day,
            "eta_days": self.eta_days,
            "eta_months": self.eta_months,
            "risk_priority": self.risk_priority,
            "action_recommendation": self.action_recommendation,
            "confidence_status": self.confidence_status,
            "required_missing_inputs": self.required_missing_inputs,
            "reason": self.reason,
            "environmental_features": self.environmental_features,
            "not_accuracy_claim": self.not_accuracy_claim,
        }


def run_realtime_eta_pipeline(
    measurement_result: dict[str, Any],
    *,
    species: str = "pohon_sono",
    point_id: str = "",
    latitude: float | None = None,
    longitude: float | None = None,
    environmental_overrides: dict[str, Any] | None = None,
) -> dict[str, Any]:
    global _LAST_PRIORITY
    environment = build_environmental_features(point_id=point_id, latitude=latitude, longitude=longitude, overrides=environmental_overrides or {})
    features = environment["features"]
    clearance = _select_clearance(measurement_result)
    growth = adjusted_growth_from_profile(species, features)
    missing: list[str] = []
    if clearance is None:
        missing.append("selected_clearance_m")
    if growth["adjusted_growth_rate_m_per_day"] is None:
        missing.extend(growth["missing_inputs"])
    eta_days = None
    eta_months = None
    if clearance is not None and clearance <= 0:
        eta_days = 0.0
        eta_months = 0.0
        risk = "EMERGENCY"
    elif not missing and growth["adjusted_growth_rate_m_per_day"]:
        eta_days = round(float(clearance) / float(growth["adjusted_growth_rate_m_per_day"]), 2)
        eta_months = round(eta_days / 30.44, 2)
        risk = classify_eta_priority(clearance, eta_days)
    else:
        risk = "INSUFFICIENT_DATA"
    if measurement_result.get("apply_hysteresis") and risk != "INSUFFICIENT_DATA":
        risk = hysteresis_priority(_LAST_PRIORITY, risk)
        _LAST_PRIORITY = risk
    action = action_for_priority(risk)
    result = EtaPipelineResult(
        selected_clearance_m=clearance,
        hazard_target=measurement_result.get("selected_hazard_target") or "unknown",
        adjusted_growth_rate_m_per_day=growth["adjusted_growth_rate_m_per_day"],
        eta_days=eta_days,
        eta_months=eta_months,
        risk_priority=risk,
        action_recommendation=action,
        confidence_status=growth["confidence_status"],
        required_missing_inputs=sorted(set(missing)),
        reason=growth["reason"] if missing else "ETA calculated from selected clearance and adjusted growth rate. Provisional until validated.",
        environmental_features=features,
        not_accuracy_claim=True,
    )
    return result.to_dict()


def adjusted_growth_from_profile(species: str, features: dict[str, Any]) -> dict[str, Any]:
    profile = get_species_profile(species)
    base = _to_float(profile.get("base_growth_rate_m_per_day"))
    missing = []
    if base is None or base <= 0:
        return {
            "adjusted_growth_rate_m_per_day": None,
            "missing_inputs": ["base_growth_rate_m_per_day"],
            "confidence_status": "GROWTH_PROFILE_REQUIRES_FIELD_CONFIRMATION",
            "reason": "Species growth profile has no confirmed or provisional base growth rate.",
        }
    factor_keys = ["season_factor", "rainfall_factor", "soil_ph_factor", "soil_moisture_factor", "temperature_factor", "humidity_factor"]
    multiplier = 1.0
    for key in factor_keys:
        value = profile.get(key, 1.0)
        number = _to_float(value)
        if number is None:
            missing.append(key)
        else:
            multiplier *= number
    if missing:
        return {
            "adjusted_growth_rate_m_per_day": None,
            "missing_inputs": missing,
            "confidence_status": "GROWTH_PROFILE_REQUIRES_FIELD_CONFIRMATION",
            "reason": "Growth multiplier config is incomplete.",
        }
    status = profile.get("reference_status", "GROWTH_PROFILE_REQUIRES_FIELD_CONFIRMATION")
    confidence = "PROVISIONAL_OPERATOR_CONFIG" if status == "PROVISIONAL_OPERATOR_CONFIG" else profile.get("confidence_level", "LOW")
    return {
        "adjusted_growth_rate_m_per_day": round(base * multiplier, 6),
        "missing_inputs": [],
        "confidence_status": confidence,
        "reason": "Adjusted growth uses species profile factors; not an accuracy claim.",
    }


def classify_eta_priority(clearance_m: float | None, eta_days: float | None) -> str:
    if clearance_m is None or eta_days is None:
        return "INSUFFICIENT_DATA"
    if clearance_m <= 0:
        return "EMERGENCY"
    if eta_days <= 30:
        return "CRITICAL"
    if eta_days <= 90:
        return "HIGH"
    if eta_days <= 180:
        return "MEDIUM"
    return "LOW"


def action_for_priority(priority: str) -> str:
    return {
        "EMERGENCY": "EMERGENCY_CONTACT_OR_NEAR_CONTACT",
        "CRITICAL": "CRITICAL_PRUNE_REVIEW",
        "HIGH": "HIGH_PRIORITY_REVIEW",
        "MEDIUM": "SCHEDULED_MONITORING",
        "LOW": "ROUTINE_MONITORING",
        "INSUFFICIENT_DATA": "INSUFFICIENT_DATA_RECHECK",
    }.get(priority, "INSUFFICIENT_DATA_RECHECK")


def _select_clearance(measurement_result: dict[str, Any]) -> float | None:
    for key in ("stabilized_clearance_m", "selected_clearance_m", "selected_clearance_m_stable"):
        value = _to_float(measurement_result.get(key))
        if value is not None:
            return value
    return None


def _to_float(value: Any) -> float | None:
    try:
        if value in (None, ""):
            return None
        return float(value)
    except (TypeError, ValueError):
        return None
