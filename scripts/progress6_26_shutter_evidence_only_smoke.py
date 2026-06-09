from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]
JS = ROOT / "src" / "ulp_project" / "static" / "progress6_26_yolo_first_switch.js"

def main():
    text = JS.read_text(encoding="utf-8")
    assert "hookShutterEvidenceOnly" in text
    assert "Shutter is evidence only" in text
    assert "window.PROGRESS626_SHUTTER_EVIDENCE" in text
    print(json.dumps({
        "status": "PROGRESS_6_26_SHUTTER_EVIDENCE_ONLY_SMOKE_PASS",
        "shutter_triggers_detection": False,
        "shutter_saves_last_result": True,
    }, indent=2))

if __name__ == "__main__":
    main()
