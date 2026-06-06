from __future__ import annotations

from pathlib import Path

from ulp_project.safe_inference import classify_model_runtime_status, run_safe_predict


def test_missing_model_returns_model_not_ready(tmp_path: Path) -> None:
    result = run_safe_predict(tmp_path / "missing.pt", tmp_path)

    assert result["status"] == "MODEL_NOT_READY"
    assert result["detections"] == []


def test_no_detections_is_weak_model() -> None:
    summary = {
        "status": "UNCLASSIFIED",
        "conf": 0.25,
        "max_det": 20,
        "image_count": 2,
        "total_detections": 0,
        "detections_per_image": {},
        "confidence_stats": {"median": None, "below_0_01_share": 0.0},
    }

    assert classify_model_runtime_status(summary) == "MODEL_WEAK_NO_DETECTION"


def test_low_conf_many_boxes_is_unstable() -> None:
    summary = {
        "status": "UNCLASSIFIED",
        "conf": 0.001,
        "max_det": 300,
        "image_count": 1,
        "total_detections": 300,
        "detections_per_image": {"a.jpg": 300},
        "confidence_stats": {"median": 0.002, "below_0_01_share": 1.0},
    }

    assert classify_model_runtime_status(summary) == "MODEL_UNSTABLE_TOO_MANY_BOXES"


def test_low_conf_any_detection_is_low_conf_unstable() -> None:
    summary = {
        "status": "UNCLASSIFIED",
        "conf": 0.005,
        "max_det": 20,
        "image_count": 1,
        "total_detections": 1,
        "detections_per_image": {"a.jpg": 1},
        "confidence_stats": {"median": 0.004, "below_0_01_share": 1.0},
    }

    assert classify_model_runtime_status(summary) == "MODEL_UNSTABLE_LOW_CONF"
