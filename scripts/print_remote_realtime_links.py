from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ulp_project.runtime_links import build_public_links, detect_lan_ips  # noqa: E402


def build_remote_link_help(port: int = 5000) -> str:
    links = build_public_links(port)
    lines = [
        "ULP Progress 5.2 Remote Realtime Links",
        "",
        "LAN mode hanya untuk debug:",
        f"  {links['local_field_capture_url']}",
    ]
    for ip in detect_lan_ips():
        lines.append(f"  http://{ip}:{port}/field-capture")
    lines.extend(
        [
            "",
            "HTTPS tunnel mode adalah target field trial beda jaringan:",
            f"  ngrok http {port}",
            f"  cloudflared tunnel --url http://localhost:{port}",
            "",
            "Setelah tunnel aktif, buka dari HP:",
            f"  {links['public_field_capture_url'] or 'https://<public-tunnel-url>/field-capture'}",
            "",
            "API link runtime:",
            f"  http://127.0.0.1:{port}/api/runtime/public-links",
            "",
            "Status CLI tunnel lokal:",
            f"  ngrok: {'AVAILABLE' if shutil.which('ngrok') else 'NOT_FOUND'}",
            f"  cloudflared: {'AVAILABLE' if shutil.which('cloudflared') else 'NOT_FOUND'}",
            "",
            "Token/authtoken ngrok/cloudflared tidak boleh disimpan di Git.",
            "Camera/GPS otomatis lebih mungkin aktif pada HTTPS secure context.",
            "Fallback tetap tersedia: upload file foto dari HP.",
        ]
    )
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Print Phase 16 LAN and HTTPS tunnel operator links.")
    parser.add_argument("--port", type=int, default=5000)
    args = parser.parse_args(argv)
    print(build_remote_link_help(args.port))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
