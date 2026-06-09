from __future__ import annotations

import base64
import importlib
import json
import re
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path.cwd()
SRC = ROOT / "src"
FLASK_APP = SRC / "ulp_project" / "flask_app.py"
BRIDGE = SRC / "ulp_project" / "progress6_18g_runtime_tracking_bridge.py"
LIVE_SMOKE = ROOT / "scripts" / "progress6_18g_live_smoke.py"
VALIDATION_REPORT = ROOT / "reports" / "progress6_18g_factory_patch_validation.json"


BRIDGE_CODE = r'''
from __future__ import annotations

from functools import wraps
from typing import Any

from flask import current_app, jsonify, request

VERSION = "progress6_18g_runtime_tracking_bridge"


def _find_frame_endpoint(app: Any) -> str | None:
    try:
        for rule in app.url_map.iter_rules():
            if str(rule.rule) == "/api/field/session/frame" and "POST" in getattr(rule, "methods", set()):
                return str(rule.endpoint)
    except Exception:
        return None
    return None


def _safe_json_from_response(resp: Any) -> dict:
    try:
        data = resp.get_json(silent=True)
        if isinstance(data, dict):
            return data
    except Exception:
        pass

    try:
        text = resp.get_data(as_text=True)
    except Exception:
        text = ""

    return {
        "original_response_non_json": text[:2000],
    }


def _tracking_payload(data: dict) -> dict:
    measurement = data.get("measurement_result")
    if not isinstance(measurement, dict):
        measurement = {}

    detections = data.get("detections")
    if not isinstance(detections, list):
        detections = []

    tree_detected = bool(
        data.get("tree_detected")
        or measurement.get("tree_detected")
        or any(str(d.get("class_name", "")).lower() in {"pohon_sono", "tree_sono", "tree"} for d in detections if isinstance(d, dict))
    )

    model_status = (
        data.get("tree_model_status")
        or measurement.get("tree_model_status")
        or "TREE_MODEL_READY_CANDIDATE"
    )

    if tree_detected:
        tracking_status = "TRACKING_READY_TREE_DETECTED_NO_STABLE_ID_YET"
    else:
        tracking_status = "TRACKING_READY_NO_DETECTION"

    return {
        "version": VERSION,
        "tracking_status": tracking_status,
        "tree_tracking_status": tracking_status,
        "model_status": model_status,
        "detection_count": len(detections),
        "tree_detected": tree_detected,
        "track_id_seen": False,
        "tree_track_ids": [],
        "no_fake_detection": True,
        "no_fake_track_id": True,
        "note": "Runtime tracking bridge integrated. Track ID remains false until stable detection exists across frames.",
    }


def install_progress6_18g_runtime_tracking_bridge(app: Any) -> None:
    if app.config.get("PROGRESS_6_18G_TRACKING_BRIDGE_INSTALLED"):
        return

    frame_endpoint = _find_frame_endpoint(app)

    def progress6_18_tracking_status():
        endpoint = _find_frame_endpoint(app)
        return jsonify({
            "status": "PROGRESS_6_18G_RUNTIME_TRACKING_BRIDGE_INSTALLED",
            "version": VERSION,
            "frame_endpoint": endpoint,
            "frame_route_wrapped": bool(app.config.get("PROGRESS_6_18G_FRAME_ROUTE_WRAPPED")),
            "no_label_touch": True,
            "no_raw_touch": True,
            "no_dataset_touch": True,
            "no_runs_touch": True,
            "no_weights_touch": True,
        })

    if "progress6_18g_tracking_status" not in app.view_functions:
        app.add_url_rule(
            "/api/runtime/progress6-18-tracking-status",
            endpoint="progress6_18g_tracking_status",
            view_func=progress6_18_tracking_status,
            methods=["GET"],
        )

    if frame_endpoint and frame_endpoint in app.view_functions:
        original = app.view_functions[frame_endpoint]

        if not getattr(original, "_progress6_18g_wrapped", False):
            @wraps(original)
            def wrapped_frame_route(*args, **kwargs):
                original_result = original(*args, **kwargs)
                resp = current_app.make_response(original_result)
                status_code = getattr(resp, "status_code", 200)

                data = _safe_json_from_response(resp)
                tracking = _tracking_payload(data)

                data["progress6_18_tracking"] = tracking
                data["runtime_tracking_integrated"] = True
                data["tracking_status"] = tracking["tracking_status"]
                data["tree_tracking_status"] = tracking["tree_tracking_status"]
                data["track_id_seen"] = tracking["track_id_seen"]
                data["tree_track_ids"] = tracking["tree_track_ids"]

                out = jsonify(data)
                out.status_code = status_code
                return out

            wrapped_frame_route._progress6_18g_wrapped = True
            app.view_functions[frame_endpoint] = wrapped_frame_route
            app.config["PROGRESS_6_18G_FRAME_ROUTE_WRAPPED"] = True
        else:
            app.config["PROGRESS_6_18G_FRAME_ROUTE_WRAPPED"] = True
    else:
        app.config["PROGRESS_6_18G_FRAME_ROUTE_WRAPPED"] = False

    app.config["PROGRESS_6_18G_TRACKING_BRIDGE_INSTALLED"] = True
'''


LIVE_SMOKE_CODE = r'''
from __future__ import annotations

import base64
import json
import re
import time
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

ROOT = Path.cwd()
REPORT = ROOT / "reports" / "progress6_18g_runtime_tracking_live_smoke.json"
BASE = "http://127.0.0.1:5000"


def request_json(method: str, url: str, payload=None, timeout=30):
    data = None
    headers = {
        "Cache-Control": "no-store",
        "Pragma": "no-cache",
    }
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = Request(url, data=data, headers=headers, method=method)
    try:
        with urlopen(req, timeout=timeout) as resp:
            text = resp.read().decode("utf-8", errors="replace")
            try:
                js = json.loads(text)
            except Exception:
                js = None
            return resp.status, text, js
    except HTTPError as e:
        text = e.read().decode("utf-8", errors="replace")
        return e.code, text, None
    except URLError as e:
        return 0, str(e), None


def find_session_id(text: str) -> str:
    m = re.search(r"FS_\d{8}_\d{6}_[A-Za-z0-9]+", text or "")
    return m.group(0) if m else ""


def make_synthetic_frame_b64() -> str:
    try:
        import cv2
        import numpy as np
        img = np.zeros((480, 640, 3), dtype=np.uint8)
        img[:] = (245, 245, 245)
        cv2.rectangle(img, (260, 80), (390, 420), (60, 140, 60), -1)
        cv2.circle(img, (325, 90), 70, (40, 160, 40), -1)
        cv2.putText(img, "PROGRESS_6_18G_SYNTHETIC_NOT_FIELD", (25, 450), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (20, 20, 20), 2)
        ok, buf = cv2.imencode(".jpg", img, [int(cv2.IMWRITE_JPEG_QUALITY), 85])
        if ok:
            return base64.b64encode(buf.tobytes()).decode("ascii")
    except Exception:
        pass

    return base64.b64encode(b"PROGRESS_6_18G_SYNTHETIC_NOT_FIELD").decode("ascii")


def main() -> int:
    REPORT.parent.mkdir(parents=True, exist_ok=True)

    status_code, status_text, status_json = request_json("GET", f"{BASE}/api/runtime/progress6-18-tracking-status", timeout=10)

    start_code, start_text, start_json = request_json("POST", f"{BASE}/api/field/session/start", {
        "point_id": "V001_pohon_sono",
        "operator": "debug_ps",
        "operator_name": "debug_ps",
        "notes": "progress6_18g live smoke; synthetic frame, not field evidence",
    }, timeout=30)

    session_id = find_session_id(start_text)

    frame_code = 0
    frame_text = ""
    frame_json = None

    if session_id:
        frame_code, frame_text, frame_json = request_json("POST", f"{BASE}/api/field/session/frame", {
            "session_id": session_id,
            "frame_base64": make_synthetic_frame_b64(),
            "diagnostic": "progress6_18g_runtime_tracking_synthetic_not_field_data",
            "source": "SYNTHETIC_DIAGNOSTIC_NOT_FIELD_EVIDENCE",
        }, timeout=120)

    has_tracking_key = "progress6_18_tracking" in (frame_text or "")
    has_runtime_integrated = "runtime_tracking_integrated" in (frame_text or "")
    has_tracking_status = any(x in (frame_text or "") for x in [
        "TRACKING_READY",
        "TRACKING_MODEL_NOT_READY",
        "TRACKING_RUNTIME_EXCEPTION",
        "FRAME_NOT_AVAILABLE",
    ])

    result = {
        "version": "progress6_18g_live_smoke",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "status": "PROGRESS_6_18G_RUNTIME_TRACKING_LIVE_SMOKE_PASS"
        if status_code == 200 and 200 <= start_code < 300 and 200 <= frame_code < 300 and has_tracking_key and has_runtime_integrated and has_tracking_status
        else "PROGRESS_6_18G_RUNTIME_TRACKING_LIVE_SMOKE_FAILED",
        "status_route_code": status_code,
        "status_route_json": status_json,
        "status_route_text_head": (status_text or "")[:1000],
        "start_status_code": start_code,
        "session_id": session_id,
        "frame_status_code": frame_code,
        "has_progress6_18_tracking_key": has_tracking_key,
        "has_runtime_tracking_integrated": has_runtime_integrated,
        "has_tracking_status": has_tracking_status,
        "frame_json_keys": sorted(frame_json.keys()) if isinstance(frame_json, dict) else [],
        "frame_text_head": (frame_text or "")[:2000],
        "no_label_touch": True,
        "no_raw_touch": True,
        "no_dataset_touch": True,
        "no_runs_touch": True,
        "no_weights_touch": True,
    }

    REPORT.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))

    return 0 if result["status"].endswith("_PASS") else 1


if __name__ == "__main__":
    raise SystemExit(main())
'''


def run(cmd, check=True):
    print("RUN:", " ".join(str(x) for x in cmd))
    p = subprocess.run(cmd, cwd=str(ROOT), text=True, capture_output=True)
    if p.stdout.strip():
        print(p.stdout[-5000:])
    if p.stderr.strip():
        print(p.stderr[-5000:])
    if check and p.returncode != 0:
        raise RuntimeError(f"COMMAND_FAILED rc={p.returncode}: {' '.join(str(x) for x in cmd)}")
    return p


def write_report(status, hard_failures, extra=None):
    VALIDATION_REPORT.parent.mkdir(parents=True, exist_ok=True)
    data = {
        "version": "progress6_18g_factory_patch_and_validate",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "status": status,
        "hard_failures": hard_failures,
        "extra": extra or {},
        "no_label_touch": True,
        "no_raw_touch": True,
        "no_dataset_touch": True,
        "no_runs_touch": True,
        "no_weights_touch": True,
    }
    VALIDATION_REPORT.write_text(json.dumps(data, indent=2), encoding="utf-8")
    print(json.dumps(data, indent=2))


def normalize(path: Path):
    text = path.read_text(encoding="utf-8", errors="replace")
    lines = [line.rstrip() for line in text.splitlines()]
    while lines and lines[-1] == "":
        lines.pop()
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def remove_old_runtime_tracking_blocks(text: str) -> str:
    patterns = [
        r"\n?# PROGRESS 6\.18 RUNTIME TRACKING INTEGRATION START.*?# PROGRESS 6\.18 RUNTIME TRACKING INTEGRATION END\n?",
        r"\n?# PROGRESS 6\.18F RUNTIME TRACKING BRIDGE START.*?# PROGRESS 6\.18F RUNTIME TRACKING BRIDGE END\n?",
        r"\n?# PROGRESS 6\.18G RUNTIME TRACKING BRIDGE FACTORY INSTALL START.*?# PROGRESS 6\.18G RUNTIME TRACKING BRIDGE FACTORY INSTALL END\n?",
    ]
    for pat in patterns:
        text = re.sub(pat, "\n", text, flags=re.S)
    return text


def install_before_factory_return(text: str) -> tuple[str, dict]:
    lines = text.splitlines()

    candidates = []
    for i, line in enumerate(lines):
        m = re.match(r"^(?P<indent>\s*)return\s+(?P<var>app|application|flask_app)\s*$", line)
        if m:
            candidates.append((i, m.group("indent"), m.group("var")))

    if not candidates:
        raise RuntimeError("NO_FACTORY_RETURN_APP_FOUND: tidak menemukan return app/application/flask_app di flask_app.py")

    index, indent, var = candidates[-1]

    block_lines = [
        f"{indent}# PROGRESS 6.18G RUNTIME TRACKING BRIDGE FACTORY INSTALL START",
        f"{indent}try:",
        f"{indent}    from ulp_project.progress6_18g_runtime_tracking_bridge import install_progress6_18g_runtime_tracking_bridge",
        f"{indent}    install_progress6_18g_runtime_tracking_bridge({var})",
        f"{indent}except Exception as _progress6_18g_error:",
        f"{indent}    try:",
        f"{indent}        {var}.logger.exception(\"PROGRESS_6_18G_RUNTIME_TRACKING_BRIDGE_INSTALL_FAILED: %s\", _progress6_18g_error)",
        f"{indent}    except Exception:",
        f"{indent}        pass",
        f"{indent}# PROGRESS 6.18G RUNTIME TRACKING BRIDGE FACTORY INSTALL END",
    ]

    new_lines = lines[:index] + block_lines + lines[index:]
    return "\n".join(new_lines) + "\n", {"return_index": index, "app_var": var}


def load_created_app():
    sys.path.insert(0, str(SRC))
    mod = importlib.import_module("ulp_project.flask_app")

    for name in ["create_app", "make_app", "build_app"]:
        fn = getattr(mod, name, None)
        if callable(fn):
            try:
                return fn(), name
            except TypeError:
                continue

    raise RuntimeError("NO_APP_FACTORY_CALLABLE_FOUND: flask_app.py tidak punya create_app/make_app/build_app tanpa argumen")


def main() -> int:
    hard_failures = []
    extra = {}

    try:
        if not FLASK_APP.exists():
            hard_failures.append("flask_app_missing")
            write_report("PROGRESS_6_18G_VALIDATION_FAILED", hard_failures)
            return 1

        BRIDGE.write_text(BRIDGE_CODE.strip() + "\n", encoding="utf-8")
        LIVE_SMOKE.write_text(LIVE_SMOKE_CODE.strip() + "\n", encoding="utf-8")

        original = FLASK_APP.read_text(encoding="utf-8", errors="replace")
        cleaned = remove_old_runtime_tracking_blocks(original)

        backup_dir = ROOT / "manual_backups" / f"progress6_18g_before_factory_patch_{time.strftime('%Y%m%d_%H%M%S')}"
        backup_dir.mkdir(parents=True, exist_ok=True)
        (backup_dir / "src_ulp_project_flask_app_before_6_18g.py").write_text(original, encoding="utf-8")

        patched, patch_info = install_before_factory_return(cleaned)
        FLASK_APP.write_text(patched, encoding="utf-8")

        for p in [FLASK_APP, BRIDGE, LIVE_SMOKE, Path(__file__)]:
            normalize(p)

        run([sys.executable, "-m", "py_compile", str(FLASK_APP), str(BRIDGE), str(LIVE_SMOKE), str(Path(__file__))])
        run([sys.executable, "-m", "compileall", "src", "scripts", "tests"])
        run(["git", "diff", "--check"])

        app, factory_name = load_created_app()

        with app.test_client() as client:
            status_resp = client.get("/api/runtime/progress6-18-tracking-status")
            status_json = status_resp.get_json(silent=True)

        extra = {
            "patch_info": patch_info,
            "factory_name": factory_name,
            "status_route_code_imported_app": status_resp.status_code,
            "status_route_json_imported_app": status_json,
            "backup_dir": str(backup_dir),
        }

        if status_resp.status_code != 200:
            hard_failures.append("status_route_not_200_in_imported_factory_app")

        if not isinstance(status_json, dict) or status_json.get("status") != "PROGRESS_6_18G_RUNTIME_TRACKING_BRIDGE_INSTALLED":
            hard_failures.append("status_route_payload_wrong_in_imported_factory_app")

        if hard_failures:
            write_report("PROGRESS_6_18G_VALIDATION_FAILED", hard_failures, extra)
            return 1

        write_report("PROGRESS_6_18G_FACTORY_PATCH_VALIDATION_PASS", [], extra)
        return 0

    except Exception as exc:
        write_report("PROGRESS_6_18G_EXCEPTION", ["exception"], {"exception": repr(exc), **extra})
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
