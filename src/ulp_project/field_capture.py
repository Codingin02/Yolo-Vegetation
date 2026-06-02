"""Browser-based HP field capture helpers.

HP is only an input client. The laptop Flask server remains the processing
center and writes runtime files only under ignored data/runtime.
"""

from __future__ import annotations

import hashlib
import time
from pathlib import Path
from typing import Any

from .job_queue import RUNTIME_ROOT, load_job, load_job_result, write_job_result
from .mobile_upload import accept_mobile_upload
from .field_inspection_record import parse_float
from .phase9_monitoring import append_monitoring_row, write_phase9_risk_map  # compatibility for older tests
from .realtime_field_pipeline import process_realtime_inspection

DEDUP_WINDOW_SEC = 5.0
_RECENT_REQUESTS: dict[str, tuple[float, dict[str, Any]]] = {}


def accept_field_capture_upload(
    form: dict[str, Any],
    image_file: Any | None = None,
    video_file: Any | None = None,
    runtime_root: Path = RUNTIME_ROOT,
) -> dict[str, Any]:
    started = time.perf_counter()
    fingerprint = build_capture_fingerprint(form, image_file=image_file, video_file=video_file, runtime_root=runtime_root)
    duplicate = _duplicate_response(fingerprint)
    if duplicate is not None:
        return duplicate
    result = accept_mobile_upload(form, image_file=image_file, video_file=video_file, runtime_root=runtime_root)
    job_id = str(result.get("job_id", ""))
    image_path = result.get("saved_files", {}).get("image_path", "") if isinstance(result.get("saved_files"), dict) else ""
    pipeline = process_realtime_inspection({**form, "job_id": job_id}, photo_path=image_path, write_outputs=True)
    response = {
        "status": pipeline["status"],
        "mode": "IMAGE_CAPTURE_ONLY_MODEL_NOT_READY" if pipeline["status"] == "INSUFFICIENT_DATA" else "PROVISIONAL_MANUAL_DEMO",
        "job_id": job_id,
        "inspection_id": pipeline["inspection_id"],
        "point_id": pipeline["point_id"],
        "species": pipeline["species"],
        "asset_type": pipeline["asset_type"],
        "eta_days": pipeline["eta_days"],
        "eta_months": pipeline["eta_months"],
        "risk_priority": pipeline["risk_priority"],
        "action_recommendation": pipeline["action_recommendation"],
        "reason": pipeline["reason"],
        "latency_ms": result.get("latency_ms", 0),
        "gps": pipeline["gps"],
        "report_written": pipeline["report_written"],
        "report_path": pipeline["report_path"],
        "report_status": pipeline.get("report_status"),
        "report_operator_warning": pipeline.get("report_operator_warning"),
        "map_marker_written": pipeline["map_marker_written"],
        "map_path": pipeline["map_path"],
        "map_reason": pipeline["map_reason"],
        "clearance_m": pipeline.get("clearance_m"),
        "growth_rate_m_per_day": pipeline.get("growth_rate_m_per_day"),
        "adjusted_growth_rate_m_per_day": pipeline.get("adjusted_growth_rate_m_per_day"),
        "model_status": pipeline["model_status"],
        "calibration_status": pipeline["calibration_status"],
        "environment_source_status": pipeline["environmental_data_status"],
        "environmental_data_status": pipeline["environmental_data_status"],
        "confidence_status": pipeline["confidence_status"],
        "required_missing_inputs": pipeline["required_missing_inputs"],
        "csv_status_link": pipeline["report_path"],
        "map_status_link": pipeline["map_path"],
        "latest_job_id": job_id,
        "request_dedup_status": "ACCEPTED_NEW",
        "queue_length": 1,
        "processing_latency_ms": int((time.perf_counter() - started) * 1000),
        "not_accuracy_claim": True,
    }
    write_job_result(job_id, response, runtime_root)
    final_response = {
        **response,
        "capture_architecture": "field_input_browser",
        "hp_role": "input_client_only",
        "processing_center": "laptop_flask_server",
        "monitoring_primary": "csv_google_sheets_and_map",
    }
    _RECENT_REQUESTS[fingerprint] = (time.monotonic(), final_response)
    _trim_recent_requests()
    return final_response


def load_field_capture_job(job_id: str, runtime_root: Path = RUNTIME_ROOT) -> dict[str, object]:
    return load_job(job_id, runtime_root)


def load_field_capture_result(job_id: str, runtime_root: Path = RUNTIME_ROOT) -> dict[str, object]:
    return load_job_result(job_id, runtime_root)


def build_capture_fingerprint(
    form: dict[str, Any],
    image_file: Any | None = None,
    video_file: Any | None = None,
    runtime_root: Path = RUNTIME_ROOT,
) -> str:
    image_name = getattr(image_file, "filename", "") if image_file is not None else ""
    video_name = getattr(video_file, "filename", "") if video_file is not None else ""
    explicit = form.get("capture_fingerprint") or form.get("client_submit_id")
    parts = [
        str(runtime_root),
        str(explicit or ""),
        str(form.get("point_id", "")),
        str(form.get("species", "")),
        str(form.get("asset_type", "")),
        str(form.get("lat") or form.get("latitude") or ""),
        str(form.get("lon") or form.get("longitude") or ""),
        str(form.get("clearance_m", "")),
        str(form.get("growth_rate_m_per_day", "")),
        str(image_name),
        str(video_name),
    ]
    return hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()


def _duplicate_response(fingerprint: str) -> dict[str, Any] | None:
    item = _RECENT_REQUESTS.get(fingerprint)
    if item is None:
        return None
    created_at, response = item
    age = time.monotonic() - created_at
    if age > DEDUP_WINDOW_SEC:
        return None
    return {
        **response,
        "status": "DUPLICATE_COOLESCED",
        "request_dedup_status": "DUPLICATE_COOLESCED",
        "duplicate_age_sec": round(age, 3),
        "report_written": False,
        "map_marker_written": False,
        "reason": "Duplicate field capture payload received within 5 seconds; previous job was reused.",
        "latest_job_id": response.get("job_id"),
        "queue_length": 0,
    }


def _trim_recent_requests() -> None:
    now = time.monotonic()
    for key, (created_at, _) in list(_RECENT_REQUESTS.items()):
        if now - created_at > DEDUP_WINDOW_SEC * 4:
            _RECENT_REQUESTS.pop(key, None)
