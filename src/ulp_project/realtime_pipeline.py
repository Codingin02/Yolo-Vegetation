"""Phase 8 laptop processing pipeline for field capture jobs."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .job_queue import RUNTIME_ROOT, create_job, write_job_result
from .latency_report import build_latency_report
from .risk_priority import evaluate_pln_vegetation_risk
from .risk_map_exporter import export_risk_map
from .spreadsheet_report_writer import build_phase8_report_row, write_phase8_report


def run_realtime_field_pipeline(
    metadata: dict[str, Any],
    runtime_root: Path = RUNTIME_ROOT,
    mode: str = "dry-run",
    allow_provisional: bool = False,
) -> dict[str, Any]:
    job = create_job(metadata, runtime_root)
    minimum_clearance = _to_float(metadata.get("minimum_clearance_m"))
    growth_override = _to_float(metadata.get("base_growth_rate_m_per_day"))
    environment = {
        "season_label": metadata.get("season_label"),
        "rainfall_30d_mm": metadata.get("rainfall_30d_mm"),
        "soil_ph": metadata.get("soil_ph"),
        "soil_moisture_proxy": metadata.get("soil_moisture_proxy"),
    }
    risk = evaluate_pln_vegetation_risk(
        minimum_clearance,
        str(metadata.get("species") or "pohon_sono"),
        environment=environment,
        allow_provisional=allow_provisional,
        base_growth_rate_override=growth_override,
    )
    row = build_phase8_report_row(
        {
            **metadata,
            "minimum_clearance_m": minimum_clearance or "",
            "risk_priority": risk["risk_priority"],
            "recommended_action": risk["recommended_action"],
            "recommended_trim_deadline": risk["recommended_trim_deadline"],
            "days_to_contact_p50": risk["days_to_contact_p50"] or "",
            "months_to_contact_p50": risk["months_to_contact_p50"] or "",
            "growth_rate_base_m_per_day": risk.get("growth_rate_base_m_per_day", ""),
            "growth_rate_adjusted_m_per_day": risk.get("growth_rate_adjusted_m_per_day", ""),
            "model_status": "MODEL_NOT_READY",
            "calibration_status": "CALIBRATION_NOT_READY" if minimum_clearance is None else "CALIBRATION_PARTIAL",
            "environmental_data_status": "ENVIRONMENTAL_DATA_PARTIAL" if allow_provisional else "ENVIRONMENTAL_DATA_NOT_READY",
        }
    )
    report = write_phase8_report([row], mode="dry-run" if mode == "dry-run" else "write")
    risk_map = export_risk_map([row], mode="dry-run" if mode == "dry-run" else "write")
    latency = build_latency_report(upload_latency_ms=0, queue_latency_ms=0, inference_latency_ms=None, report_write_latency_ms=0)
    result = {
        "status": "REALTIME_PIPELINE_DRY_RUN_READY" if mode == "dry-run" else "REALTIME_PIPELINE_WRITTEN",
        "job_id": job["job_id"],
        "model_status": "MODEL_NOT_READY",
        "risk": risk,
        "spreadsheet": report,
        "map": risk_map,
        "latency": latency,
        "not_accuracy_claim": True,
    }
    if mode != "dry-run":
        write_job_result(str(job["job_id"]), result, runtime_root)
    return result


def _to_float(value: Any) -> float | None:
    try:
        if value in (None, ""):
            return None
        return float(value)
    except (TypeError, ValueError):
        return None
