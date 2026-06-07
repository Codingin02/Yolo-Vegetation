from __future__ import annotations

from ulp_project.tree_detection_runtime import TREE_MODEL_PATH, infer_tree_candidate, tree_model_status


def test_progress6_7_tree_model_candidate_status_if_bestpt_exists() -> None:
    status = tree_model_status()
    if TREE_MODEL_PATH.exists():
        assert status["tree_model_status"] == "TREE_MODEL_READY_CANDIDATE"
        assert status["production_status"] == "NOT_FINAL_CANDIDATE_DETECTION"
    else:
        assert status["tree_model_status"] == "TREE_MODEL_NOT_READY"


def test_progress6_7_tree_inference_safe_no_fake_pole_conductor() -> None:
    result = infer_tree_candidate({"frame_image_base64": "%%%bad"})
    assert result["status"] == "FRAME_DECODE_FAILED_SAFE"
    assert result["pole_detected"] is False
    assert result["conductor_detected"] is False
    assert result["no_fake_detection"] is True
