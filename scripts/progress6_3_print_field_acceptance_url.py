from __future__ import annotations

import json
import socket
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ulp_project.runtime_links import build_public_links


def main() -> int:
    links = build_public_links(port=5000)
    host = _lan_ip()
    public = links.get("public_https_url") or "PUBLIC_TUNNEL_NOT_RUNNING"
    result = {
        "status": "PROGRESS_6_3_FIELD_ACCEPTANCE_URLS_READY",
        "local_field_capture": "http://localhost:5000/field-capture",
        "local_field_acceptance": "http://localhost:5000/field-acceptance",
        "lan_debug_field_capture": f"http://{host}:5000/field-capture",
        "lan_debug_field_acceptance": f"http://{host}:5000/field-acceptance",
        "public_https_url": public,
        "public_field_capture": f"{public.rstrip('/')}/field-capture" if str(public).startswith("https://") else public,
        "public_field_acceptance": f"{public.rstrip('/')}/field-acceptance" if str(public).startswith("https://") else public,
        "public_field_report": f"{public.rstrip('/')}/field-report" if str(public).startswith("https://") else public,
        "public_field_result": f"{public.rstrip('/')}/field-result" if str(public).startswith("https://") else public,
        "lan_http_is_debug_only": True,
    }
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


def _lan_ip() -> str:
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.connect(("8.8.8.8", 80))
            return sock.getsockname()[0]
    except OSError:
        return "127.0.0.1"


if __name__ == "__main__":
    raise SystemExit(main())
