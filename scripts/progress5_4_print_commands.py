from __future__ import annotations


def main() -> int:
    print("Progress 5.4 Realtime Camera Geometry Commands")
    print("Set-Location E:\\Projects\\ULP_Project")
    print(".\\venv\\Scripts\\python.exe scripts\\operator_command_center.py --camera-ui-smoke")
    print(".\\venv\\Scripts\\python.exe scripts\\operator_command_center.py --geometry-math-smoke")
    print(".\\venv\\Scripts\\python.exe scripts\\operator_command_center.py --shutter-report-smoke")
    print(".\\venv\\Scripts\\python.exe scripts\\operator_command_center.py --progress5-4-gate")
    print(".\\venv\\Scripts\\python.exe scripts\\run_remote_realtime_server.py --host 0.0.0.0 --port 5000")
    print("Tunnel: ngrok http 5000")
    print("HP: https://<ngrok-public-url>/field-capture")
    print("HP steps: Izinkan Kamera, Izinkan GPS, Mulai Deteksi, Jepret / Shutter, Buka Spreadsheet/CSV, Buka Map")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
