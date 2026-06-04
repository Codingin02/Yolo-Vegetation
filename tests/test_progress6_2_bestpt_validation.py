from __future__ import annotations

from pathlib import Path

from ulp_project.progress6_2_training import progress6_2_bestpt_handoff_status


def test_progress6_2_missing_bestpt_stays_model_not_ready(tmp_path: Path) -> None:
    result = progress6_2_bestpt_handoff_status(tmp_path / "best.pt")

    assert result["status"] == "BESTPT_NOT_READY_MODEL_NOT_READY_SAFE_MODE"
    assert result["model"]["status"] == "BESTPT_NOT_FOUND"
    assert result["no_fake_detection"] is True
