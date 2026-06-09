from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]
JS = ROOT / "src" / "ulp_project" / "static" / "progress6_26_yolo_first_switch.js"
CSS = ROOT / "src" / "ulp_project" / "static" / "progress6_26_yolo_first_ui.css"

def main():
    js = JS.read_text(encoding="utf-8")
    css = CSS.read_text(encoding="utf-8")
    assert "progress626IconHud" in js
    assert "p626CamIcon" in js
    assert "p626GpsIcon" in js
    assert "p626YoloIcon" in js
    assert "p626ModelIcon" in js
    assert "p626ShutterIcon" in js
    assert "[data-p626-hidden-chip" in css
    print(json.dumps({
        "status": "PROGRESS_6_26_ICON_STATUS_CONTRACT_SMOKE_PASS",
        "operator_hud": "icon_only",
        "legacy_text_chips_hidden": True,
    }, indent=2))

if __name__ == "__main__":
    main()
