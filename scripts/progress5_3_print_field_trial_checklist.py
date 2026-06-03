from __future__ import annotations


def main() -> int:
    print("Progress 5.3 Field Trial Checklist")
    print("Set-Location E:\\Projects\\ULP_Project")
    print(".\\venv\\Scripts\\python.exe scripts\\operator_command_center.py --diagnose")
    print(".\\venv\\Scripts\\python.exe scripts\\operator_command_center.py --print-links")
    print(".\\venv\\Scripts\\python.exe scripts\\run_remote_realtime_server.py --host 0.0.0.0 --port 5000")
    print("Terminal kedua: ngrok http 5000")
    print(".\\venv\\Scripts\\python.exe scripts\\operator_command_center.py --ngrok-probe")
    print("HP: https://<ngrok-public-url>/field-capture")
    print("HP checklist: https://<ngrok-public-url>/field-trial-checklist")
    print("HP steps: Test koneksi, Ambil GPS, Start kamera, Manual prediction, Snapshot report, Checklist submit")
    print(".\\venv\\Scripts\\python.exe scripts\\operator_command_center.py --evidence-pack")
    print(".\\venv\\Scripts\\python.exe scripts\\operator_command_center.py --progress5-3-gate")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
