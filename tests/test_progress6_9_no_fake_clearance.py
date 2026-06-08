from __future__ import annotations

from ulp_project.realtime_yolo_detection_pipeline import process_realtime_yolo_frame


def test_progress6_9_no_fake_clearance_without_pole_conductor() -> None:
    result = process_realtime_yolo_frame(
        {
            "mock_detections": [
                {"class_name": "pohon_sono", "confidence": 0.9, "bbox_xyxy": [10, 10, 80, 220]},
            ]
        }
    )
    assert result["tree_detected"] is True
    assert result["pole_detected"] is False
    assert result["conductor_detected"] is False
    assert result["geometry"]["geometry_status"] in {"GEOMETRY_BLOCKED_NO_POLE", "GEOMETRY_BLOCKED_NO_CONDUCTOR", "GEOMETRY_BLOCKED_NO_POLE_CONDUCTOR"}
    assert result["geometry"].get("estimated_clearance_m") is None
    assert result["no_fake_detection"] is True
