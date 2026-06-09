from __future__ import annotations

import importlib
import json
import sys
import time
from pathlib import Path
from typing import Any, Dict

ROOT = Path(r"E:\Projects\ULP_Project")
SRC = ROOT / "src"
REPORT = ROOT / "reports" / "final_step2_prediction_geometry_eta_gate.json"

sys.path.insert(0, str(SRC))


def load_app():
    mod = importlib.import_module("ulp_project.flask_app")
    if hasattr(mod, "create_app"):
        return mod.create_app()
    if hasattr(mod, "app"):
        return mod.app
    if hasattr(mod, "get_app"):
        return mod.get_app()
    raise RuntimeError("APP_FACTORY_NOT_FOUND")


def post_json(client, path: str, payload: Dict[str, Any]):
    started = time.perf_counter()
    resp = client.post(path, json=payload)
    elapsed_ms = int((time.perf_counter() - started) * 1000)
    data = resp.get_json(silent=True)
    if data is None:
        raw = resp.get_data()
        data = raw.decode("utf-8", errors="ignore") if isinstance(raw, bytes) else str(raw)
    return resp.status_code, elapsed_ms, data


def get_json(client, path: str):
    started = time.perf_counter()
    resp = client.get(path)
    elapsed_ms = int((time.perf_counter() - started) * 1000)
    data = resp.get_json(silent=True)
    if data is None:
        raw = resp.get_data()
        data = raw.decode("utf-8", errors="ignore") if isinstance(raw, bytes) else str(raw)
    return resp.status_code, elapsed_ms, data


def main() -> int:
    from ulp_project.final_step2_prediction_runtime import final_step2_predict

    result: Dict[str, Any] = {
        "version": "final_step2_prediction_geometry_eta_gate",
        "status": "UNKNOWN",
        "hard_failures": [],
        "checks": {},
        "policy": {
            "step_name": "LANGKAH_BESAR_2_PREDIKSI_GEOMETRI_CLEARANCE_ETA_GROWTH_PRIOR",
            "latency_budget_ms": 1000,
            "no_label_touch": True,
            "no_raw_touch": True,
            "no_dataset_touch": True,
            "no_runs_touch": True,
            "no_weights_touch": True,
            "no_fake_detection": True,
            "no_fake_gps": True,
            "no_fake_clearance": True,
        },
    }

    # Pure function checks.
    case_5m = final_step2_predict({
        "session_id": "FS_STEP2_5M",
        "point_id": "V001_pohon_sono",
        "clearance_m": 5.0,
        "growth_rate_m_per_day": 0.01,
        "tree_detected": True,
    })
    result["checks"]["case_5m_001"] = case_5m

    if case_5m.get("eta", {}).get("eta_days") != 200.0:
        result["hard_failures"].append("ETA_5M_001_NOT_200_DAYS")

    if case_5m.get("latency_ms", 9999) > 1000:
        result["hard_failures"].append("PURE_FUNCTION_LATENCY_EXCEEDS_1000MS")

    if case_5m.get("can_claim_final_eta") is not False:
        result["hard_failures"].append("FINAL_ETA_CLAIM_NOT_BLOCKED")

    case_unsafe = final_step2_predict({
        "session_id": "FS_STEP2_UNSAFE",
        "point_id": "V001_pohon_sono",
        "clearance_m": 2.75,
        "growth_rate_m_per_day": 0.01,
        "tree_detected": True,
    })
    result["checks"]["case_2_75m"] = case_unsafe

    if case_unsafe.get("eta", {}).get("eta_days") != 0:
        result["hard_failures"].append("ETA_2_75M_NOT_ZERO")

    if case_unsafe.get("eta", {}).get("clearance_display_m_integer_floor") != 2:
        result["hard_failures"].append("DISPLAY_FLOOR_2_75M_NOT_2")

    case_no_data = final_step2_predict({
        "session_id": "FS_STEP2_NODATA",
        "point_id": "V001_pohon_sono",
        "tree_detected": True,
    })
    result["checks"]["case_no_clearance"] = case_no_data

    if case_no_data.get("eta_status") != "INSUFFICIENT_GEOMETRY_DATA":
        result["hard_failures"].append("NO_CLEARANCE_SHOULD_BE_INSUFFICIENT_GEOMETRY_DATA")

    # Flask route checks.
    app = load_app()
    routes = {rule.rule for rule in app.url_map.iter_rules()}
    required_routes = [
        "/api/field/session/final-step2-predict",
        "/api/field/session/final-step2-status",
    ]
    result["checks"]["route_checks"] = {r: r in routes for r in required_routes}

    missing_routes = [r for r in required_routes if r not in routes]
    if missing_routes:
        result["hard_failures"].append({"missing_routes": missing_routes})

    client = app.test_client()

    status_code, elapsed_ms, status_data = get_json(client, "/api/field/session/final-step2-status")
    result["checks"]["status_route"] = {
        "http_status": status_code,
        "elapsed_ms": elapsed_ms,
        "data": status_data,
    }
    if status_code != 200:
        result["hard_failures"].append("STATUS_ROUTE_NOT_200")
    if elapsed_ms > 1000:
        result["hard_failures"].append("STATUS_ROUTE_LATENCY_EXCEEDS_1000MS")

    pred_status, pred_elapsed_ms, pred_data = post_json(client, "/api/field/session/final-step2-predict", {
        "session_id": "FS_STEP2_ROUTE",
        "point_id": "V001_pohon_sono",
        "clearance_m": 5.0,
        "growth_rate_m_per_day": 0.01,
        "tree_detected": True,
        "source": "final_step2_gate",
    })
    result["checks"]["predict_route_5m"] = {
        "http_status": pred_status,
        "elapsed_ms": pred_elapsed_ms,
        "data": pred_data,
    }
    if pred_status != 200:
        result["hard_failures"].append("PREDICT_ROUTE_NOT_200")
    if pred_elapsed_ms > 1000:
        result["hard_failures"].append("PREDICT_ROUTE_LATENCY_EXCEEDS_1000MS")
    if isinstance(pred_data, dict):
        if pred_data.get("eta", {}).get("eta_days") != 200.0:
            result["hard_failures"].append("PREDICT_ROUTE_ETA_5M_001_NOT_200")
        if pred_data.get("no_fake_clearance") is not True:
            result["hard_failures"].append("PREDICT_ROUTE_NO_FAKE_CLEARANCE_NOT_TRUE")
        if pred_data.get("can_claim_final_clearance") is not False:
            result["hard_failures"].append("PREDICT_ROUTE_FINAL_CLEARANCE_NOT_BLOCKED")
        if pred_data.get("latency_contract_status") != "LATENCY_WITHIN_1000MS":
            result["hard_failures"].append("PREDICT_ROUTE_INTERNAL_LATENCY_NOT_WITHIN_1000MS")
    else:
        result["hard_failures"].append("PREDICT_ROUTE_NON_JSON")

    if result["hard_failures"]:
        result["status"] = "PREDICTION_GEOMETRY_ETA_GUARDED_FAILED"
        code = 1
    else:
        result["status"] = "PREDICTION_GEOMETRY_ETA_GUARDED_READY"
        code = 0

    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
