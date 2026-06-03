"""Progress 5.3 evidence pack and HP result intake helpers."""

from __future__ import annotations

import json
import subprocess
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from .calibration_readiness import check_calibration_readiness
from .field_trial_diagnostics import collect_field_trial_diagnostics
from .model_handoff import check_model_handoff
from .ngrok_runtime_probe import probe_ngrok_runtime
from .paths import PROJECT_ROOT
from .phase5_2_field_trial import build_manual_prediction
from .realtime_streaming import websocket_available
from .runtime_links import build_public_links
from .tunnel_diagnostics import tunnel_cli_status


EVIDENCE_DIR = PROJECT_ROOT / "data" / "runtime" / "field_trial_evidence"
HP_RESULT_BOOL_FIELDS = [
    "public_url_opened",
    "server_connection_ok",
    "camera_ok",
    "gps_ok",
    "manual_prediction_ok",
    "snapshot_report_ok",
    "map_report_ok",
]


def build_field_trial_evidence_pack(
    *,
    evidence_dir: Path = EVIDENCE_DIR,
    port: int = 5000,
    dry_run: bool = False,
) -> dict[str, Any]:
    timestamp = datetime.now().isoformat()
    manual_prediction = build_manual_prediction(
        {
            "point_id": "V001_pohon_sono",
            "species": "pohon_sono",
            "asset_type": "span",
            "clearance_m": 5.0,
            "growth_rate_m_per_day": 0.01,
            "measurement_source": "manual",
        }
    )
    ngrok = probe_ngrok_runtime(port=port)
    tunnel_cli = tunnel_cli_status()
    model = check_model_handoff()
    calibration = check_calibration_readiness({})
    hp_result = load_latest_hp_result(evidence_dir)
    diagnostics = collect_field_trial_diagnostics(port=port)
    pack = {
        "status": "FIELD_TRIAL_EVIDENCE_READY",
        "timestamp": timestamp,
        "branch": _git(["branch", "--show-current"]),
        "head": _git(["rev-parse", "--short", "HEAD"]),
        "server_local_url": f"http://127.0.0.1:{port}/field-capture",
        "lan_urls": build_public_links(port=port).get("lan_field_capture_urls", []),
        "public_tunnel_url": ngrok.get("public_https_url"),
        "field_capture_public_url": ngrok.get("field_capture_public_url"),
        "checklist_public_url": ngrok.get("checklist_public_url"),
        "ngrok_status": ngrok.get("status"),
        "ngrok": ngrok,
        "cloudflared_status": tunnel_cli.get("cloudflared"),
        "model_status": model.get("model_status"),
        "model_status_detail": model,
        "calibration_status": calibration.get("status"),
        "calibration_status_detail": calibration,
        "transport_status": websocket_available(),
        "route_health_status": diagnostics.get("local_health", {}),
        "port_diagnostic": diagnostics.get("port", {}),
        "windows_firewall_status": diagnostics.get("windows_firewall", {}),
        "manual_prediction_smoke_status": manual_prediction.get("status"),
        "manual_prediction_eta_days": manual_prediction.get("eta_days"),
        "snapshot_report_smoke_status": "SNAPSHOT_REPORT_ENDPOINT_READY_FIELD_TRIGGER_REQUIRED",
        "map_policy_status": "NO_GPS_NO_MARKER_POLICY_READY",
        "hp_physical_confirmation_status": hp_result.get("hp_physical_confirmation_status"),
        "latest_hp_result": hp_result,
        "known_blockers": _known_blockers(ngrok, model, calibration, hp_result, diagnostics),
        "next_operator_command": ".\\venv\\Scripts\\python.exe scripts\\operator_command_center.py --ngrok-probe",
        "no_fake_detection": True,
        "no_label_touch": True,
        "token_policy": "TOKENS_AND_RUNTIME_TUNNEL_URLS_NOT_WRITTEN_TO_GIT",
        "output_policy": "Evidence output is runtime-only under data/runtime/field_trial_evidence and must not be committed.",
    }
    if not dry_run:
        written = write_evidence_pack(pack, evidence_dir=evidence_dir)
        pack["evidence_json_path"] = str(written["json_path"])
        pack["evidence_markdown_path"] = str(written["markdown_path"])
        pack["evidence_written"] = True
    else:
        pack["evidence_written"] = False
        pack["dry_run"] = True
    return pack


def write_evidence_pack(pack: dict[str, Any], *, evidence_dir: Path = EVIDENCE_DIR) -> dict[str, Path]:
    evidence_dir.mkdir(parents=True, exist_ok=True)
    suffix = datetime.now().strftime("%Y%m%d_%H%M%S")
    json_path = evidence_dir / f"field_trial_evidence_{suffix}.json"
    markdown_path = evidence_dir / f"field_trial_evidence_{suffix}.md"
    json_path.write_text(json.dumps(_redact_runtime_secrets(pack), indent=2, ensure_ascii=False), encoding="utf-8")
    markdown_path.write_text(_render_evidence_markdown(pack), encoding="utf-8")
    return {"json_path": json_path, "markdown_path": markdown_path}


def record_hp_result(payload: dict[str, Any], *, evidence_dir: Path = EVIDENCE_DIR) -> dict[str, Any]:
    evidence_dir.mkdir(parents=True, exist_ok=True)
    sanitized = sanitize_hp_result(payload)
    status = _hp_confirmation_status(sanitized)
    sanitized.update(
        {
            "status": "HP_RESULT_RECORDED",
            "hp_physical_confirmation_status": status,
            "timestamp": datetime.now().isoformat(),
            "no_screenshot_stored": True,
        }
    )
    path = evidence_dir / f"hp_result_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}.json"
    path.write_text(json.dumps(sanitized, indent=2, ensure_ascii=False), encoding="utf-8")
    return {**sanitized, "path": str(path)}


def sanitize_hp_result(payload: dict[str, Any]) -> dict[str, Any]:
    allowed = {
        "operator_name",
        "device_name",
        "browser_name",
        "network_type",
        "error_code",
        "notes",
        *HP_RESULT_BOOL_FIELDS,
    }
    result: dict[str, Any] = {}
    for key in allowed:
        if key not in payload:
            continue
        if key in HP_RESULT_BOOL_FIELDS:
            result[key] = _to_bool(payload.get(key))
        else:
            result[key] = _safe_text(payload.get(key))
    if result.get("network_type") not in {"wifi", "paket_data", "unknown"}:
        result["network_type"] = "unknown"
    return result


def load_latest_hp_result(evidence_dir: Path = EVIDENCE_DIR) -> dict[str, Any]:
    if not evidence_dir.exists():
        return {"hp_physical_confirmation_status": "HP_PHYSICAL_TEST_PENDING_USER_CONFIRMATION", "status": "NO_HP_RESULT_RECORDED"}
    candidates = sorted(evidence_dir.glob("hp_result_*.json"), key=lambda path: path.stat().st_mtime, reverse=True)
    if not candidates:
        return {"hp_physical_confirmation_status": "HP_PHYSICAL_TEST_PENDING_USER_CONFIRMATION", "status": "NO_HP_RESULT_RECORDED"}
    try:
        payload = json.loads(candidates[0].read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {"hp_physical_confirmation_status": "HP_RESULT_UNREADABLE", "status": "HP_RESULT_UNREADABLE"}
    payload["path"] = str(candidates[0])
    return payload


def _known_blockers(
    ngrok: dict[str, Any],
    model: dict[str, Any],
    calibration: dict[str, Any],
    hp_result: dict[str, Any],
    diagnostics: dict[str, Any],
) -> list[str]:
    blockers: list[str] = []
    if ngrok.get("status") != "NGROK_HTTPS_TUNNEL_READY":
        blockers.append("PUBLIC_TUNNEL_NOT_RUNNING")
    if model.get("model_status") == "MODEL_NOT_READY":
        blockers.append("MODEL_NOT_READY_EXPECTED")
    if calibration.get("status") != "CALIBRATION_READY":
        blockers.append("CALIBRATION_NOT_READY_EXPECTED")
    if diagnostics.get("local_health", {}).get("status") != "LOCAL_SERVER_HEALTH_OK":
        blockers.append("LOCAL_SERVER_NOT_RUNNING")
    if hp_result.get("hp_physical_confirmation_status") != "HP_CONFIRMED":
        blockers.append("HP_PHYSICAL_TEST_PENDING_USER_CONFIRMATION")
    return blockers


def _hp_confirmation_status(payload: dict[str, Any]) -> str:
    required = ["public_url_opened", "server_connection_ok", "manual_prediction_ok", "snapshot_report_ok"]
    if all(payload.get(key) is True for key in required):
        return "HP_CONFIRMED"
    return "HP_PHYSICAL_TEST_PENDING_USER_CONFIRMATION"


def _render_evidence_markdown(pack: dict[str, Any]) -> str:
    lines = [
        "# Progress 5.3 Field Trial Evidence Pack",
        "",
        f"- status: {pack.get('status')}",
        f"- timestamp: {pack.get('timestamp')}",
        f"- branch: {pack.get('branch')}",
        f"- head: {pack.get('head')}",
        f"- local_url: {pack.get('server_local_url')}",
        f"- public_tunnel_url: {pack.get('public_tunnel_url') or 'PUBLIC_TUNNEL_NOT_RUNNING'}",
        f"- ngrok_status: {pack.get('ngrok_status')}",
        f"- model_status: {pack.get('model_status')}",
        f"- calibration_status: {pack.get('calibration_status')}",
        f"- hp_physical_confirmation_status: {pack.get('hp_physical_confirmation_status')}",
        f"- known_blockers: {', '.join(pack.get('known_blockers', []))}",
        "",
        "Next command:",
        "",
        f"    {pack.get('next_operator_command')}",
        "",
        "No photo, video, base64 image, token, or credential is stored in this evidence pack.",
    ]
    return "\n".join(lines)


def _redact_runtime_secrets(payload: Any) -> Any:
    if isinstance(payload, dict):
        redacted: dict[str, Any] = {}
        for key, value in payload.items():
            lowered = str(key).lower()
            if any(marker in lowered for marker in ("token", "secret", "credential", "authtoken", "api_key", "base64")):
                redacted[key] = "REDACTED_RUNTIME_ONLY_POLICY"
            else:
                redacted[key] = _redact_runtime_secrets(value)
        return redacted
    if isinstance(payload, list):
        return [_redact_runtime_secrets(item) for item in payload]
    return payload


def _git(args: list[str]) -> str:
    completed = subprocess.run(["git", *args], cwd=PROJECT_ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    return completed.stdout.strip() if completed.returncode == 0 else completed.stderr.strip()[:180]


def _to_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    lowered = str(value).strip().lower()
    return lowered in {"true", "1", "yes", "ya", "ok", "on"}


def _safe_text(value: Any) -> str:
    text = "" if value is None else str(value)
    return text.replace("\x00", "").strip()[:500]
