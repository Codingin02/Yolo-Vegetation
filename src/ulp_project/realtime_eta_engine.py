"""Provisional ETA engine for tree-to-cable/span/trafo risk."""

from __future__ import annotations

from .clearance_policy import clearance_status
from .field_inspection_record import FieldInspectionRecord
from .growth_adjustment import choose_adjusted_growth_rate
from .realtime_estimation_result import RealtimeEstimationResult
from .risk_action_policy import classify_eta_action


def estimate_realtime_eta(record: FieldInspectionRecord) -> RealtimeEstimationResult:
    clearance = clearance_status(record.clearance_m)
    growth = choose_adjusted_growth_rate(record)
    missing: list[str] = []
    eta_days: float | None = None
    eta_months: float | None = None

    if clearance["status"] == "INSUFFICIENT_DATA":
        missing.append("clearance_m")
    if growth["adjusted_growth_rate_m_per_day"] is None:
        missing.extend(str(item) for item in growth["missing_inputs"])

    if record.clearance_m is not None and record.clearance_m <= 0:
        eta_days = 0.0
        eta_months = 0.0
    elif not missing:
        eta_days = round(record.clearance_m / float(growth["adjusted_growth_rate_m_per_day"]), 2)
        eta_months = round(eta_days / 30.4375, 2)

    action = classify_eta_action(record.clearance_m, eta_days)
    status = "OK" if eta_days is not None and record.clearance_m is not None and record.clearance_m > 0 else action["action_recommendation"]
    if missing:
        status = "INSUFFICIENT_DATA"
    if record.clearance_m is not None and record.clearance_m <= 0:
        status = "IMMEDIATE_ACTION"

    reason_parts = [str(clearance["reason"]), str(growth["reason"]), action["reason"]]
    return RealtimeEstimationResult(
        status=status,
        mode="PROVISIONAL_MANUAL_INPUT",
        eta_days=eta_days,
        eta_months=eta_months,
        risk_priority=action["risk_priority"],
        action_recommendation=action["action_recommendation"],
        adjusted_growth_rate_m_per_day=growth["adjusted_growth_rate_m_per_day"],
        environmental_data_status=growth["environmental_data_status"],
        calibration_status="MANUAL_CLEARANCE_PROVISIONAL" if record.clearance_m is not None else "CALIBRATION_NOT_READY",
        model_status="MODEL_NOT_READY",
        confidence_status=record.confidence_status or "PROVISIONAL",
        reason=" ".join(reason_parts),
        required_missing_inputs=sorted(set(missing)),
        not_accuracy_claim=True,
    )
