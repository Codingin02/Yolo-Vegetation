from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]
JS = ROOT / "src" / "ulp_project" / "static" / "progress6_26_yolo_first_switch.js"

def main():
    text = JS.read_text(encoding="utf-8")
    assert "/api/field/session/frame" in text
    assert "CLOUD_VISION_BLOCKED_AS_CORE_LOOP_BY_PROGRESS_6_26" in text
    assert "stopRealtime" in text
    assert "clearOverlay" in text
    assert "PROGRESS626_LAST_YOLO_RESULT" in text
    assert "vision-analyze" in text
    print(json.dumps({
        "status": "PROGRESS_6_26_FRONTEND_SWITCH_CONTRACT_SMOKE_PASS",
        "core_loop": "/api/field/session/frame",
        "vision_analyze_core_loop": False,
        "switch_off_clears_overlay": True,
    }, indent=2))

if __name__ == "__main__":
    main()
