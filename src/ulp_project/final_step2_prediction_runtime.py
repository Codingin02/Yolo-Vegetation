from __future__ import annotations

import math
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional


PROJECT_ROOT = Path(r"E:\Projects\ULP_Project")
TREE_MODEL_PATH = PROJECT_ROOT / "runs" / "detect" / "v001_pohon_sono_only_v2" / "weights" / "best.pt"
GROWTH_EXCEL_PATH = PROJECT_ROOT / "data" / "growth_model" / "pohon_sono" / "dataset_pohon_sono_surabaya_utara_2015_2025_lengkap_v2.xlsx"

CLEARANCE_THRESHOLD_M = 3.0
MONITORING_THRESHOLD_M = 4.0
LATENCY_BUDGET_MS = 1000


def now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def to_float(value: Any, default: Optional[float] = None) -> Optional[float]:
    try:
        if value is None or value == "":
            return default
        v = float(value)
        if math.isnan(v) or math.isinf(v):
            return default
        return v
    except Exception:
        return default


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def tree_model_status() -> str:
    return "TREE_MODEL_READY_CANDIDATE" if TREE_MODEL_PATH.exists() else "TREE_MODEL_NOT_READY"


def growth_prior_status() -> Dict[str, Any]:
    if GROWTH_EXCEL_PATH.exists():
        return {
            "growth_prior_status": "GROWTH_PRIOR_READY_PROXY_DATASET",
            "source_status": "PROXY_NOT_FIELD_OBSERVED",
            "dataset_path_status": "GROWTH_EXCEL_FOUND",
            "limitations": [
                "Dataset pertumbuhan masih proxy, bukan observasi lapangan final.",
                "Nilai growth hanya prior untuk estimasi provisional.",
            ],
        }

    return {
        "growth_prior_status": "GROWTH_PRIOR_DATASET_NOT_FOUND",
        "source_status": "NOT_AVAILABLE",
        "dataset_path_status": "GROWTH_EXCEL_NOT_FOUND",
        "limitations": [
            "Dataset growth proxy tidak ditemukan; prediksi hanya memakai input manual growth_rate_m_per_day jika diberikan.",
        ],
    }


def select_growth_rate(payload: Dict[str, Any]) -> Dict[str, Any]:
    raw = to_float(payload.get("growth_rate_m_per_day"))
    if raw is not None and raw > 0:
        return {
            "growth_rate_m_per_day": round(raw, 6),
            "growth_rate_source": "MANUAL_OPERATOR_INPUT",
            "growth_rate_status": "GROWTH_RATE_READY_MANUAL",
        }

    # Proxy aman untuk smoke, bukan klaim biologis final.
    fallback = to_float(payload.get("proxy_growth_rate_m_per_day"), 0.01)
    if fallback is None or fallback <= 0:
        fallback = 0.01

    return {
        "growth_rate_m_per_day": round(fallback, 6),
        "growth_rate_source": "PROXY_DEFAULT_NOT_FIELD_OBSERVED",
        "growth_rate_status": "GROWTH_RATE_READY_PROXY",
    }


def geometry_guard(payload: Dict[str, Any]) -> Dict[str, Any]:
    tree_detected = bool(payload.get("tree_detected") or payload.get("tree_detected_candidate"))
    pole_detected = bool(payload.get("pole_detected") or payload.get("support_structure_detected"))
    conductor_detected = bool(payload.get("conductor_detected"))
    reference_height_m = to_float(payload.get("reference_height_m"))
    reference_pixel_height = to_float(payload.get("reference_pixel_height"))
    clearance_m = to_float(payload.get("clearance_m"))

    reference_valid = (
        reference_height_m is not None
        and reference_pixel_height is not None
        and reference_height_m > 0
        and reference_pixel_height > 0
    )

    meter_per_px = None
    if reference_valid:
        meter_per_px = round(reference_height_m / reference_pixel_height, 6)

    has_auto_geometry = tree_detected and pole_detected and conductor_detected and reference_valid

    if has_auto_geometry:
        return {
            "geometry_status": "REFERENCE_GEOMETRY_READY",
            "measurement_source": "AUTO_OR_REFERENCE_GEOMETRY_CANDIDATE",
            "clearance_claim_status": "CLEARANCE_CANDIDATE_NEEDS_FIELD_VALIDATION",
            "meter_per_px": meter_per_px,
            "reason_codes": ["TREE_POLE_CONDUCTOR_REFERENCE_AVAILABLE"],
            "can_compute_provisional_eta": clearance_m is not None,
            "can_claim_final_clearance": False,
            "no_fake_clearance": True,
        }

    if clearance_m is not None:
        return {
            "geometry_status": "MANUAL_CLEARANCE_INPUT_READY",
            "measurement_source": "MANUAL_PROVISIONAL",
            "clearance_claim_status": "CLEARANCE_MANUAL_PROVISIONAL_NOT_FINAL",
            "meter_per_px": meter_per_px,
            "reason_codes": ["MANUAL_CLEARANCE_USED", "AUTO_GEOMETRY_NOT_FINAL"],
            "can_compute_provisional_eta": True,
            "can_claim_final_clearance": False,
            "no_fake_clearance": True,
        }

    if tree_detected and (not pole_detected or not conductor_detected):
        return {
            "geometry_status": "TREE_DETECTED_BUT_POLE_CONDUCTOR_NOT_READY",
            "measurement_source": "DETECTION_CANDIDATE_ONLY",
            "clearance_claim_status": "CLEARANCE_NOT_FINAL_NO_POLE_CONDUCTOR",
            "meter_per_px": meter_per_px,
            "reason_codes": ["TREE_DETECTED_CANDIDATE", "POLE_CONDUCTOR_MODEL_NOT_READY"],
            "can_compute_provisional_eta": False,
            "can_claim_final_clearance": False,
            "no_fake_clearance": True,
        }

    return {
        "geometry_status": "INSUFFICIENT_GEOMETRY_DATA",
        "measurement_source": "NOT_AVAILABLE",
        "clearance_claim_status": "CLEARANCE_NOT_FINAL",
        "meter_per_px": meter_per_px,
        "reason_codes": ["CLEARANCE_INPUT_OR_REFERENCE_GEOMETRY_REQUIRED"],
        "can_compute_provisional_eta": False,
        "can_claim_final_clearance": False,
        "no_fake_clearance": True,
    }


def compute_eta(clearance_m: Optional[float], growth_rate_m_per_day: Optional[float]) -> Dict[str, Any]:
    if clearance_m is None:
        return {
            "eta_status": "INSUFFICIENT_GEOMETRY_DATA",
            "risk_status": "INSUFFICIENT_DATA",
            "action_priority": "NOT_AVAILABLE",
            "eta_days": None,
            "eta_months": None,
            "clearance_display_m_integer_floor": None,
            "clearance_raw_m": None,
            "reason_codes": ["CLEARANCE_MISSING"],
        }

    display_floor = math.floor(clearance_m)

    if clearance_m <= CLEARANCE_THRESHOLD_M:
        return {
            "eta_status": "ETA_READY_PROVISIONAL",
            "risk_status": "ALREADY_WITHIN_UNSAFE_ZONE",
            "action_priority": "CRITICAL",
            "eta_days": 0,
            "eta_months": 0.0,
            "clearance_display_m_integer_floor": display_floor,
            "clearance_raw_m": round(clearance_m, 4),
            "reason_codes": ["CLEARANCE_LE_3M_THRESHOLD"],
        }

    if growth_rate_m_per_day is None or growth_rate_m_per_day <= 0:
        return {
            "eta_status": "INSUFFICIENT_GROWTH_RATE_DATA",
            "risk_status": "INSUFFICIENT_DATA",
            "action_priority": "NOT_AVAILABLE",
            "eta_days": None,
            "eta_months": None,
            "clearance_display_m_integer_floor": display_floor,
            "clearance_raw_m": round(clearance_m, 4),
            "reason_codes": ["GROWTH_RATE_MISSING_OR_INVALID"],
        }

    eta_days = (clearance_m - CLEARANCE_THRESHOLD_M) / growth_rate_m_per_day
    eta_months = eta_days / 30.4375

    if eta_days <= 30:
        risk = "HIGH"
        priority = "HIGH"
    elif eta_days <= 90:
        risk = "MEDIUM"
        priority = "MEDIUM"
    else:
        risk = "LOW_MONITORING"
        priority = "MONITOR"

    eta_4m_days = None
    if clearance_m > MONITORING_THRESHOLD_M:
        eta_4m_days = (clearance_m - MONITORING_THRESHOLD_M) / growth_rate_m_per_day
    elif clearance_m <= MONITORING_THRESHOLD_M:
        eta_4m_days = 0

    return {
        "eta_status": "ETA_READY_PROVISIONAL",
        "risk_status": risk,
        "action_priority": priority,
        "eta_days": round(eta_days, 2),
        "eta_months": round(eta_months, 2),
        "eta_to_4m_monitoring_days": round(eta_4m_days, 2) if eta_4m_days is not None else None,
        "clearance_display_m_integer_floor": display_floor,
        "clearance_raw_m": round(clearance_m, 4),
        "reason_codes": ["ETA_COMPUTED_WITH_3M_THRESHOLD", "PROVISIONAL_NOT_FINAL"],
    }


def final_step2_predict(payload: Dict[str, Any]) -> Dict[str, Any]:
    started = time.perf_counter()

    if not isinstance(payload, dict):
        payload = {}

    clearance_m = to_float(payload.get("clearance_m"))
    growth = select_growth_rate(payload)
    growth_status = growth_prior_status()
    geometry = geometry_guard(payload)
    eta = compute_eta(clearance_m, growth.get("growth_rate_m_per_day"))

    all_reason_codes = []
    for part in (geometry, eta):
        codes = part.get("reason_codes") or []
        if isinstance(codes, list):
            all_reason_codes.extend(str(c) for c in codes)

    latency_ms = int((time.perf_counter() - started) * 1000)

    result = {
        "ok": True,
        "version": "final_step2_prediction_geometry_eta_runtime",
        "timestamp": now_iso(),
        "session_id": str(payload.get("session_id") or ""),
        "point_id": str(payload.get("point_id") or ""),
        "runtime_mode": "PREDICTION_GEOMETRY_ETA_GUARDED",
        "refresh_contract_ms": LATENCY_BUDGET_MS,
        "latency_ms": latency_ms,
        "latency_contract_status": "LATENCY_WITHIN_1000MS" if latency_ms <= LATENCY_BUDGET_MS else "LATENCY_EXCEEDS_1000MS",
        "tree_model_status": tree_model_status(),
        "pole_model_status": "POLE_MODEL_NOT_READY" if not payload.get("pole_model_status") else str(payload.get("pole_model_status")),
        "conductor_model_status": "CONDUCTOR_MODEL_NOT_READY" if not payload.get("conductor_model_status") else str(payload.get("conductor_model_status")),
        "growth": growth,
        "growth_prior": growth_status,
        "geometry": geometry,
        "eta": eta,
        "prediction_status": "PREDICTION_GEOMETRY_ETA_GUARDED_READY",
        "clearance_status": geometry.get("clearance_claim_status"),
        "eta_status": eta.get("eta_status"),
        "risk_status": eta.get("risk_status"),
        "action_priority": eta.get("action_priority"),
        "reason_codes": list(dict.fromkeys(all_reason_codes)),
        "operator_message": "Prediksi bersifat provisional. Clearance dan ETA final menunggu model pole/conductor serta reference geometry lapangan yang sah.",
        "no_fake_detection": True,
        "no_fake_gps": True,
        "no_fake_clearance": True,
        "can_claim_final_clearance": False,
        "can_claim_final_eta": False,
    }
    return result


def install_final_step2_prediction_runtime(app: Any) -> Any:
    if getattr(app, "_final_step2_prediction_runtime_installed", False):
        return app

    @app.post("/api/field/session/final-step2-predict")
    def final_step2_predict_route():  # type: ignore[unused-ignore]
        try:
            from flask import jsonify, request
            payload = request.get_json(silent=True) or {}
            if not isinstance(payload, dict):
                payload = {}
            return jsonify(final_step2_predict(payload)), 200
        except Exception as exc:
            from flask import jsonify
            return jsonify({
                "ok": False,
                "status": "FINAL_STEP2_PREDICTION_EXCEPTION",
                "error_type": type(exc).__name__,
                "message": str(exc),
                "no_fake_detection": True,
                "no_fake_gps": True,
                "no_fake_clearance": True,
                "can_claim_final_clearance": False,
                "can_claim_final_eta": False,
            }), 200

    @app.get("/api/field/session/final-step2-status")
    def final_step2_status_route():  # type: ignore[unused-ignore]
        from flask import jsonify
        return jsonify({
            "ok": True,
            "status": "FINAL_STEP2_PREDICTION_RUNTIME_READY",
            "refresh_contract_ms": LATENCY_BUDGET_MS,
            "tree_model_status": tree_model_status(),
            "growth_prior": growth_prior_status(),
            "clearance_threshold_m": CLEARANCE_THRESHOLD_M,
            "no_fake_detection": True,
            "no_fake_gps": True,
            "no_fake_clearance": True,
        }), 200

    app._final_step2_prediction_runtime_installed = True
    return app


__all__ = [
    "final_step2_predict",
    "install_final_step2_prediction_runtime",
    "compute_eta",
    "geometry_guard",
    "growth_prior_status",
]
