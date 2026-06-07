"""Runtime API helpers for pohon_sono growth prior prediction."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .growth_prior_loader import DEFAULT_POHON_SONO_XLSX, growth_prior_dataset_status, sample_proxy_row
from .pohon_sono_growth_model import predict_pohon_sono_growth


def growth_prior_status(path: Path | None = None) -> dict[str, Any]:
    status = growth_prior_dataset_status(path)
    return {
        **status,
        "runtime_status": "GROWTH_PRIOR_RUNTIME_READY",
        "proxy_not_field_observed": True,
        "no_fake_final_claim": True,
    }


def growth_prior_sample(point_id: str = "V001_pohon_sono", path: Path | None = None) -> dict[str, Any]:
    status = growth_prior_dataset_status(path)
    if not Path(path or DEFAULT_POHON_SONO_XLSX).exists():
        return {**status, "point_id": point_id, "sample": {}}
    try:
        sample = sample_proxy_row(point_id, path)
    except Exception as exc:  # pragma: no cover - corrupted external xlsx
        return {**status, "status": "GROWTH_PRIOR_DATASET_INVALID", "error_type": type(exc).__name__, "message": str(exc)[:300], "sample": {}}
    return {**status, "point_id": point_id, "sample": sample}


def predict_growth_prior(payload: dict[str, Any] | None = None, *, path: Path | None = None) -> dict[str, Any]:
    payload = dict(payload or {})
    status = growth_prior_dataset_status(path)
    sample: dict[str, Any] = {}
    if status.get("status") != "GROWTH_PRIOR_DATASET_NOT_FOUND":
        try:
            sample = sample_proxy_row(str(payload.get("point_id") or "V001_pohon_sono"), path)
        except Exception:
            sample = {}
    merged = {**sample, **payload, "source_status": sample.get("source_status") or "PROXY_NOT_FIELD_OBSERVED"}
    prediction = predict_pohon_sono_growth(merged)
    if status.get("status") == "GROWTH_PRIOR_DATASET_NOT_FOUND":
        prediction["growth_prior_status"] = "GROWTH_PRIOR_DATASET_NOT_FOUND"
    elif status.get("status") == "GROWTH_PRIOR_DATASET_INVALID":
        prediction["growth_prior_status"] = "GROWTH_PRIOR_DATASET_INVALID"
    return {
        **prediction,
        "dataset_status": status.get("status"),
        "dataset_row_count": status.get("row_count", 0),
        "missing_columns": status.get("missing_columns", []),
        "source_status": "PROXY_NOT_FIELD_OBSERVED",
        "proxy_not_field_observed": True,
        "no_fake_final_claim": True,
    }
