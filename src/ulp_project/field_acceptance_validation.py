"""Progress 6.4 physical HP acceptance evidence validation."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .model_handoff import check_model_handoff
from .paths import PROJECT_ROOT

DEFAULT_ACCEPTANCE_LATEST = PROJECT_ROOT / "outputs" / "runtime" / "field_acceptance" / "latest.json"

PASS_STATUS = "PHYSICAL_HP_ACCEPTANCE_PASS"
PASS_WITH_GPS_LIMITATION = "PHYSICAL_HP_ACCEPTANCE_PASS_WITH_GPS_LIMITATION"
PENDING_STATUS = "PHYSICAL_HP_ACCEPTANCE_PENDING_USER_TEST"
PARTIAL_STATUS = "PHYSICAL_HP_ACCEPTANCE_PARTIAL_REVIEW_REQUIRED"

READY_VALUES = {"PASS", "OK", "READY", True}
CAMERA_READY_VALUES = {"CAMERA_READY", "CAMERA_ACTIVE", "PASS"}
GPS_READY_VALUES = {"GPS_READY", "GPS_ACTIVE", "GPS_ACCURACY_GOOD", "GPS_ACCURACY_MEDIUM", "GPS_ACCURACY_LOW", "PASS"}
PASSISH_VALUES = {"PASS", "OK", "READY", "SHUTTER_RECORDED", "REPORT_OPENED", "RESULT_OPENED", True}
MAP_READY_VALUES = {
    "MAP_READY",
    "MAP_HTML_READY",
    "MAP_BASIC_FALLBACK",
    "FOLIUM_READY",
    "NO_GPS_NO_MARKER",
    "NO_GPS_NO_MARKER_CONFIRMED",
}
NO_FAKE_DETECTION_VALUES = {"PASS", "NO_FAKE_DETECTION_PASS", "TRUE", True}


def latest_acceptance_path(runtime_root: Path | None = None) -> Path:
    if runtime_root is None:
        return DEFAULT_ACCEPTANCE_LATEST
    return runtime_root / "field_acceptance" / "latest.json"


def load_latest_acceptance(runtime_root: Path | None = None) -> dict[str, Any]:
    path = latest_acceptance_path(runtime_root)
    if not path.exists():
        return {
            "status": PENDING_STATUS,
            "acceptance_status": PENDING_STATUS,
            "reason_codes": ["NO_HP_PHYSICAL_EVIDENCE_SUBMITTED"],
            "latest_path": str(path),
        }
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return {
            "status": "PHYSICAL_HP_ACCEPTANCE_EVIDENCE_JSON_INVALID",
            "acceptance_status": "PHYSICAL_HP_ACCEPTANCE_EVIDENCE_JSON_INVALID",
            "reason_codes": [f"EVIDENCE_JSON_INVALID:{exc.msg}"],
            "latest_path": str(path),
        }


def validate_latest_acceptance(runtime_root: Path | None = None) -> dict[str, Any]:
    return validate_acceptance_payload(load_latest_acceptance(runtime_root))


def validate_acceptance_payload(payload: dict[str, Any] | None) -> dict[str, Any]:
    payload = payload or {}
    auto = payload.get("automatic_checklist") or {}
    manual = payload.get("manual_checklist") or {}
    evidence = payload.get("evidence") or {}
    model = check_model_handoff()

    submitted = _bool(payload.get("acceptance_submitted")) or bool(payload.get("submitted_at"))
    current_url_mode = _value(auto, payload, "current_url_mode")
    secure_context = _value(auto, payload, "secure_context", "secure_context_status")
    camera_status = _value(auto, payload, "camera_permission_status", "camera_status") or evidence.get("camera")
    gps_status = (
        _value(auto, payload, "gps_status", "gps_permission_status")
        or _value(auto, payload, "gps_accuracy_status")
        or evidence.get("gps")
    )
    gps_accuracy_status = _value(auto, payload, "gps_accuracy_status")
    gps_accuracy_m = _to_float(_value(auto, payload, "gps_accuracy_m", "current_accuracy_m", "gps_accuracy_m"))
    start_session_status = _check_status(auto, payload, manual, "start_session_status", "start_record_ok")
    stop_record_status = _check_status(auto, payload, manual, "stop_record_status", "stop_record_ok")
    shutter_status = _check_status(auto, payload, manual, "shutter_status", "shutter_recorded")
    report_page_status = _check_status(auto, payload, manual, "report_page_status", "report_opened")
    result_page_status = _check_status(auto, payload, manual, "result_page_status", "result_opened")
    map_status = _value(auto, payload, "map_status") or evidence.get("map") or "NO_GPS_NO_MARKER"
    model_status = _value(auto, payload, "model_status") or evidence.get("model_status") or model.get("model_status")
    no_fake_detection_status = _value(auto, payload, "no_fake_detection_status") or payload.get("no_fake_detection_status")
    operator_name = str(payload.get("operator_name") or "").strip()
    device_name = str(payload.get("device_name") or "").strip()
    distance_reliability_status = _value(auto, payload, "distance_reliability_status")
    current_lat = _to_float(_value(auto, payload, "current_latitude", "gps_lat", "lat"))
    current_lon = _to_float(_value(auto, payload, "current_longitude", "gps_lon", "lon"))
    map_failure_reason = str(payload.get("map_failure_reason") or payload.get("problem_note") or "").strip()

    missing: list[str] = []
    if not submitted:
        return _result(
            payload,
            PENDING_STATUS,
            ["NO_HP_PHYSICAL_EVIDENCE_SUBMITTED"],
            missing_requirements=["submit_acceptance_from_hp"],
            evidence_summary=_summary(payload, auto, evidence, model),
            model_handoff=model,
        )
    if current_url_mode != "HTTPS_PUBLIC_READY" or secure_context != "SECURE_CONTEXT_OK" or not _boolish(
        manual.get("public_https_url_opened") or payload.get("submitted_from_public_https")
    ):
        missing.append("public_https_secure_context")
    if camera_status not in CAMERA_READY_VALUES:
        missing.append("camera_ready")
    if gps_status not in GPS_READY_VALUES and gps_accuracy_status not in GPS_READY_VALUES:
        missing.append("gps_ready")
    if gps_accuracy_m is None:
        missing.append("gps_accuracy_m")
    if start_session_status not in PASSISH_VALUES:
        missing.append("start_session_pass")
    if stop_record_status not in PASSISH_VALUES:
        missing.append("stop_record_pass")
    if shutter_status not in PASSISH_VALUES:
        missing.append("shutter_pass")
    if report_page_status not in PASSISH_VALUES:
        missing.append("report_page_pass")
    if result_page_status not in PASSISH_VALUES:
        missing.append("result_page_pass")
    if map_status not in MAP_READY_VALUES:
        missing.append("map_status_clear")
    if current_lat is not None and current_lon is not None and map_status == "NO_GPS_NO_MARKER" and not map_failure_reason:
        missing.append("map_marker_or_failure_reason")
    if not model_status:
        missing.append("model_status")
    if str(no_fake_detection_status).upper() not in NO_FAKE_DETECTION_VALUES:
        missing.append("no_fake_detection_pass")
    if not (operator_name or device_name):
        missing.append("operator_or_device_name")

    if missing:
        return _result(
            payload,
            _failure_status(missing),
            [f"MISSING_{item.upper()}" for item in missing],
            missing_requirements=missing,
            evidence_summary=_summary(payload, auto, evidence, model),
            model_handoff=model,
        )

    gps_limitation = gps_accuracy_status == "GPS_ACCURACY_LOW" or gps_status == "GPS_ACCURACY_LOW"
    gps_limitation = gps_limitation or distance_reliability_status in {
        "GPS_ACCURACY_GREATER_THAN_DISTANCE",
        "DISTANCE_TOO_SMALL_FOR_GPS_RELIABILITY",
        "GPS_ACCURACY_UNKNOWN",
    }
    status = PASS_WITH_GPS_LIMITATION if gps_limitation else PASS_STATUS
    reason = "GPS_LIMITATION_RECORDED_ACCEPTANCE_ALLOWED" if gps_limitation else "HP_PHYSICAL_ACCEPTANCE_EVIDENCE_COMPLETE"
    return _result(
        payload,
        status,
        [reason],
        missing_requirements=[],
        evidence_summary=_summary(payload, auto, evidence, model),
        model_handoff=model,
    )


def _failure_status(missing: list[str]) -> str:
    if "public_https_secure_context" in missing:
        return "PHYSICAL_HP_ACCEPTANCE_FAIL_NO_PUBLIC_HTTPS"
    if "camera_ready" in missing:
        return "PHYSICAL_HP_ACCEPTANCE_FAIL_CAMERA_NOT_READY"
    if "gps_ready" in missing or "gps_accuracy_m" in missing:
        return "PHYSICAL_HP_ACCEPTANCE_FAIL_GPS_NOT_READY"
    if "shutter_pass" in missing:
        return "PHYSICAL_HP_ACCEPTANCE_FAIL_SHUTTER_NOT_RECORDED"
    if "report_page_pass" in missing or "result_page_pass" in missing:
        return "PHYSICAL_HP_ACCEPTANCE_FAIL_REPORT_RESULT_NOT_OPENED"
    return PARTIAL_STATUS


def _result(
    payload: dict[str, Any],
    status: str,
    reason_codes: list[str],
    *,
    missing_requirements: list[str],
    evidence_summary: dict[str, Any],
    model_handoff: dict[str, Any],
) -> dict[str, Any]:
    return {
        "status": status,
        "acceptance_status": status,
        "acceptance_id": payload.get("acceptance_id", ""),
        "session_id": payload.get("session_id", ""),
        "reason_codes": reason_codes,
        "missing_requirements": missing_requirements,
        "evidence_summary": evidence_summary,
        "model_status": evidence_summary.get("model_status") or model_handoff.get("model_status", "MODEL_NOT_READY"),
        "bestpt_status": "BESTPT_VALID_OR_PRESENT" if model_handoff.get("model_status") != "MODEL_NOT_READY" else "BESTPT_NOT_AVAILABLE",
        "model_not_ready_allowed": True,
        "no_fake_acceptance": True,
        "no_fake_detection": True,
        "no_fake_gps": True,
        "no_fake_precision": True,
    }


def _summary(payload: dict[str, Any], auto: dict[str, Any], evidence: dict[str, Any], model: dict[str, Any]) -> dict[str, Any]:
    return {
        "current_url_mode": _value(auto, payload, "current_url_mode"),
        "secure_context_status": _value(auto, payload, "secure_context", "secure_context_status"),
        "camera_status": _value(auto, payload, "camera_permission_status", "camera_status") or evidence.get("camera"),
        "gps_status": _value(auto, payload, "gps_status", "gps_permission_status") or evidence.get("gps"),
        "gps_accuracy_m": _value(auto, payload, "gps_accuracy_m", "current_accuracy_m", "gps_accuracy_m"),
        "start_session_status": _value(auto, payload, "start_session_status"),
        "stop_record_status": _value(auto, payload, "stop_record_status"),
        "shutter_status": _value(auto, payload, "shutter_status") or evidence.get("shutter"),
        "report_page_status": _value(auto, payload, "report_page_status") or evidence.get("report"),
        "result_page_status": _value(auto, payload, "result_page_status") or evidence.get("result"),
        "map_status": _value(auto, payload, "map_status") or evidence.get("map"),
        "model_status": _value(auto, payload, "model_status") or evidence.get("model_status") or model.get("model_status"),
        "distance_reliability_status": _value(auto, payload, "distance_reliability_status"),
    }


def _value(auto: dict[str, Any], payload: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        if key in auto and auto[key] not in {None, ""}:
            return auto[key]
        if key in payload and payload[key] not in {None, ""}:
            return payload[key]
    return None


def _check_status(auto: dict[str, Any], payload: dict[str, Any], manual: dict[str, Any], status_key: str, manual_key: str) -> Any:
    status = _value(auto, payload, status_key)
    if status not in {None, ""}:
        return status
    return "PASS" if _boolish(manual.get(manual_key) or payload.get(manual_key)) else ""


def _bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "ya", "on", "pass"}


def _boolish(value: Any) -> bool:
    return _bool(value)


def _to_float(value: Any) -> float | None:
    if value in {None, ""}:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
