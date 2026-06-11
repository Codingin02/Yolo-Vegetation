"""Optional AI visual validator for Plan C snapshots.

The validator is intentionally conservative: it never creates boxes, never
computes clearance, and does not send image data unless a future explicit
implementation is added.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

AI_ENV_CANDIDATES = ["OPENAI_API_KEY", "GEMINI_API_KEY", "OPENROUTER_API_KEY"]


def validate_snapshot_with_ai(original_path: Path, *, metadata: dict[str, Any] | None = None) -> dict[str, Any]:
    metadata = metadata or {}
    configured = [name for name in AI_ENV_CANDIDATES if bool(os.environ.get(name))]
    key_present = bool(configured)
    if not key_present:
        return {
            "status": "AI_VALIDATOR_DISABLED",
            "enabled": False,
            "visual_quality": "not_run",
            "object_visibility": "not_run",
            "retake_recommendation": "AI validator disabled; gunakan ringkasan YOLO dan geometry.",
            "short_validation_summary": "AI vision validator tidak dijalankan karena API key tidak tersedia di environment.",
            "image_path": str(original_path),
            "metadata_keys": sorted(metadata.keys()),
            "configured_provider_count": 0,
            "provider_names_redacted": [],
            "no_secret_logged": True,
        }

    return {
        "status": "AI_VALIDATOR_READY",
        "enabled": False,
        "execution_status": "READY_NOT_SENT",
        "visual_quality": "manual_review_required",
        "object_visibility": "not_evaluated_by_ai",
        "retake_recommendation": "AI key terdeteksi, tetapi pengiriman image dinonaktifkan sampai wrapper tervalidasi.",
        "short_validation_summary": "AI validator siap secara konfigurasi, namun tidak menggantikan YOLO atau Python geometry.",
        "image_path": str(original_path),
        "metadata_keys": sorted(metadata.keys()),
        "configured_provider_count": len(configured),
        "provider_names_redacted": ["configured_provider" for _ in configured],
        "does_not_create_bounding_box": True,
        "does_not_compute_clearance": True,
        "no_secret_logged": True,
    }
