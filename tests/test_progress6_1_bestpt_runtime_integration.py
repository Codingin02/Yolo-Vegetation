from __future__ import annotations

from pathlib import Path

from ulp_project.progress6_1_labeling import check_trained_model, integrate_bestpt_runtime


def test_progress6_1_missing_bestpt_is_safe_model_not_ready(tmp_path: Path) -> None:
    result = check_trained_model(tmp_path / "best.pt")

    assert result["status"] == "BESTPT_NOT_FOUND"
    assert result["runtime_integration"] == "MODEL_NOT_READY"


def test_progress6_1_runtime_candidate_path_registered() -> None:
    result = integrate_bestpt_runtime()

    assert result["status"] == "BESTPT_RUNTIME_PATH_REGISTERED"
    assert result["do_not_commit_weights"] is True
