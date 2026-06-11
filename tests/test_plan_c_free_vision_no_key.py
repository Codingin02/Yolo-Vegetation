from pathlib import Path

from ulp_project.plan_c_free_vision_config import load_free_vision_config
from ulp_project.plan_c_free_vision_detector import detect_yolo_compatible_from_snapshot
from ulp_project.plan_c_yolo_compatible_renderer import render_yolo_compatible_annotation


def test_free_vision_no_key_does_not_crash(monkeypatch, tmp_path):
    monkeypatch.setenv("PLAN_C_VISION_MODE", "free_only")
    monkeypatch.setenv("PLAN_C_OPERATOR_HIDE_PROVIDER", "true")
    monkeypatch.setenv("GEMINI_API_KEY", "")
    monkeypatch.setenv("GROQ_API_KEY", "")
    monkeypatch.setenv("OPENROUTER_API_KEY", "")
    monkeypatch.setenv("OPENROUTER_VISION_MODEL", "")

    image_path = tmp_path / "snapshot.jpg"
    _write_jpeg(image_path)
    config = load_free_vision_config()

    result = detect_yolo_compatible_from_snapshot(
        image_path,
        image_width=64,
        image_height=48,
        config=config,
        yolo_result={"status": "YOLO_MODEL_NOT_READY", "detections": []},
    )

    assert result["status"] == "DATA_TIDAK_CUKUP"
    assert result["pipeline_status"] == "FREE_VISION_ALL_DISABLED"
    assert result["detections"] == []
    assert result["no_fake_detection"] is True

    annotated = tmp_path / "annotated.jpg"
    render = render_yolo_compatible_annotation(image_path, annotated, result["detections"])
    assert annotated.exists()
    assert render["detection_count"] == 0


def _write_jpeg(path: Path) -> None:
    from PIL import Image

    image = Image.new("RGB", (64, 48), color=(70, 90, 50))
    image.save(path, format="JPEG", quality=90)
