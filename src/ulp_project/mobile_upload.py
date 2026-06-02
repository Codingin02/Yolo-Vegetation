"""Compatibility upload handling for browser-based HP field capture.

Runtime writes are restricted to data/runtime, which is ignored by Git.
"""

from __future__ import annotations

import re
import time
from pathlib import Path
from typing import Any

from .job_queue import RUNTIME_ROOT, create_job, write_job_result
from .mobile_result import build_mobile_dry_result
from .network_mode import normalize_network_mode

UPLOADS_DIRNAME = "field_capture_uploads"


def _safe_filename(filename: str) -> str:
    clean = re.sub(r"[^A-Za-z0-9._-]+", "_", filename or "upload.bin").strip("._")
    return clean or "upload.bin"


def build_upload_metadata(form: dict[str, Any]) -> dict[str, Any]:
    network = normalize_network_mode(str(form.get("network_mode") or "same_lan_mode"))
    return {
        "point_id": str(form.get("point_id") or ""),
        "lat": form.get("lat"),
        "lon": form.get("lon"),
        "timestamp": str(form.get("timestamp") or ""),
        "operator_note": str(form.get("operator_note") or ""),
        "network_mode": network["network_mode"],
        "network_status": network["status"],
        "source_device": str(form.get("source_device") or "hp_input_browser"),
    }


def accept_mobile_upload(
    form: dict[str, Any],
    image_file: Any | None = None,
    video_file: Any | None = None,
    runtime_root: Path = RUNTIME_ROOT,
) -> dict[str, Any]:
    started = time.perf_counter()
    metadata = build_upload_metadata(form)
    upload_dir = runtime_root / UPLOADS_DIRNAME
    upload_dir.mkdir(parents=True, exist_ok=True)

    saved_files: dict[str, str] = {}
    for field_name, file_obj in {"image": image_file, "video": video_file}.items():
        if file_obj is None:
            continue
        filename = _safe_filename(getattr(file_obj, "filename", "") or f"{field_name}.bin")
        target = upload_dir / filename
        suffix_counter = 1
        while target.exists():
            target = upload_dir / f"{target.stem}_{suffix_counter}{target.suffix}"
            suffix_counter += 1
        file_obj.save(str(target))
        saved_files[f"{field_name}_filename"] = target.name
        saved_files[f"{field_name}_path"] = str(target)

    metadata.update(saved_files)
    job = create_job(metadata, runtime_root)
    input_path = saved_files.get("image_path") or saved_files.get("video_path") or "field-capture-metadata-only"
    dry_result = build_mobile_dry_result(job, input_path=input_path, started_at=started)
    write_result = write_job_result(str(job["job_id"]), dry_result, runtime_root)
    return {
        "status": "MODEL_NOT_READY_BUT_UPLOAD_ACCEPTED" if dry_result["model_status"] == "MODEL_NOT_READY" else "UPLOAD_ACCEPTED",
        "job_id": job["job_id"],
        "metadata": metadata,
        "saved_files": saved_files,
        "result_status": dry_result["status"],
        "result_json_path": write_result["result_json_path"],
        "latency_ms": dry_result["latency_ms"],
        "not_accuracy_claim": True,
    }
