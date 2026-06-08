from __future__ import annotations

from pathlib import Path

from ulp_project.paths import PROJECT_ROOT
from ulp_project.realtime_yolo_detection_pipeline import model_readiness_status


def test_progress6_9_tree_model_status_not_generic_model_not_ready_when_bestpt_exists() -> None:
    readiness = model_readiness_status()
    bestpt = PROJECT_ROOT / "runs" / "detect" / "v001_pohon_sono_only_v2" / "weights" / "best.pt"
    if bestpt.exists():
        assert readiness["tree_model_status"] == "TREE_MODEL_READY_CANDIDATE"
        assert readiness["model_status"] == "TREE_MODEL_READY_CANDIDATE"
    assert readiness["pole_model_status"] in {"POLE_MODEL_NOT_READY", "POLE_MODEL_READY_CANDIDATE"}
    assert readiness["conductor_model_status"] in {"CONDUCTOR_MODEL_NOT_READY", "CONDUCTOR_MODEL_READY_CANDIDATE"}
    if readiness["pole_model_status"] == "POLE_MODEL_NOT_READY" or readiness["conductor_model_status"] == "CONDUCTOR_MODEL_NOT_READY":
        assert readiness["geometry_readiness"] == "AUTO_GEOMETRY_BLOCKED_WAITING_FOR_POLE_CONDUCTOR_MODEL"
        assert readiness["no_fake_detection"] is True
