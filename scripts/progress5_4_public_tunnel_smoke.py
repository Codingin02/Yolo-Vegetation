from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ulp_project.runtime_links import build_public_links  # noqa: E402


def build_smoke_status() -> dict[str, object]:
    links = build_public_links(port=5000)
    public_url = links.get("public_field_capture_url")
    checks = {
        "schema_ready": {"local_field_capture_url", "lan_field_capture_urls", "public_url_status", "tunnel_status"}.issubset(links),
        "operator_command_ready": "ngrok http 5000" in links.get("manual_tunnel_commands", []),
        "honest_when_tunnel_missing": links.get("public_url_status") in {"PUBLIC_HTTPS_TUNNEL_READY", "PUBLIC_TUNNEL_NOT_RUNNING"},
        "public_url_https_when_present": public_url is None or str(public_url).startswith("https://"),
    }
    status = "PROGRESS5_4_PUBLIC_TUNNEL_SMOKE_PASS" if all(checks.values()) else "PROGRESS5_4_PUBLIC_TUNNEL_SMOKE_FAIL"
    return {"status": status, "checks": checks, "public_field_capture_url": public_url, "links": links}


def main() -> int:
    result = build_smoke_status()
    print(json.dumps(result, indent=2, ensure_ascii=False))
    if result.get("public_field_capture_url"):
        print(result["public_field_capture_url"])
    else:
        print("PUBLIC_TUNNEL_NOT_RUNNING_RUN: ngrok http 5000")
    print(result["status"])
    return 0 if result["status"].endswith("_PASS") else 1


if __name__ == "__main__":
    raise SystemExit(main())
