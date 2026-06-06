from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ulp_project.flask_app import create_app  # noqa: E402


REQUIRED_ROUTE_TOKENS = {
    "/field-capture": [
        "Monitoring Vegetasi 20 kV",
        "session-start",
        "session-stop",
        "field_session.js",
        "field_capture_glass.css",
        "FOREGROUND_RECORDING_REQUIRED",
    ],
    "/field-report": ["Field Report", "Download CSV", "Open Map", "field_capture_glass.css"],
    "/field-result": [
        "Field Result",
        "FIELD_RESULT_PROVISIONAL",
        "MODEL_NOT_READY_NO_FAKE_DETECTION",
        "field_capture_glass.css",
    ],
    "/field-manual-input": [
        "Manual Input",
        "MANUAL_OPERATOR_INPUT_NOT_AI_DETECTION",
        "field_capture_glass.css",
    ],
}


def build_smoke_status() -> dict[str, object]:
    client = create_app().test_client()
    checks: dict[str, bool] = {}
    for route, tokens in REQUIRED_ROUTE_TOKENS.items():
        response = client.get(route)
        html = response.get_data(as_text=True)
        checks[f"{route}:200"] = response.status_code == 200
        for token in tokens:
            checks[f"{route}:{token}"] = token in html
    status = "PROGRESS_6_2_UI_ROUTE_SMOKE_PASS" if all(checks.values()) else "PROGRESS_6_2_UI_ROUTE_SMOKE_FAIL"
    return {"status": status, "checks": checks}


def main() -> int:
    result = build_smoke_status()
    print(json.dumps(result, indent=2, ensure_ascii=False))
    print(result["status"])
    return 0 if result["status"].endswith("_PASS") else 1


if __name__ == "__main__":
    raise SystemExit(main())
