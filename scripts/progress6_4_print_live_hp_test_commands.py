from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ulp_project.runtime_links import build_public_links


def build_live_hp_commands() -> dict[str, object]:
    links = build_public_links(port=5000)
    public = str(links.get("public_https_url") or "").rstrip("/")
    public_capture = f"{public}/field-capture" if public.startswith("https://") else "https://<public-tunnel-url>/field-capture"
    public_acceptance = f"{public}/field-acceptance" if public.startswith("https://") else "https://<public-tunnel-url>/field-acceptance"
    return {
        "status": "PROGRESS_6_4_LIVE_HP_TEST_COMMANDS_READY",
        "terminal_1": [
            "Set-Location E:\\Projects\\ULP_Project",
            ".\\venv\\Scripts\\python.exe scripts\\run_remote_realtime_server.py --host 0.0.0.0 --port 5000",
        ],
        "terminal_2": ["ngrok http 5000"],
        "terminal_3": [
            ".\\venv\\Scripts\\python.exe scripts\\progress6_4_live_field_acceptance_preflight.py",
            ".\\venv\\Scripts\\python.exe scripts\\operator_command_center.py --print-field-acceptance-url",
        ],
        "hp_urls": {
            "field_capture": public_capture,
            "field_acceptance": public_acceptance,
        },
        "operator_hp_steps": [
            "Buka public HTTPS URL.",
            "Tekan Start.",
            "Izinkan kamera.",
            "Izinkan lokasi.",
            "Tunggu GPS_READY atau GPS_ACCURACY_LOW.",
            "Pastikan preview kamera muncul.",
            "Tekan Shutter.",
            "Buka Report.",
            "Buka Result.",
            "Buka Acceptance.",
            "Isi device/network/operator note.",
            "Tekan Submit Acceptance.",
        ],
        "model_not_ready_is_allowed_for_acceptance": True,
        "acceptance_is_not_model_accuracy_claim": True,
    }


def main() -> int:
    print(json.dumps(build_live_hp_commands(), indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
