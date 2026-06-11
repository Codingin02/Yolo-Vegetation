"""Review-only pseudo-label preparation for Plan C priority dataset."""

from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Any

from .plan_c_priority_acquisition_config import PSEUDO_LABEL_DIR

PROMPTS = {
    "pohon_sono": "Pterocarpus indicus tree, Angsana tree, Narra tree, Sonokembang tree, tree trunk and canopy of Pterocarpus indicus",
    "konduktor": "overhead electrical conductor, power line cable, medium voltage distribution conductor, overhead line wire",
    "struktur_penyangga": "utility pole, electric pole, concrete pole, crossarm, pole top electrical structure",
}


def pseudo_label_engine_available() -> bool:
    return importlib.util.find_spec("groundingdino") is not None or importlib.util.find_spec("segment_anything") is not None


def create_review_only_pseudo_labels(rows: list[dict[str, Any]], *, output_dir: Path | None = None) -> dict[str, Any]:
    output_dir = output_dir or PSEUDO_LABEL_DIR
    output_dir.mkdir(parents=True, exist_ok=True)
    if not pseudo_label_engine_available():
        return {
            "ok": True,
            "status": "PSEUDO_LABEL_ENGINE_NOT_AVAILABLE_USE_ROBOFLOW_MANUAL_LABEL",
            "needs_review": True,
            "not_ground_truth": True,
            "labels_created": 0,
            "prompts": PROMPTS,
        }
    # The engine is intentionally not invoked automatically in this stage.
    return {
        "ok": True,
        "status": "PSEUDO_LABEL_REVIEW_REQUIRED_ENGINE_AVAILABLE_NOT_RUN_AUTOMATICALLY",
        "needs_review": True,
        "not_ground_truth": True,
        "labels_created": 0,
        "candidate_count": len(rows),
        "prompts": PROMPTS,
    }


def empty_label_for_manual_review(path: Path) -> dict[str, Any]:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_text("", encoding="utf-8")
    return {
        "status": "PSEUDO_LABEL_REVIEW_REQUIRED",
        "needs_review": True,
        "not_ground_truth": True,
        "label_path": str(path),
    }
