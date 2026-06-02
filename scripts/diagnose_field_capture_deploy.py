from __future__ import annotations

import json
import socket
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

OUTPUT_DIR = ROOT / "outputs" / "runtime"
JSON_OUT = OUTPUT_DIR / "phase9_deploy_diagnostic.json"
TXT_OUT = OUTPUT_DIR / "phase9_deploy_diagnostic.txt"


def _git(args: list[str]) -> str:
    completed = subprocess.run(["git", *args], cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    return completed.stdout.strip() if completed.returncode == 0 else completed.stderr.strip()


def _port_available(port: int = 5000, host: str = "127.0.0.1") -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.5)
        return sock.connect_ex((host, port)) != 0


def _route_checks() -> dict[str, object]:
    try:
        from ulp_project.flask_app import create_app
    except Exception as exc:  # pragma: no cover
        return {"status": "FLASK_IMPORT_FAILED", "error": str(exc), "routes": {}}
    try:
        app = create_app()
    except Exception as exc:
        return {"status": "FLASK_APP_CREATE_FAILED", "error": str(exc), "routes": {}}
    client = app.test_client()
    checks = {
        "/": client.get("/").status_code,
        "/field-capture": client.get("/field-capture").status_code,
        "/api/latency/ping": client.get("/api/latency/ping").status_code,
        "/api/field-capture/upload": client.post("/api/field-capture/upload", json={"point_id": "diagnostic"}).status_code,
        "/api/field-capture/job/<job_id>": client.get("/api/field-capture/job/diagnostic_missing").status_code,
        "/api/field-capture/result/<job_id>": client.get("/api/field-capture/result/diagnostic_missing").status_code,
    }
    return {"status": "ROUTES_CHECKED", "routes": checks}


def build_diagnostic(host: str = "0.0.0.0", port: int = 5000) -> dict[str, object]:
    flask_status = "OK"
    try:
        import flask  # noqa: F401
    except ImportError:
        flask_status = "FLASK_NOT_INSTALLED"
    return {
        "python_executable": sys.executable,
        "venv_active": "venv" in sys.executable.lower() or ".venv" in sys.executable.lower(),
        "flask_import": flask_status,
        "project_root": str(ROOT),
        "project_root_ok": (ROOT / "src" / "ulp_project").exists(),
        "git_branch": _git(["branch", "--show-current"]),
        "git_commit": _git(["rev-parse", "--short", "HEAD"]),
        "port_5000_available": _port_available(port),
        "host_binding": host,
        "port": port,
        "routes": _route_checks(),
        "operator_hint": [
            "Run server with: .\\venv\\Scripts\\python.exe scripts\\run_field_capture_server.py --host 0.0.0.0 --port 5000",
            "Open on HP: http://<IP-LAPTOP>:5000/field-capture",
            "If camera is blocked on HTTP/LAN, use file upload fallback or manual ngrok HTTPS.",
        ],
    }


def write_diagnostic(result: dict[str, object]) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    JSON_OUT.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    lines = ["Phase 9 Field Capture Deploy Diagnostic", ""]
    for key, value in result.items():
        lines.append(f"{key}: {value}")
    TXT_OUT.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    result = build_diagnostic()
    write_diagnostic(result)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    print(f"diagnostic_json: {JSON_OUT}")
    print(f"diagnostic_txt: {TXT_OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
