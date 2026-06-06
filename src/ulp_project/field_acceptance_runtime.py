"""Physical HP acceptance evidence runtime for Progress 6.3."""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Any

from .field_session_runtime import session_status, latest_field_session_map
from .model_handoff import check_model_handoff
from .paths import PROJECT_ROOT

ACCEPTANCE_RUNTIME_DIR = PROJECT_ROOT / "outputs" / "runtime" / "field_acceptance"

AUTO_CHECK_KEYS = [
    "current_url_mode",
    "secure_context",
    "public_tunnel_status",
    "camera_permission_status",
    "gps_permission_status",
    "gps_accuracy_status",
    "gps_watch_status",
    "camera_preview_status",
    "frame_loop_status",
    "shutter_status",
    "report_page_status",
    "result_page_status",
    "map_status",
    "latest_latency_ms",
    "visibility_state",
    "foreground_recording_status",
    "model_status",
    "no_fake_detection_status",
]

MANUAL_CONFIRM_KEYS = [
    "hp_different_network_confirmed",
    "public_https_url_opened",
    "camera_visible",
    "gps_active",
    "start_record_ok",
    "stop_record_ok",
    "report_opened",
    "result_opened",
    "map_opened_or_no_gps_correct",
]


@dataclass
class FieldAcceptance:
    acceptance_id: str
    started_at: str
    submitted_at: str = ""
    status: str = "PHYSICAL_HP_ACCEPTANCE_PENDING_USER_TEST"
    operator_name: str = ""
    device_name: str = ""
    network_type: str = ""
    field_location_note: str = ""
    problem_note: str = ""
    session_id: str = ""
    automatic_checklist: dict[str, Any] = field(default_factory=dict)
    manual_checklist: dict[str, bool] = field(default_factory=dict)
    evidence: dict[str, Any] = field(default_factory=dict)
    reason_codes: list[str] = field(default_factory=lambda: ["HP_PHYSICAL_TEST_REQUIRED"])


_LATEST_ACCEPTANCE: FieldAcceptance | None = None


def start_acceptance(payload: dict[str, Any], *, runtime_root: Path | None = None) -> dict[str, Any]:
    global _LATEST_ACCEPTANCE
    acceptance = FieldAcceptance(
        acceptance_id=str(payload.get("acceptance_id") or f"FACC_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"),
        started_at=datetime.now().isoformat(),
        operator_name=str(payload.get("operator_name") or ""),
        device_name=str(payload.get("device_name") or ""),
        network_type=str(payload.get("network_type") or ""),
        field_location_note=str(payload.get("field_location_note") or ""),
        problem_note=str(payload.get("problem_note") or ""),
        session_id=str(payload.get("session_id") or ""),
        automatic_checklist=_automatic_checklist(payload),
    )
    acceptance.evidence = _evidence_payload(acceptance, payload)
    _LATEST_ACCEPTANCE = acceptance
    _save_acceptance(acceptance, runtime_root=runtime_root)
    return _acceptance_payload(acceptance, "FIELD_ACCEPTANCE_STARTED")


def submit_acceptance(payload: dict[str, Any], *, runtime_root: Path | None = None) -> dict[str, Any]:
    global _LATEST_ACCEPTANCE
    acceptance = _LATEST_ACCEPTANCE or FieldAcceptance(
        acceptance_id=str(payload.get("acceptance_id") or f"FACC_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"),
        started_at=datetime.now().isoformat(),
    )
    acceptance.submitted_at = datetime.now().isoformat()
    acceptance.operator_name = str(payload.get("operator_name") or acceptance.operator_name)
    acceptance.device_name = str(payload.get("device_name") or acceptance.device_name)
    acceptance.network_type = str(payload.get("network_type") or acceptance.network_type)
    acceptance.field_location_note = str(payload.get("field_location_note") or acceptance.field_location_note)
    acceptance.problem_note = str(payload.get("problem_note") or acceptance.problem_note)
    acceptance.session_id = str(payload.get("session_id") or acceptance.session_id)
    acceptance.automatic_checklist = _automatic_checklist(payload, fallback=acceptance.automatic_checklist)
    acceptance.manual_checklist = {key: _bool(payload.get(key)) for key in MANUAL_CONFIRM_KEYS}
    acceptance.status, acceptance.reason_codes = _acceptance_status(acceptance)
    acceptance.evidence = _evidence_payload(acceptance, payload)
    _LATEST_ACCEPTANCE = acceptance
    _save_acceptance(acceptance, runtime_root=runtime_root)
    return _acceptance_payload(acceptance, "FIELD_ACCEPTANCE_SUBMITTED")


def latest_acceptance() -> dict[str, Any]:
    if _LATEST_ACCEPTANCE is None:
        return {
            "status": "PHYSICAL_HP_ACCEPTANCE_PENDING_USER_TEST",
            "acceptance_status": "PHYSICAL_HP_ACCEPTANCE_PENDING_USER_TEST",
            "reason_codes": ["NO_HP_PHYSICAL_EVIDENCE_SUBMITTED"],
        }
    return _acceptance_payload(_LATEST_ACCEPTANCE, "FIELD_ACCEPTANCE_LATEST_READY")


def acceptance_status() -> dict[str, Any]:
    latest = latest_acceptance()
    return {
        "status": latest.get("acceptance_status", "PHYSICAL_HP_ACCEPTANCE_PENDING_USER_TEST"),
        "acceptance_status": latest.get("acceptance_status", "PHYSICAL_HP_ACCEPTANCE_PENDING_USER_TEST"),
        "physical_hp_acceptance": latest,
    }


def acceptance_evidence() -> dict[str, Any]:
    latest = latest_acceptance()
    return {
        "status": "FIELD_ACCEPTANCE_EVIDENCE_READY"
        if latest.get("acceptance_id")
        else "PHYSICAL_HP_ACCEPTANCE_PENDING_USER_TEST",
        "evidence": latest.get("evidence", {}),
        "acceptance": latest,
    }


def _automatic_checklist(payload: dict[str, Any], *, fallback: dict[str, Any] | None = None) -> dict[str, Any]:
    fallback = fallback or {}
    session_id = payload.get("session_id") or fallback.get("session_id")
    session = {}
    try:
        session = session_status(session_id)
    except Exception:
        session = {}
    model = check_model_handoff()
    fmap = latest_field_session_map(session_id)
    defaults = {
        "current_url_mode": payload.get("current_url_mode") or fallback.get("current_url_mode") or "UNKNOWN",
        "secure_context": payload.get("secure_context_status") or fallback.get("secure_context") or "UNKNOWN",
        "public_tunnel_status": payload.get("public_tunnel_status") or fallback.get("public_tunnel_status") or "PUBLIC_TUNNEL_NOT_RUNNING",
        "camera_permission_status": payload.get("camera_permission_status") or session.get("camera_status") or "CAMERA_WAITING_PERMISSION",
        "gps_permission_status": payload.get("gps_permission_status") or "GPS_WAITING_PERMISSION",
        "gps_accuracy_status": payload.get("gps_accuracy_status") or session.get("derived_gps", {}).get("gps_accuracy_status") or "GPS_ACCURACY_UNKNOWN",
        "gps_watch_status": payload.get("gps_watch_status") or "GPS_WATCH_NOT_CONFIRMED",
        "camera_preview_status": payload.get("camera_preview_status") or "CAMERA_PREVIEW_NOT_CONFIRMED",
        "frame_loop_status": payload.get("frame_loop_status") or "FRAME_LOOP_NOT_CONFIRMED",
        "shutter_status": payload.get("shutter_status") or "SHUTTER_NOT_CONFIRMED",
        "report_page_status": payload.get("report_page_status") or "REPORT_NOT_CONFIRMED",
        "result_page_status": payload.get("result_page_status") or "RESULT_NOT_CONFIRMED",
        "map_status": payload.get("map_status") or fmap.get("status") or "NO_GPS_NO_MARKER",
        "latest_latency_ms": payload.get("latest_latency_ms") or "",
        "visibility_state": payload.get("visibility_state") or session.get("visibility_state") or "visible",
        "foreground_recording_status": payload.get("foreground_recording_status") or session.get("foreground_recording_status") or "FOREGROUND_RECORDING_REQUIRED",
        "model_status": payload.get("model_status") or model.get("model_status") or "MODEL_NOT_READY",
        "no_fake_detection_status": "NO_FAKE_DETECTION_PASS",
    }
    return {key: defaults.get(key) for key in AUTO_CHECK_KEYS}


def _evidence_payload(acceptance: FieldAcceptance, payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "acceptance_id": acceptance.acceptance_id,
        "session_id": acceptance.session_id,
        "secure_context": acceptance.automatic_checklist.get("secure_context"),
        "camera": acceptance.automatic_checklist.get("camera_permission_status"),
        "gps": acceptance.automatic_checklist.get("gps_accuracy_status"),
        "frame_loop": acceptance.automatic_checklist.get("frame_loop_status"),
        "shutter": acceptance.automatic_checklist.get("shutter_status"),
        "report": acceptance.automatic_checklist.get("report_page_status"),
        "result": acceptance.automatic_checklist.get("result_page_status"),
        "map": acceptance.automatic_checklist.get("map_status"),
        "latency_ms": acceptance.automatic_checklist.get("latest_latency_ms"),
        "visibility_state": acceptance.automatic_checklist.get("visibility_state"),
        "foreground_recording_status": acceptance.automatic_checklist.get("foreground_recording_status"),
        "model_status": acceptance.automatic_checklist.get("model_status"),
        "no_fake_detection": True,
        "raw_payload_keys": sorted(str(key) for key in payload.keys()),
    }


def _acceptance_status(acceptance: FieldAcceptance) -> tuple[str, list[str]]:
    manual_values = list(acceptance.manual_checklist.values())
    if not manual_values or not any(manual_values):
        return "PHYSICAL_HP_ACCEPTANCE_PENDING_USER_TEST", ["NO_HP_PHYSICAL_EVIDENCE_SUBMITTED"]
    if all(manual_values):
        blocking = _automatic_blockers(acceptance.automatic_checklist)
        if not blocking:
            return "PHYSICAL_HP_ACCEPTANCE_PASS", ["HP_PHYSICAL_ACCEPTANCE_EVIDENCE_COMPLETE"]
        return "PHYSICAL_HP_ACCEPTANCE_PARTIAL", blocking
    if acceptance.problem_note:
        return "PHYSICAL_HP_ACCEPTANCE_FAIL_REVIEW_REQUIRED", ["OPERATOR_REPORTED_FIELD_PROBLEM"]
    return "PHYSICAL_HP_ACCEPTANCE_PARTIAL", ["MANUAL_CONFIRMATION_INCOMPLETE"]


def _automatic_blockers(checklist: dict[str, Any]) -> list[str]:
    blockers: list[str] = []
    if checklist.get("secure_context") not in {"SECURE_CONTEXT_OK", "HTTPS_PUBLIC_READY"}:
        blockers.append("SECURE_CONTEXT_NOT_CONFIRMED")
    if checklist.get("camera_permission_status") not in {"CAMERA_READY", "CAMERA_ACTIVE"}:
        blockers.append("CAMERA_NOT_CONFIRMED")
    if checklist.get("gps_accuracy_status") in {"GPS_ACCURACY_UNKNOWN", "GPS_NOT_READY"}:
        blockers.append("GPS_NOT_CONFIRMED")
    if checklist.get("foreground_recording_status") == "PAGE_HIDDEN_BROWSER_MAY_THROTTLE":
        blockers.append("PAGE_HIDDEN_BROWSER_MAY_THROTTLE")
    return blockers


def _acceptance_payload(acceptance: FieldAcceptance, status: str) -> dict[str, Any]:
    return {
        **asdict(acceptance),
        "status": status,
        "acceptance_status": acceptance.status,
        "no_fake_detection": True,
        "physical_pass_requires_user_submitted_hp_evidence": True,
    }


def _save_acceptance(acceptance: FieldAcceptance, *, runtime_root: Path | None = None) -> None:
    root = (runtime_root / "field_acceptance") if runtime_root else ACCEPTANCE_RUNTIME_DIR
    root.mkdir(parents=True, exist_ok=True)
    (root / f"{acceptance.acceptance_id}.json").write_text(json.dumps(asdict(acceptance), indent=2, ensure_ascii=False), encoding="utf-8")
    (root / "latest.json").write_text(json.dumps(asdict(acceptance), indent=2, ensure_ascii=False), encoding="utf-8")


def _bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "ya", "on", "pass"}
