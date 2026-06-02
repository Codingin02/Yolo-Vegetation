"""Field capture runtime status and upload contract."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .field_capture import accept_field_capture_upload
from .job_queue import RUNTIME_ROOT


def field_capture_runtime_status() -> dict[str, Any]:
    return {
        "status": "FIELD_CAPTURE_BROWSER_READY",
        "route": "/field-capture",
        "legacy_alias": "/mobile",
        "hp_role": "HP_BROWSER_INPUT_ONLY",
        "processing_center": "LAPTOP_PROCESSING_SERVER",
        "monitoring_primary": "SPREADSHEET_AND_MAP",
    }


def receive_field_capture_input(form: dict[str, Any], image_file: Any | None = None, video_file: Any | None = None, runtime_root: Path = RUNTIME_ROOT) -> dict[str, Any]:
    return accept_field_capture_upload(form, image_file=image_file, video_file=video_file, runtime_root=runtime_root)
