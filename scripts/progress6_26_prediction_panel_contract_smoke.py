from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]
JS = ROOT / "src" / "ulp_project" / "static" / "progress6_26_yolo_first_switch.js"
CSS = ROOT / "src" / "ulp_project" / "static" / "progress6_26_yolo_first_ui.css"

def main():
    js = JS.read_text(encoding="utf-8")
    css = CSS.read_text(encoding="utf-8")
    assert "progress626PredictionPanel" in js
    assert "Clearance" in js
    assert "ETA" in js
    assert "Risk" in js
    assert "Source" in js
    assert "progress626-prediction-panel" in css
    assert "backdrop-filter" in css
    print(json.dumps({
        "status": "PROGRESS_6_26_PREDICTION_PANEL_CONTRACT_SMOKE_PASS",
        "panel_position": "above_shutter_left",
        "contains_regression_eta_risk": True,
    }, indent=2))

if __name__ == "__main__":
    main()
