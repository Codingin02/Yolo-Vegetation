from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
JS = ROOT / "src" / "ulp_project" / "static" / "progress6_26_yolo_first_switch.js"
CSS = ROOT / "src" / "ulp_project" / "static" / "progress6_26_yolo_first_ui.css"

def test_progress6_26_no_cloud_vision_as_core_loop():
    text = JS.read_text(encoding="utf-8")
    assert "/api/field/session/frame" in text
    assert "CLOUD_VISION_BLOCKED_AS_CORE_LOOP_BY_PROGRESS_6_26" in text

def test_progress6_26_switch_off_clears_overlay():
    text = JS.read_text(encoding="utf-8")
    assert "function stopRealtime" in text
    assert "clearOverlay();" in text
    assert "ai_switch_on: false" in text

def test_progress6_26_shutter_does_not_trigger_detection():
    text = JS.read_text(encoding="utf-8")
    assert "hookShutterEvidenceOnly" in text
    assert "window.PROGRESS626_SHUTTER_EVIDENCE" in text
    assert "Shutter is evidence only" in text

def test_progress6_26_project_class_filter_only():
    text = JS.read_text(encoding="utf-8")
    assert "pohon_sono" in text
    assert "konduktor" in text
    assert "struktur_penyangga" in text
    assert '["pohon_sono", "konduktor", "struktur_penyangga"]' in text

def test_progress6_26_prediction_panel_contains_regression_status():
    text = JS.read_text(encoding="utf-8")
    assert "progress626PredictionPanel" in text
    assert "Clearance" in text
    assert "ETA" in text
    assert "Risk" in text
    assert "Source" in text

def test_progress6_26_icon_status_not_text_chips():
    text = JS.read_text(encoding="utf-8")
    css = CSS.read_text(encoding="utf-8")
    assert "progress626IconHud" in text
    assert "p626CamIcon" in text
    assert "[data-p626-hidden-chip" in css
