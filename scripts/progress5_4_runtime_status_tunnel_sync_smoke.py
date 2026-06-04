from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ulp_project.flask_app import create_app  # noqa: E402


def build_smoke_status() -> dict[str, object]:
    client = create_app().test_client()
    tunnel = client.get("/api/runtime/tunnel-status").get_json()
    runtime = client.get("/api/runtime/status").get_json()
    public_links = runtime.get("public_links", {})
    tunnel_ready = tunnel.get("status") == "NGROK_HTTPS_TUNNEL_READY"
    checks = {
        "tunnel_endpoint_ready": tunnel.get("status") is not None,
        "runtime_endpoint_ready": runtime.get("status") is not None,
        "runtime_exposes_tunnel_status": runtime.get("tunnel_status") is not None,
        "no_no_public_when_tunnel_ready": (not tunnel_ready) or public_links.get("status") != "NO_PUBLIC_TUNNEL_CONFIGURED",
        "recommended_command_when_missing": tunnel_ready or tunnel.get("operator_command") == "ngrok http 5000",
    }
    status = "PROGRESS5_4_RUNTIME_STATUS_TUNNEL_SYNC_SMOKE_PASS" if all(checks.values()) else "PROGRESS5_4_RUNTIME_STATUS_TUNNEL_SYNC_SMOKE_FAIL"
    return {"status": status, "checks": checks, "tunnel_status": tunnel.get("status"), "runtime_tunnel_status": runtime.get("tunnel_status")}


def main() -> int:
    result = build_smoke_status()
    print(json.dumps(result, indent=2, ensure_ascii=False))
    print(result["status"])
    return 0 if result["status"].endswith("_PASS") else 1


if __name__ == "__main__":
    raise SystemExit(main())
