from __future__ import annotations

import argparse
import socket
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ulp_project.flask_app import create_app  # noqa: E402


def detect_lan_ip() -> str:
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.connect(("8.8.8.8", 80))
            return sock.getsockname()[0]
    except OSError:
        try:
            return socket.gethostbyname(socket.gethostname())
        except OSError:
            return "127.0.0.1"


def print_startup_help(host: str, port: int) -> None:
    lan_ip = detect_lan_ip()
    print("ULP field capture server starting")
    print(f"Local laptop URL : http://127.0.0.1:{port}/field-capture")
    print(f"HP same WiFi URL : http://{lan_ip}:{port}/field-capture")
    print(f"Bind host        : {host}")
    print("")
    print("Jika HP tidak bisa membuka URL:")
    print("1. Pastikan HP dan laptop berada di WiFi/hotspot yang sama.")
    print("2. Pastikan Windows Firewall mengizinkan Python/port 5000.")
    print("3. Coba ping endpoint: /api/latency/ping")
    print("4. Jika kamera browser tidak aktif di HTTP/LAN, gunakan upload file/foto dari galeri.")
    print("5. Jika beda jaringan, gunakan ngrok/cloudflared HTTPS manual tanpa menyimpan token di Git.")


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
