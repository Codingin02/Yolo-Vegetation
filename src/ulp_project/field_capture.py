"""Browser-based HP field capture helpers.

HP is only an input client. The laptop Flask server remains the processing
center and writes runtime files only under ignored data/runtime.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .job_queue import RUNTIME_ROOT, load_job, load_job_result
from .mobile_upload import accept_mobile_upload


def accept_field_capture_upload(
    form: dict[str, Any],
    image_file: Any | None = None,
    video_file: Any | None = None,
    runtime_root: Path = RUNTIME_ROOT,
) -> dict[str, Any]:
    result = accept_mobile_upload(form, image_file=image_file, video_file=video_file, runtime_root=runtime_root)
    return {
        **result,
        "capture_architecture": "field_input_browser",
        "hp_role": "input_client_only",
        "processing_center": "laptop_flask_server",
        "monitoring_primary": "csv_google_sheets_and_map",
    }


def load_field_capture_job(job_id: str, runtime_root: Path = RUNTIME_ROOT) -> dict[str, object]:
    return load_job(job_id, runtime_root)


def load_field_capture_result(job_id: str, runtime_root: Path = RUNTIME_ROOT) -> dict[str, object]:
    return load_job_result(job_id, runtime_root)
