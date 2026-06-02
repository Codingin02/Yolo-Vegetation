"""Mobile job result contracts."""

from __future__ import annotations

import time
from typing import Any

from .inference_runtime import run_image_inference
from .vegetation_risk_model import score_pohon_sono_risk


def build_mobile_dry_result(job: dict[str, Any], input_path: str | None = None, started_at: float | None = None) -> dict[str, Any]:
    started = started_at if started_at is not None else time.perf_counter()
    inference = run_image_inference(input_path or "mobile-upload-placeholder")
    metadata = job.get("metadata", {}) if isinstance(job.get("metadata"), dict) else {}
    risk_input = {
        "point_id": metadata.get("point_id"),
        "species": "pohon_sono",
        "latitude": metadata.get("lat"),
        "longitude": metadata.get("lon"),
    }
    risk = score_pohon_sono_risk(risk_input)
    latency_ms = int((time.perf_counter() - started) * 1000)
    status = "MODEL_NOT_READY_DRY_RESULT" if inference["status"] == "MODEL_NOT_READY" else "MOBILE_RESULT_READY"
    return {
        "status": status,
        "job_id": job.get("job_id"),
        "model_status": inference["status"],
        "detections": inference.get("detections", []),
        "risk": risk,
        "latency_ms": latency_ms,
        "not_accuracy_claim": True,
        "next_required_action": inference.get("next_required_action"),
    }
