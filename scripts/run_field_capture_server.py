from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ulp_project.flask_app import create_app  # noqa: E402
from ulp_project.runtime_links import detect_lan_ips, format_startup_links  # noqa: E402


def print_startup_help(host: str, port: int) -> None:
    print(format_startup_links(host=host, port=port))
    print("")
    print("Jika HP tidak bisa membuka URL:")
    print("1. Pastikan HP dan laptop berada di WiFi/hotspot yang sama.")
    print("2. Pastikan Windows Firewall mengizinkan Python/port 5000.")
    print("3. Jangan pakai localhost dari HP; pakai LAN URL kandidat.")
    print("4. Coba ping endpoint: /api/latency/ping")
    print("5. Jika port 5000 bentrok, jalankan dengan --port 5001.")
    print("6. Jika kamera browser tidak aktif di HTTP/LAN, gunakan upload file/foto dari galeri.")
    print("7. Jika beda jaringan, gunakan ngrok/cloudflared HTTPS manual tanpa menyimpan token di Git.")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run browser-based HP field capture server on the laptop.")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=5000)
    args = parser.parse_args(argv)
    app = create_app()
    print_startup_help(args.host, args.port)
    app.run(host=args.host, port=args.port, debug=False)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
