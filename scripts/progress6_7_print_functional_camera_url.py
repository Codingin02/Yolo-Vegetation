from __future__ import annotations

import json
import socket
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ulp_project.runtime_links import build_public_links  # noqa: E402


def _lan_host() -> str:
    try:
        return socket.gethostbyname(socket.gethostname())
    except OSError:
        return "<LAN-IP>"


def main() -> int:
    links = build_public_links(port=5000)
    public = links.get("public_https_url") or "https://<public-tunnel-url>"
    payload = {
        "status": "PROGRESS_6_7_FUNCTIONAL_CAMERA_URLS_READY",
        "local_capture": "http://127.0.0.1:5000/field-capture",
        "local_camera": "http://127.0.0.1:5000/field-camera?session_id=<session_id>",
        "lan_capture_debug_only": f"http://{_lan_host()}:5000/field-capture",
        "public_capture": f"{public}/field-capture",
        "public_camera_after_start": f"{public}/field-camera?session_id=<session_id>",
        "public_map_after_shutter": f"{public}/field-map/session/<session_id>",
        "public_spreadsheet_after_shutter": f"{public}/field-spreadsheet/session/<session_id>",
        "operator_note": "Result dibuka setelah Shutter melalui spreadsheet evidence lokal; MODEL_NOT_READY tetap aman tanpa deteksi palsu.",
    }
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
