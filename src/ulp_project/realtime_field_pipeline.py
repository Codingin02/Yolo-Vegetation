"""Unified rough realtime field pipeline without touching labels or training data."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .field_inspection_record import FieldInspectionRecord
from .phase9_monitoring import append_monitoring_row, build_phase9_monitoring_row, write_phase9_risk_map
from .realtime_eta_engine import estimate_realtime_eta
from .realtime_eta_pipeline import run_realtime_eta_pipeline


def process_realtime_inspection(
    payload: dict[str, Any],
    *,
    photo_path: str = "",
    write_outputs: bool = True,
    report_output: Path | None = None,
    map_output: Path | None = None,
) -> dict[str, Any]:
    record = FieldInspectionRecord.from_payload(payload, photo_path=photo_path)
    if payload.get("selected_clearance_m") not in (None, "") or payload.get("auto_measurement_status") == "AUTO_MEASUREMENT_READY":
        eta = run_realtime_eta_pipeline(
            payload,
            species=record.species,
            point_id=record.point_id,
            latitude=record.latitude,
            longitude=record.longitude,
            environmental_overrides={
                "season": record.season,
                "rainfall_mm": record.rainfall_mm,
                "temperature_c": record.temperature_c,
                "relative_humidity_percent": record.relative_humidity_percent,
                "soil_moisture": record.soil_moisture,
                "soil_ph": record.soil_ph,
                "solar_radiation": record.solar_radiation,
                "evapotranspiration": record.evapotranspiration,
                "wind_speed": record.wind_speed,
            },
        )
        result_dict = {
            "status": "OK" if eta["eta_days"] is not None else "INSUFFICIENT_DATA",
            "mode": "AUTO_YOLO_MEASUREMENT",
            "eta_days": eta["eta_days"],
            "eta_months": eta["eta_months"],
            "risk_priority": eta["risk_priority"],
            "action_recommendation": eta["action_recommendation"],
            "adjusted_growth_rate_m_per_day": eta["adjusted_growth_rate_m_per_day"],
            "environmental_data_status": eta["environmental_features"].get("freshness_status"),
            "calibration_status": payload.get("calibration_status", "AUTO_MEASUREMENT_CALIBRATION_CONFIG"),
            "model_status": payload.get("auto_model_status") or payload.get("model_status", "MODEL_READY_UNVALIDATED_OR_MOCK"),
            "confidence_status": eta["confidence_status"],
            "reason": eta["reason"],
            "required_missing_inputs": eta["required_missing_inputs"],
            "not_accuracy_claim": True,
        }
        result_adjusted_growth = eta["adjusted_growth_rate_m_per_day"]
    else:
        result = estimate_realtime_eta(record)
        result_dict = result.to_dict()
        result_adjusted_growth = result.adjusted_growth_rate_m_per_day
    row = build_phase9_monitoring_row({**payload, **record.to_dict(), **result_dict, "job_id": payload.get("job_id", record.inspection_id)})

    csv_result = {"written": False, "path": str(report_output) if report_output else "", "status": "DRY_RUN"}
    map_result = {"written": False, "path": str(map_output) if map_output else "", "status": "DRY_RUN", "reason": "DRY_RUN"}
    if write_outputs:
        csv_result = append_monitoring_row(row, output=report_output) if report_output else append_monitoring_row(row)
        map_result = write_phase9_risk_map(row, output=map_output) if map_output else write_phase9_risk_map(row)

    return {
        **result_dict,
        "inspection_id": record.inspection_id,
        "job_id": payload.get("job_id", record.inspection_id),
        "point_id": record.point_id,
        "species": record.species,
        "asset_type": record.asset_type,
        "clearance_m": record.clearance_m,
        "growth_rate_m_per_day": record.growth_rate_m_per_day,
        "adjusted_growth_rate_m_per_day": result_adjusted_growth,
        "gps": {"latitude": record.latitude, "longitude": record.longitude},
        "report_written": bool(csv_result.get("written")),
        "report_path": csv_result.get("path"),
        "report_status": csv_result.get("status"),
        "report_operator_warning": csv_result.get("operator_warning", ""),
        "map_marker_written": bool(map_result.get("written")),
        "map_path": map_result.get("path"),
        "map_reason": map_result.get("reason") or map_result.get("status"),
        "row": row,
    }


def pipeline_status() -> dict[str, str]:
    return {
        "status": "REALTIME_FIELD_PIPELINE_READY",
        "model_status": "MODEL_NOT_READY",
        "dataset_status": "WAITING_FOR_LABELS",
        "training_status": "BLOCKED_UNTIL_LABEL_VALIDATION_AND_OPERATOR_APPROVAL",
    }
