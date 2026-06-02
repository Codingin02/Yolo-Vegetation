"""Unified rough realtime field pipeline without touching labels or training data."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .field_inspection_record import FieldInspectionRecord
from .phase9_monitoring import append_monitoring_row, build_phase9_monitoring_row, write_phase9_risk_map
from .realtime_eta_engine import estimate_realtime_eta


def process_realtime_inspection(
    payload: dict[str, Any],
    *,
    photo_path: str = "",
    write_outputs: bool = True,
    report_output: Path | None = None,
    map_output: Path | None = None,
) -> dict[str, Any]:
    record = FieldInspectionRecord.from_payload(payload, photo_path=photo_path)
    result = estimate_realtime_eta(record)
    result_dict = result.to_dict()
    row = build_phase9_monitoring_row({**record.to_dict(), **result_dict, "job_id": payload.get("job_id", record.inspection_id)})

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
        "adjusted_growth_rate_m_per_day": result.adjusted_growth_rate_m_per_day,
        "gps": {"latitude": record.latitude, "longitude": record.longitude},
        "report_written": bool(csv_result.get("written")),
        "report_path": csv_result.get("path"),
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
