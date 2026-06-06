from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
JS = ROOT / "src" / "ulp_project" / "static" / "field_session.js"


def run_smoke() -> dict[str, object]:
    text = JS.read_text(encoding="utf-8")
    required = [
        'document.addEventListener("visibilitychange", handleVisibilityChange)',
        "PAGE_HIDDEN_BROWSER_MAY_THROTTLE",
        "FOREGROUND_RECORDING_ACTIVE",
        "frame_process_interval_ms = 3000",
        "browser_throttle_warning",
    ]
    missing = [item for item in required if item not in text]
    return {
        "status": "PROGRESS_6_3_VISIBILITY_POLICY_SMOKE_PASS" if not missing else "PROGRESS_6_3_VISIBILITY_POLICY_FAILED",
        "missing": missing,
        "foreground_recording_not_background_claim": True,
    }


def main() -> int:
    result = run_smoke()
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result["status"] == "PROGRESS_6_3_VISIBILITY_POLICY_SMOKE_PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
