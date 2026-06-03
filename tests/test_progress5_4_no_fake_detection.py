from __future__ import annotations

from pathlib import Path

from ulp_project.progress5_4_field_runtime import process_progress5_4_realtime_frame


def test_progress5_4_model_not_ready_never_uses_payload_detections(tmp_path: Path) -> None:
    result = process_progress5_4_realtime_frame(
        {
            "point_id": "V001_pohon_sono",
            "timestamp_client_ms": 0,
            "detections": [{"class_name": "pohon_sono", "bbox_xyxy": [1, 2, 3, 4]}],
        },
        runtime_root=tmp_path,
    )

    assert result["model_status"] == "MODEL_NOT_READY"
    assert result["detections"] == []
    assert result["no_fake_detection"] is True
    assert "MODEL_NOT_READY" in result["reason_codes"]


def test_progress5_4_debug_coco_is_not_real_model_when_file_missing(tmp_path: Path) -> None:
    result = process_progress5_4_realtime_frame({"point_id": "V001_pohon_sono"}, runtime_root=tmp_path, debug_coco=True)

    assert result["model_status"].startswith("DEBUG_COCO_YOLO_NOT_FIELD_MODEL")
    assert result["debug_mode"] is True
    assert result["detections"] == []
