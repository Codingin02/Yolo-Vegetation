from __future__ import annotations

import base64
import importlib
import json
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Tuple

ROOT = Path(r"E:\Projects\ULP_Project")
SRC = ROOT / "src"
REPORT = ROOT / "reports" / "final_step3_field_acceptance_report_lock_gate.json"

sys.path.insert(0, str(SRC))

LATENCY_BUDGET_MS = 1000


def now() -> str:
    return datetime.now().isoformat(timespec="seconds")


def load_app():
    mod = importlib.import_module("ulp_project.flask_app")
    if hasattr(mod, "create_app"):
        return mod.create_app()
    if hasattr(mod, "app"):
        return mod.app
    if hasattr(mod, "get_app"):
        return mod.get_app()
    raise RuntimeError("APP_FACTORY_NOT_FOUND")


def safe_text(resp) -> str:
    raw = resp.get_data()
    if isinstance(raw, bytes):
        return raw.decode("utf-8", errors="ignore")
    return str(raw)


def get_text(client, path: str) -> Tuple[int, int, str]:
    started = time.perf_counter()
    resp = client.get(path)
    elapsed_ms = int((time.perf_counter() - started) * 1000)
    return resp.status_code, elapsed_ms, safe_text(resp)


def post_json(client, path: str, payload: Dict[str, Any]) -> Tuple[int, int, Any]:
    started = time.perf_counter()
    resp = client.post(path, json=payload)
    elapsed_ms = int((time.perf_counter() - started) * 1000)
    data = resp.get_json(silent=True)
    if data is None:
        data = safe_text(resp)[:1000]
    return resp.status_code, elapsed_ms, data


def route_set(app) -> set[str]:
    return {rule.rule for rule in app.url_map.iter_rules()}


def make_jpeg_data_url() -> str:
    import cv2
    import numpy as np

    img = np.zeros((480, 640, 3), dtype=np.uint8)
    img[:] = (18, 18, 18)
    cv2.rectangle(img, (210, 80), (430, 400), (20, 170, 70), -1)
    cv2.rectangle(img, (210, 80), (430, 400), (190, 255, 210), 3)
    cv2.putText(img, "FINAL STEP 3 FIELD", (130, 445), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (230, 255, 235), 2)
    ok, buf = cv2.imencode(".jpg", img, [int(cv2.IMWRITE_JPEG_QUALITY), 84])
    if not ok:
        raise RuntimeError("JPEG_ENCODE_FAILED")
    return "data:image/jpeg;base64," + base64.b64encode(buf.tobytes()).decode("ascii")


def add_latency_check(result: Dict[str, Any], name: str, elapsed_ms: int) -> None:
    result["latency_checks"][name] = elapsed_ms
    if elapsed_ms > LATENCY_BUDGET_MS:
        result["hard_failures"].append(f"{name}_LATENCY_EXCEEDS_1000MS")


def main() -> int:
    result: Dict[str, Any] = {
        "version": "final_step3_field_acceptance_report_lock_gate",
        "timestamp": now(),
        "root": str(ROOT),
        "status": "UNKNOWN",
        "hard_failures": [],
        "warnings": [],
        "route_checks": {},
        "ui_checks": {},
        "request_checks": {},
        "latency_checks": {},
        "final_report_lock": {},
        "policy": {
            "step_name": "LANGKAH_BESAR_3_FIELD_ACCEPTANCE_OUTPUT_OPERATOR_LAPORAN_FINAL",
            "latency_budget_ms": LATENCY_BUDGET_MS,
            "no_label_touch": True,
            "no_raw_touch": True,
            "no_dataset_touch": True,
            "no_runs_touch": True,
            "no_weights_touch": True,
            "no_fake_detection": True,
            "no_fake_gps": True,
            "no_fake_clearance": True,
            "cloud_vision_policy": "OPTIONAL_VALIDATOR_ONLY_NOT_REALTIME_CORE",
            "field_trial_status": "LIMITED_FIELD_TRIAL_PROTOTYPE",
        },
    }

    app = load_app()
    client = app.test_client()
    routes = route_set(app)

    required_routes = [
        "/field-capture",
        "/field-camera",
        "/api/field/session/start",
        "/api/field/session/frame",
        "/api/field/session/gps-update",
        "/api/field/session/shutter",
        "/field-map/session/<session_id>",
        "/field-spreadsheet/session/<session_id>",
        "/api/field/session/final-step2-predict",
        "/api/field/session/final-step2-status",
    ]

    optional_routes = [
        "/api/field/session/vision-analyze",
        "/field-report",
        "/field-result",
    ]

    result["route_checks"] = {r: (r in routes) for r in required_routes}
    missing_routes = [r for r in required_routes if r not in routes]
    if missing_routes:
        result["hard_failures"].append({"missing_required_routes": missing_routes})

    result["route_checks"]["optional"] = {r: (r in routes) for r in optional_routes}

    capture_status, capture_ms, capture_html = get_text(client, "/field-capture")
    add_latency_check(result, "field_capture_get", capture_ms)
    result["ui_checks"]["field_capture_http_status"] = capture_status
    result["ui_checks"]["field_capture_has_start"] = "Start" in capture_html or "start" in capture_html
    result["ui_checks"]["field_capture_not_blank"] = len(capture_html.strip()) > 100
    if capture_status in (404, 405, 500):
        result["hard_failures"].append({"field_capture_bad_http": capture_status})

    start_payload = {
        "point_id": "V001_pohon_sono",
        "operator_name": "final_step3_acceptance",
        "notes": "final_step3_field_acceptance",
        "secure_context_status": "SECURE_CONTEXT_OK",
        "current_url_mode": "HTTPS_PUBLIC_READY",
        "public_tunnel_status": "NGROK_HTTPS_TUNNEL_READY",
        "camera_status": "CAMERA_READY",
        "gps_status": "GPS_READY",
        "gps_source": "GPS_SOURCE_BROWSER",
        "base_latitude": -7.2161234,
        "base_longitude": 112.7351234,
        "base_accuracy_m": 3.8,
    }

    start_status, start_ms, start_data = post_json(client, "/api/field/session/start", start_payload)
    add_latency_check(result, "session_start_post", start_ms)
    result["request_checks"]["session_start"] = {
        "http_status": start_status,
        "elapsed_ms": start_ms,
        "data": start_data,
    }

    if start_status not in (200, 201):
        result["hard_failures"].append({"session_start_bad_http": start_status})

    session_id = ""
    if isinstance(start_data, dict):
        session_id = str(start_data.get("session_id") or "")
        camera_url = str(start_data.get("camera_url") or "")
        if not session_id:
            result["hard_failures"].append("SESSION_ID_EMPTY")
        if session_id and session_id not in camera_url:
            result["hard_failures"].append("CAMERA_URL_DOES_NOT_CONTAIN_SESSION_ID")
        if start_data.get("no_fake_detection") is not True:
            result["warnings"].append("session_start_no_fake_detection_flag_missing")
    else:
        result["hard_failures"].append("SESSION_START_NON_JSON")

    if not session_id:
        session_id = "FS_FINAL_STEP3_FALLBACK"

    camera_status, camera_ms, camera_html = get_text(client, f"/field-camera?session_id={session_id}")
    add_latency_check(result, "field_camera_get", camera_ms)
    result["ui_checks"]["field_camera_http_status"] = camera_status
    result["ui_checks"]["field_camera_has_video"] = "<video" in camera_html
    result["ui_checks"]["field_camera_has_session_id"] = session_id in camera_html or "session_id" in camera_html
    result["ui_checks"]["field_camera_yolo_first_hint"] = "YOLO" in camera_html or "progress6_27_yolo_first_lock" in camera_html

    if camera_status in (404, 405, 500):
        result["hard_failures"].append({"field_camera_bad_http": camera_status})
    if "<video" not in camera_html:
        result["hard_failures"].append("FIELD_CAMERA_VIDEO_ELEMENT_MISSING")

    frame_data_url = make_jpeg_data_url()

    # Warmup frame: tidak dihitung sebagai kontrak realtime karena ini dapat memuat model pertama kali.
    warmup_status, warmup_ms, warmup_data = post_json(
        client,
        "/api/field/session/frame",
        {
            "session_id": session_id,
            "frame_base64": frame_data_url,
            "image_base64": frame_data_url,
            "image": frame_data_url,
            "source": "final_step3_yolo_warmup_not_measured",
            "realtime_mode": "YOLO_FIRST_WARMUP",
            "synthetic_warmup": True,
            "no_fake_detection": True,
        },
    )
    result["latency_checks"]["session_frame_warmup_not_contract"] = warmup_ms
    result["request_checks"]["session_frame_warmup"] = {
        "http_status": warmup_status,
        "elapsed_ms": warmup_ms,
        "contract": "NOT_COUNTED_COLD_START_WARMUP",
        "data": warmup_data,
    }

    if warmup_status in (404, 405, 500):
        result["hard_failures"].append({"session_frame_warmup_bad_http": warmup_status})

    # Frame hot setelah warmup: ini yang harus <=1000ms.
    frame_status, frame_ms, frame_data = post_json(
        client,
        "/api/field/session/frame",
        {
            "session_id": session_id,
            "frame_base64": frame_data_url,
            "image_base64": frame_data_url,
            "image": frame_data_url,
            "source": "final_step3_field_acceptance_hot_frame",
            "realtime_mode": "YOLO_FIRST",
            "no_fake_detection": True,
            "synthetic_smoke": True,
        },
    )
    add_latency_check(result, "session_frame_post_hot_after_warmup", frame_ms)
    result["request_checks"]["session_frame"] = {
        "http_status": frame_status,
        "elapsed_ms": frame_ms,
        "contract": "MUST_BE_WITHIN_1000MS_AFTER_WARMUP",
        "data": frame_data,
    }

    if frame_status in (404, 405, 500):
        result["hard_failures"].append({"session_frame_bad_http": frame_status})
    if isinstance(frame_data, dict):
        if frame_data.get("no_fake_detection") is not True:
            result["hard_failures"].append("FRAME_NO_FAKE_DETECTION_NOT_TRUE")
        response_refresh = frame_data.get("refresh_contract_ms")
        if response_refresh is not None:
            try:
                if int(response_refresh) > LATENCY_BUDGET_MS:
                    result["hard_failures"].append("FRAME_REFRESH_CONTRACT_GT_1000MS")
            except Exception:
                result["warnings"].append("FRAME_REFRESH_CONTRACT_NOT_INTEGER")
    else:
        result["warnings"].append("FRAME_RESPONSE_NON_JSON")

    gps_status, gps_ms, gps_data = post_json(
        client,
        "/api/field/session/gps-update",
        {
            "session_id": session_id,
            "latitude": -7.2161234,
            "longitude": 112.7351234,
            "accuracy_m": 3.8,
            "gps_source": "GPS_SOURCE_BROWSER",
            "no_fake_gps": True,
        },
    )
    add_latency_check(result, "gps_update_post", gps_ms)
    result["request_checks"]["gps_update"] = {
        "http_status": gps_status,
        "elapsed_ms": gps_ms,
        "data": gps_data,
    }

    if gps_status in (404, 405, 500):
        result["hard_failures"].append({"gps_update_bad_http": gps_status})

    pred_status, pred_ms, pred_data = post_json(
        client,
        "/api/field/session/final-step2-predict",
        {
            "session_id": session_id,
            "point_id": "V001_pohon_sono",
            "clearance_m": 5.0,
            "growth_rate_m_per_day": 0.01,
            "tree_detected": True,
            "source": "final_step3_acceptance",
        },
    )
    add_latency_check(result, "final_step2_predict_post", pred_ms)
    result["request_checks"]["prediction"] = {
        "http_status": pred_status,
        "elapsed_ms": pred_ms,
        "data": pred_data,
    }

    if pred_status != 200:
        result["hard_failures"].append({"prediction_bad_http": pred_status})
    if isinstance(pred_data, dict):
        if pred_data.get("eta", {}).get("eta_days") != 200.0:
            result["hard_failures"].append("PREDICTION_5M_001_NOT_200_DAYS")
        if pred_data.get("can_claim_final_eta") is not False:
            result["hard_failures"].append("PREDICTION_FINAL_ETA_NOT_BLOCKED")
        if pred_data.get("no_fake_clearance") is not True:
            result["hard_failures"].append("PREDICTION_NO_FAKE_CLEARANCE_NOT_TRUE")
    else:
        result["hard_failures"].append("PREDICTION_RESPONSE_NON_JSON")

    shutter_status, shutter_ms, shutter_data = post_json(
        client,
        "/api/field/session/shutter",
        {
            "session_id": session_id,
            "idempotency_key": "final_step3_acceptance_once",
            "camera_status": "CAMERA_READY",
            "model_status": "TREE_MODEL_READY_CANDIDATE",
            "gps": {
                "latitude": -7.2161234,
                "longitude": 112.7351234,
                "accuracy_m": 3.8,
                "gps_source": "GPS_SOURCE_BROWSER",
            },
            "no_fake_detection": True,
            "no_fake_gps": True,
        },
    )
    result["latency_checks"]["shutter_post"] = shutter_ms
    if shutter_ms > LATENCY_BUDGET_MS:
        result["warnings"].append({
            "shutter_post_latency_note": shutter_ms,
            "reason": "Shutter writes evidence/map/spreadsheet, not realtime frame loop."
        })
    result["request_checks"]["shutter"] = {
        "http_status": shutter_status,
        "elapsed_ms": shutter_ms,
        "data": shutter_data,
    }

    if shutter_status in (404, 405, 500):
        result["hard_failures"].append({"shutter_bad_http": shutter_status})
    if isinstance(shutter_data, dict):
        if shutter_data.get("map_status") not in ("MAP_HTML_READY", "MAP_READY", None):
            result["warnings"].append({"unexpected_map_status": shutter_data.get("map_status")})
        if shutter_data.get("no_fake_detection") is not True:
            result["warnings"].append("shutter_no_fake_detection_flag_missing")
    else:
        result["warnings"].append("SHUTTER_RESPONSE_NON_JSON")

    map_status, map_ms, map_html = get_text(client, f"/field-map/session/{session_id}")
    add_latency_check(result, "map_get", map_ms)
    result["request_checks"]["map"] = {
        "http_status": map_status,
        "elapsed_ms": map_ms,
        "preview": map_html[:500],
    }
    if map_status in (404, 405, 500):
        result["hard_failures"].append({"map_bad_http": map_status})

    sheet_status, sheet_ms, sheet_html = get_text(client, f"/field-spreadsheet/session/{session_id}")
    add_latency_check(result, "spreadsheet_get", sheet_ms)
    result["request_checks"]["spreadsheet"] = {
        "http_status": sheet_status,
        "elapsed_ms": sheet_ms,
        "preview": sheet_html[:500],
    }
    if sheet_status in (404, 405, 500):
        result["hard_failures"].append({"spreadsheet_bad_http": sheet_status})

    result["final_report_lock"] = {
        "allowed_claims": [
            "Sistem prototipe monitoring vegetasi jaringan distribusi 20 kV berbasis HP browser, Flask backend, HTTPS tunnel, YOLO-first runtime, GPS evidence, map evidence, dan spreadsheet-ready output.",
            "Sistem siap untuk limited field trial, bukan produksi final.",
            "Deteksi pohon_sono masih candidate detection.",
            "Prediksi clearance dan ETA bersifat provisional jika memakai input manual atau growth proxy.",
            "Kontrak realtime frame dipatok 1000 ms setelah YOLO warmup; cold-start tidak dihitung sebagai frame loop aktif.",
        ],
        "forbidden_claims": [
            "Tidak boleh mengklaim sistem produksi final PLN.",
            "Tidak boleh mengklaim clearance final tanpa pole, conductor, dan reference geometry yang sah.",
            "Tidak boleh mengklaim ETA final tanpa clearance final.",
            "Tidak boleh mengklaim growth biologis final karena dataset growth masih proxy.",
            "Tidak boleh menjadikan cloud vision sebagai realtime core.",
            "Tidak boleh mengklaim GPS sebagai pengukur pixel-to-meter.",
        ],
        "final_status_wording": "SYSTEM_FINAL_READY_FOR_LIMITED_FIELD_TRIAL_AND_REPORT",
    }

    if result["hard_failures"]:
        result["status"] = "SYSTEM_FINAL_FIELD_ACCEPTANCE_REPORT_LOCK_FAILED"
        code = 1
    else:
        result["status"] = "SYSTEM_FINAL_READY_FOR_LIMITED_FIELD_TRIAL_AND_REPORT"
        code = 0

    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
