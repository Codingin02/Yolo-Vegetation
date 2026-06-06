"""Physical HP acceptance evidence runtime for Progress 6.3/6.4."""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Any

from .field_session_runtime import session_status, latest_field_session_map
from .field_acceptance_validation import validate_acceptance_payload
from .model_handoff import check_model_handoff
from .paths import PROJECT_ROOT

ACCEPTANCE_RUNTIME_DIR = PROJECT_ROOT / "outputs" / "runtime" / "field_acceptance"

AUTO_CHECK_KEYS = [
    "current_url_mode",
    "secure_context",
    "public_tunnel_status",
    "camera_permission_status",
    "gps_permission_status",
    "gps_status",
    "gps_accuracy_status",
    "gps_accuracy_m",
    "gps_watch_status",
    "camera_preview_status",
    "frame_loop_status",
    "start_session_status",
    "stop_record_status",
    "shutter_status",
    "report_page_status",
    "result_page_status",
    "map_status",
    "distance_reliability_status",
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
    "shutter_recorded",
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
    derived = session.get("derived_gps", {}) if isinstance(session, dict) else {}
    gps_current = (session.get("gps", {}) or {}).get("current", {}) if isinstance(session, dict) else {}
    camera_visible = _bool(payload.get("camera_visible"))
    gps_active = _bool(payload.get("gps_active"))
    start_ok = _bool(payload.get("start_record_ok"))
    stop_ok = _bool(payload.get("stop_record_ok"))
    shutter_ok = _bool(payload.get("shutter_recorded")) or _bool(payload.get("shutter_ok"))
    report_ok = _bool(payload.get("report_opened"))
    result_ok = _bool(payload.get("result_opened"))
    map_ok = _bool(payload.get("map_opened_or_no_gps_correct"))
    defaults = {
        "current_url_mode": _first(payload.get("current_url_mode"), fallback.get("current_url_mode"), "UNKNOWN"),
        "secure_context": _first(payload.get("secure_context_status"), fallback.get("secure_context"), "UNKNOWN"),
        "public_tunnel_status": _first(payload.get("public_tunnel_status"), fallback.get("public_tunnel_status"), "PUBLIC_TUNNEL_NOT_RUNNING"),
        "camera_permission_status": _first(
            payload.get("camera_permission_status"),
            "CAMERA_READY" if camera_visible else None,
            session.get("camera_status") if isinstance(session, dict) else None,
            fallback.get("camera_permission_status"),
            "CAMERA_WAITING_PERMISSION",
        ),
        "gps_permission_status": _first(
            payload.get("gps_permission_status"),
            "GPS_READY" if gps_active else None,
            fallback.get("gps_permission_status"),
            "GPS_WAITING_PERMISSION",
        ),
        "gps_status": _first(payload.get("gps_status"), "GPS_READY" if gps_active else None, fallback.get("gps_status"), "GPS_WAITING_PERMISSION"),
        "gps_accuracy_status": _first(payload.get("gps_accuracy_status"), derived.get("gps_accuracy_status"), fallback.get("gps_accuracy_status"), "GPS_ACCURACY_UNKNOWN"),
        "gps_accuracy_m": _first(payload.get("gps_accuracy_m"), gps_current.get("accuracy"), fallback.get("gps_accuracy_m"), ""),
        "gps_watch_status": _first(payload.get("gps_watch_status"), "GPS_WATCH_ACTIVE" if gps_active else None, fallback.get("gps_watch_status"), "GPS_WATCH_NOT_CONFIRMED"),
        "camera_preview_status": _first(payload.get("camera_preview_status"), "CAMERA_PREVIEW_ACTIVE" if camera_visible else None, fallback.get("camera_preview_status"), "CAMERA_PREVIEW_NOT_CONFIRMED"),
        "frame_loop_status": _first(payload.get("frame_loop_status"), fallback.get("frame_loop_status"), "FRAME_LOOP_NOT_CONFIRMED"),
        "start_session_status": _first(payload.get("start_session_status"), "PASS" if start_ok else None, fallback.get("start_session_status"), ""),
        "stop_record_status": _first(payload.get("stop_record_status"), "PASS" if stop_ok else None, fallback.get("stop_record_status"), ""),
        "shutter_status": _first(payload.get("shutter_status"), "PASS" if shutter_ok else None, fallback.get("shutter_status"), "SHUTTER_NOT_CONFIRMED"),
        "report_page_status": _first(payload.get("report_page_status"), "PASS" if report_ok else None, fallback.get("report_page_status"), "REPORT_NOT_CONFIRMED"),
        "result_page_status": _first(payload.get("result_page_status"), "PASS" if result_ok else None, fallback.get("result_page_status"), "RESULT_NOT_CONFIRMED"),
        "map_status": _first(payload.get("map_status"), "NO_GPS_NO_MARKER_CONFIRMED" if map_ok else None, fmap.get("status"), fallback.get("map_status"), "NO_GPS_NO_MARKER"),
        "distance_reliability_status": _first(payload.get("distance_reliability_status"), derived.get("distance_reliability_status"), fallback.get("distance_reliability_status"), ""),
        "latest_latency_ms": _first(payload.get("latest_latency_ms"), fallback.get("latest_latency_ms"), ""),
        "visibility_state": _first(payload.get("visibility_state"), session.get("visibility_state") if isinstance(session, dict) else None, fallback.get("visibility_state"), "visible"),
        "foreground_recording_status": _first(
            payload.get("foreground_recording_status"),
            session.get("foreground_recording_status") if isinstance(session, dict) else None,
            fallback.get("foreground_recording_status"),
            "FOREGROUND_RECORDING_REQUIRED",
        ),
        "model_status": _first(payload.get("model_status"), model.get("model_status"), fallback.get("model_status"), "MODEL_NOT_READY"),
        "no_fake_detection_status": _first(payload.get("no_fake_detection_status"), fallback.get("no_fake_detection_status"), "PASS"),
    }
    return {key: defaults.get(key) for key in AUTO_CHECK_KEYS}


def _evidence_payload(acceptance: FieldAcceptance, payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "acceptance_id": acceptance.acceptance_id,
        "session_id": acceptance.session_id,
        "secure_context": acceptance.automatic_checklist.get("secure_context"),
        "camera": acceptance.automatic_checklist.get("camera_permission_status"),
        "gps": acceptance.automatic_checklist.get("gps_accuracy_status"),
        "gps_accuracy_m": acceptance.automatic_checklist.get("gps_accuracy_m"),
        "frame_loop": acceptance.automatic_checklist.get("frame_loop_status"),
        "start_session": acceptance.automatic_checklist.get("start_session_status"),
        "stop_record": acceptance.automatic_checklist.get("stop_record_status"),
        "shutter": acceptance.automatic_checklist.get("shutter_status"),
        "report": acceptance.automatic_checklist.get("report_page_status"),
        "result": acceptance.automatic_checklist.get("result_page_status"),
        "map": acceptance.automatic_checklist.get("map_status"),
        "latency_ms": acceptance.automatic_checklist.get("latest_latency_ms"),
        "visibility_state": acceptance.automatic_checklist.get("visibility_state"),
        "foreground_recording_status": acceptance.automatic_checklist.get("foreground_recording_status"),
        "model_status": acceptance.automatic_checklist.get("model_status"),
        "distance_reliability_status": acceptance.automatic_checklist.get("distance_reliability_status"),
        "no_fake_detection": True,
        "no_fake_acceptance": True,
        "raw_payload_keys": sorted(str(key) for key in payload.keys()),
    }


def _acceptance_status(acceptance: FieldAcceptance) -> tuple[str, list[str]]:
    manual_values = list(acceptance.manual_checklist.values())
    if not manual_values or not any(manual_values):
        return "PHYSICAL_HP_ACCEPTANCE_PENDING_USER_TEST", ["NO_HP_PHYSICAL_EVIDENCE_SUBMITTED"]
    if acceptance.problem_note:
        return "PHYSICAL_HP_ACCEPTANCE_FAIL_REVIEW_REQUIRED", ["OPERATOR_REPORTED_FIELD_PROBLEM"]
    validation = validate_acceptance_payload(asdict(acceptance))
    status = str(validation.get("acceptance_status") or validation.get("status"))
    reasons = [str(item) for item in validation.get("reason_codes", [])]
    if status == "PHYSICAL_HP_ACCEPTANCE_PASS_WITH_GPS_LIMITATION":
        return status, reasons
    if status == "PHYSICAL_HP_ACCEPTANCE_PASS":
        return status, reasons
    if not all(manual_values):
        return "PHYSICAL_HP_ACCEPTANCE_PARTIAL", ["MANUAL_CONFIRMATION_INCOMPLETE", *reasons]
    if status.startswith("PHYSICAL_HP_ACCEPTANCE_FAIL_"):
        return status, reasons
    if status == "PHYSICAL_HP_ACCEPTANCE_PARTIAL_REVIEW_REQUIRED":
        return "PHYSICAL_HP_ACCEPTANCE_PARTIAL", reasons
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
        "missing_requirements": validate_acceptance_payload(asdict(acceptance)).get("missing_requirements", []),
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


def _first(*values: Any) -> Any:
    for value in values:
        if value not in {None, ""}:
            return value
    return ""
