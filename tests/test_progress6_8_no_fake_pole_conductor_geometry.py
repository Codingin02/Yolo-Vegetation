from __future__ import annotations

from ulp_project.realtime_yolo_detection_pipeline import process_realtime_yolo_frame


def test_progress6_8_tree_only_does_not_fake_pole_conductor_or_clearance() -> None:
    result = process_realtime_yolo_frame({"frame_image_base64": ""})
    assert result["pole_model_status"] == "POLE_MODEL_NOT_READY"
    assert result["conductor_model_status"] == "CONDUCTOR_MODEL_NOT_READY"
    assert result["pole_detected"] is False
    assert result["conductor_detected"] is False
    assert result["geometry"]["no_fake_clearance"] is True
    assert "BLOCKED" in result["geometry"]["geometry_status"]
