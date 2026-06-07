from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_progress6_8_auto_yolo_pipeline_is_primary_not_manual() -> None:
    pipeline = (ROOT / "src" / "ulp_project" / "realtime_yolo_detection_pipeline.py").read_text(encoding="utf-8")
    camera = (ROOT / "src" / "ulp_project" / "templates" / "field_camera.html").read_text(encoding="utf-8")
    assert "process_realtime_yolo_frame" in pipeline
    assert "manual operator input is not a primary measurement path" in pipeline.lower()
    assert "Manual" in camera
    assert "Report" not in camera[camera.index('<nav class="camera-bottom-bar"') : camera.index("</nav>", camera.index('<nav class="camera-bottom-bar"'))]
