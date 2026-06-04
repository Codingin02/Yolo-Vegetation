from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ulp_project.flask_app import create_app  # noqa: E402


REQUIRED_TOKENS = [
    "Current URL mode",
    "HTTPS_PUBLIC_READY",
    "LAN_HTTP_DEBUG_ONLY",
    "LOCALHOST_DEBUG_ONLY",
    "INSECURE_CONTEXT_CAMERA_GPS_BLOCKED",
    "Copy Public HTTPS URL",
    "Open Public HTTPS URL",
    "Copy LAN URL hanya untuk debug",
    "Izinkan Kamera",
    "Izinkan GPS",
    "Jepret / Shutter",
    "Advanced Debug Only / Manual Provisional",
    "Jangan digunakan sebagai klaim hasil final.",
]


def build_smoke_status() -> dict[str, object]:
    html = create_app().test_client().get("/field-capture").get_data(as_text=True)
    checks = {token: token in html for token in REQUIRED_TOKENS}
    status = "PROGRESS5_4_CAMERA_UI_CONTRACT_SMOKE_PASS" if all(checks.values()) else "PROGRESS5_4_CAMERA_UI_CONTRACT_SMOKE_FAIL"
    return {"status": status, "checks": checks}


def main() -> int:
    result = build_smoke_status()
    print(json.dumps(result, indent=2, ensure_ascii=False))
    print(result["status"])
    return 0 if result["status"].endswith("_PASS") else 1


if __name__ == "__main__":
    raise SystemExit(main())
