"""Browser-based HP field capture helpers.

HP is only an input client. The laptop Flask server remains the processing
center and writes runtime files only under ignored data/runtime.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .job_queue import RUNTIME_ROOT, load_job, load_job_result, write_job_result
from .mobile_upload import accept_mobile_upload
from .phase9_eta_demo import calculate_manual_eta, parse_float
from .phase9_monitoring import append_monitoring_row, build_phase9_monitoring_row, write_phase9_risk_map


def accept_field_capture_upload(
    form: dict[str, Any],
    image_file: Any | None = None,
    video_file: Any | None = None,
    runtime_root: Path = RUNTIME_ROOT,
) -> dict[str, Any]:
    result = accept_mobile_upload(form, image_file=image_file, video_file=video_file, runtime_root=runtime_root)
    eta = calculate_manual_eta(form.get("clearance_m"), form.get("growth_rate_m_per_day"))
    job_id = str(result.get("job_id", ""))
    image_path = result.get("saved_files", {}).get("image_path", "") if isinstance(result.get("saved_files"), dict) else ""
    latitude = form.get("latitude") or form.get("lat")
    longitude = form.get("longitude") or form.get("lon")
    row = build_phase9_monitoring_row(
        {
            "job_id": job_id,
            "point_id": form.get("point_id", ""),
            "species": form.get("species") or form.get("manual_object_type") or "pohon_sono",
            "asset_type": form.get("asset_type", "span"),
            "latitude": latitude,
            "longitude": longitude,
            "tree_height_m": form.get("tree_height_m", ""),
            "cable_or_span_height_m": form.get("cable_or_span_height_m", ""),
            "clearance_m": eta.get("clearance_m") if eta.get("clearance_m") is not None else form.get("clearance_m", ""),
            "growth_rate_m_per_day": eta.get("growth_rate_m_per_day") if eta.get("growth_rate_m_per_day") is not None else form.get("growth_rate_m_per_day", ""),
            "eta_days": eta["eta_days"] if eta["eta_days"] is not None else "",
            "eta_months": eta["eta_months"] if eta["eta_months"] is not None else "",
            "risk_priority": eta["risk_priority"],
            "status": eta["status"],
            "mode": eta["mode"],
            "reason": eta["reason"],
            "image_path": image_path,
            "operator_notes": form.get("notes") or form.get("operator_note") or "",
        }
    )
    csv_result = append_monitoring_row(row)
    map_result = write_phase9_risk_map(row)
    response = {
        "status": eta["status"],
        "mode": eta["mode"],
        "job_id": job_id,
        "point_id": row["point_id"],
        "species": row["species"],
        "asset_type": row["asset_type"],
        "eta_days": eta["eta_days"],
        "eta_months": eta["eta_months"],
        "risk_priority": eta["risk_priority"],
        "reason": eta["reason"],
        "latency_ms": result.get("latency_ms", 0),
        "gps": {"latitude": parse_float(latitude), "longitude": parse_float(longitude)},
        "report_written": bool(csv_result.get("written")),
        "report_path": csv_result.get("path"),
        "map_marker_written": bool(map_result.get("written")),
        "map_path": map_result.get("path"),
        "map_reason": map_result.get("reason"),
        "clearance_m": eta.get("clearance_m"),
        "growth_rate_m_per_day": eta.get("growth_rate_m_per_day"),
        "model_status": "MODEL_NOT_READY",
        "calibration_status": "MANUAL_CLEARANCE_PROVISIONAL" if eta.get("clearance_m") is not None else "CALIBRATION_NOT_READY",
        "environment_source_status": "ENVIRONMENT_NOT_REQUIRED_FOR_MANUAL_DEMO",
        "not_accuracy_claim": True,
    }
    write_job_result(job_id, response, runtime_root)
    return {
        **response,
        "capture_architecture": "field_input_browser",
        "hp_role": "input_client_only",
        "processing_center": "laptop_flask_server",
        "monitoring_primary": "csv_google_sheets_and_map",
    }


def load_field_capture_job(job_id: str, runtime_root: Path = RUNTIME_ROOT) -> dict[str, object]:
    return load_job(job_id, runtime_root)


def load_field_capture_result(job_id: str, runtime_root: Path = RUNTIME_ROOT) -> dict[str, object]:
    return load_job_result(job_id, runtime_root)
