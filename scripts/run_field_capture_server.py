from __future__ import annotations

import argparse
import socket
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ulp_project.flask_app import create_app  # noqa: E402


def _is_good_lan_ip(value: str) -> bool:
    if not value or value.startswith("127.") or value.startswith("169.254."):
        return False
    if value.startswith("172.") or value.startswith("192.168.") or value.startswith("10."):
        return True
    return "." in value


def detect_lan_ips() -> list[str]:
    candidates: list[str] = []
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.connect(("8.8.8.8", 80))
            candidates.append(sock.getsockname()[0])
    except OSError:
        pass
    try:
        for info in socket.getaddrinfo(socket.gethostname(), None, socket.AF_INET):
            candidates.append(info[4][0])
    except OSError:
        pass
    try:
        completed = subprocess.run(["ipconfig"], text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
        for line in completed.stdout.splitlines():
            if "IPv4" in line and ":" in line:
                candidates.append(line.split(":", 1)[1].strip())
    except OSError:
        pass
    stable: list[str] = []
    for candidate in candidates:
        if _is_good_lan_ip(candidate) and candidate not in stable:
            stable.append(candidate)
    return stable


def print_startup_help(host: str, port: int) -> None:
    lan_ips = detect_lan_ips()
    print("ULP field capture server starting")
    print(f"Local URL        : http://127.0.0.1:{port}/field-capture")
    if lan_ips:
        for ip in lan_ips:
            print(f"LAN URL kandidat : http://{ip}:{port}/field-capture")
    else:
        print("LAN URL kandidat : IP belum terdeteksi otomatis.")
        print("Cek manual       : jalankan ipconfig, cari IPv4 Address WiFi/hotspot.")
    print(f"Health URL       : http://127.0.0.1:{port}/api/network/health")
    print(f"Ping latency URL : http://127.0.0.1:{port}/api/latency/ping")
    print(f"Bind host        : {host}:{port}")
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
