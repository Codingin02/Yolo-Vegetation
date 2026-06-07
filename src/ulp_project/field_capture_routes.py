"""Flask route registration for browser-based field capture."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from .calibration_readiness import check_calibration_readiness
from .field_capture import accept_field_capture_upload, load_field_capture_job, load_field_capture_result
from .field_acceptance_runtime import (
    acceptance_evidence,
    acceptance_status,
    latest_acceptance,
    start_acceptance,
    submit_acceptance,
)
from .field_session_runtime import (
    build_latest_result,
    field_session_spreadsheet,
    latest_field_session_map,
    latest_field_session_report,
    log_session_exception,
    process_field_session_frame,
    record_manual_input,
    render_field_session_spreadsheet_html,
    session_status,
    shutter_field_session,
    start_field_session,
    stop_field_session,
    update_field_session_gps,
)
from .field_trial_evidence import build_field_trial_evidence_pack, record_hp_result
from .growth_prediction_runtime import growth_prior_sample, growth_prior_status, predict_growth_prior
from .latency_monitor import ping_latency
from .model_handoff import check_model_handoff
from .network_mode import describe_network_modes
from .ngrok_runtime_probe import probe_ngrok_runtime
from .operator_failure_recovery import build_failure_recovery
from .paths import PROJECT_ROOT
from .phase5_2_field_trial import (
    build_manual_prediction,
    phase5_2_runtime_contract_status,
    write_field_trial_snapshot_report,
)
from .progress5_4_field_runtime import (
    latest_progress5_4_gps_status,
    latest_progress5_4_map,
    latest_progress5_4_measurement,
    latest_progress5_4_report,
    process_progress5_4_realtime_frame,
    progress5_4_calibration_status,
    progress5_4_realtime_status,
    write_progress5_4_shutter_capture,
)
from .realtime_streaming import (
    create_realtime_session,
    get_session_status,
    latest_realtime_result,
    process_realtime_frame,
    validate_session_token,
    websocket_available,
    write_realtime_snapshot_report,
)
from .runtime_links import build_public_links, build_secure_context_diagnostic
from .realtime_yolo_detection_pipeline import model_readiness_status
from .yolo_model_resolver import resolve_yolo_model

REQUIRED_PROGRESS6_8_ROUTES = {
    "/api/field/session/start": "POST",
    "/api/field/session/frame": "POST",
    "/api/field/session/gps-update": "POST",
    "/api/field/session/shutter": "POST",
    "/field-camera": "GET",
    "/field-capture": "GET",
    "/field-map/session/<session_id>": "GET",
    "/field-spreadsheet/session/<session_id>": "GET",
}


def register_field_capture_routes(app) -> None:
    from flask import jsonify, redirect, render_template, request, send_from_directory

    @app.after_request
    def progress6_8_static_cache_control(response):
        if request.path.startswith("/static/"):
            response.headers["Cache-Control"] = "no-store, max-age=0, must-revalidate"
        return response

    @app.get("/field-capture")
    def field_capture_page():
        return render_template("field_capture.html")

    @app.get("/field-camera")
    def field_camera_page():
        return render_template("field_camera.html")

    @app.get("/field-trial-checklist")
    def field_trial_checklist_page():
        return render_template("field_trial_checklist.html")

    @app.get("/field-report")
    def field_report_page():
        return render_template("field_report.html")

    @app.get("/field-result")
    def field_result_page():
        return render_template("field_result.html")

    @app.get("/field-manual-input")
    def field_manual_input_page():
        return render_template("field_manual_input.html")

    @app.get("/field-acceptance")
    def field_acceptance_page():
        return render_template("field_acceptance.html")

    @app.get("/realtime")
    def realtime_alias():
        return render_template("field_capture.html")

    @app.get("/mobile")
    def legacy_mobile_alias():
        return redirect("/field-capture", code=302)

    @app.post("/api/field-capture/upload")
    def field_capture_upload():
        runtime = Path(app.config["ULP_RUNTIME_ROOT"])
        payload = request.get_json(silent=True) if request.is_json else None
        form_payload = dict(payload or request.form)
        result = accept_field_capture_upload(
            form_payload,
            image_file=request.files.get("image"),
            video_file=request.files.get("video"),
            runtime_root=runtime,
        )
        return jsonify(result), 202 if result.get("status") == "INSUFFICIENT_DATA" else 200

    @app.get("/api/field-capture/job/<job_id>")
    def field_capture_job(job_id: str):
        runtime = Path(app.config["ULP_RUNTIME_ROOT"])
        return jsonify(load_field_capture_job(job_id, runtime))

    @app.get("/api/field-capture/result/<job_id>")
    def field_capture_result(job_id: str):
        runtime = Path(app.config["ULP_RUNTIME_ROOT"])
        return jsonify(load_field_capture_result(job_id, runtime))

    @app.get("/api/field-capture/ping")
    def field_capture_ping():
        network = _network_payload(request)
        return jsonify({**network, **ping_latency(), "network_status": network["status"]})

    @app.get("/api/latency/ping")
    def field_capture_latency_ping():
        network = _network_payload(request)
        return jsonify({**network, **ping_latency(), "network_status": network["status"]})

    @app.get("/api/network/whoami")
    def field_capture_whoami():
        return jsonify({"status": "NETWORK_WHOAMI_READY", **_network_payload(request)})

    @app.get("/api/network/health")
    def field_capture_network_health():
        return jsonify({"status": "NETWORK_HEALTH_READY", **_network_payload(request)})

    @app.get("/api/runtime/public-links")
    def runtime_public_links():
        return jsonify(build_public_links(port=_request_port(request), public_url=request.args.get("public_url")))

    @app.get("/api/runtime/tunnel-status")
    def runtime_tunnel_status():
        return jsonify(probe_ngrok_runtime(port=_request_port(request)))

    @app.get("/api/runtime/status")
    def runtime_status():
        links = build_public_links(port=_request_port(request), public_url=request.args.get("public_url"))
        secure_context = _secure_context_payload(request)
        return jsonify(
            {
                **phase5_2_runtime_contract_status(),
                "runtime_root": app.config["ULP_RUNTIME_ROOT"],
                "public_links": links,
                "tunnel_status": links.get("tunnel_status"),
                "public_url_status": links.get("public_url_status"),
                "current_url_mode": secure_context["current_url_mode"],
                "secure_context_status": secure_context["secure_context_status"],
                "recommended_url": secure_context.get("recommended_url"),
                "lan_http_warning": secure_context.get("lan_http_warning"),
                "websocket": websocket_available(),
                "operator_note": "Field trial prototype; HP is browser client only, laptop is processing server.",
            }
        )

    @app.get("/api/runtime/secure-context-diagnostic")
    def runtime_secure_context_diagnostic():
        return jsonify(_secure_context_payload(request))

    @app.get("/api/runtime/ui-version")
    def runtime_ui_version():
        return jsonify({"status": "UI_VERSION_READY", "ui_version": "progress6_8", "camera_first_ui": True})

    @app.get("/api/runtime/route-registry")
    def runtime_route_registry():
        routes = _route_registry_payload(app)
        return jsonify(routes)

    @app.get("/api/runtime/camera-diagnostic-contract")
    def runtime_camera_diagnostic_contract():
        return jsonify(
            {
                "status": "CAMERA_DIAGNOSTIC_CONTRACT_READY",
                "frontend_permission_source": "BROWSER_DOMEXCEPTION",
                "error_codes": [
                    "CAMERA_PERMISSION_DENIED",
                    "CAMERA_NOT_FOUND",
                    "CAMERA_CONSTRAINT_FAILED",
                    "CAMERA_NOT_READABLE",
                    "CAMERA_INSECURE_CONTEXT",
                    "CAMERA_UNKNOWN_ERROR",
                ],
                "lens_selection": "BROWSER_ENUMERATE_DEVICES_AFTER_PERMISSION",
                "no_forced_ultrawide_default": True,
            }
        )

    @app.get("/api/runtime/yolo-readiness")
    def runtime_yolo_readiness():
        return jsonify(model_readiness_status())

    @app.get("/api/model/status")
    def model_status():
        return jsonify(check_model_handoff())

    @app.get("/api/growth-prior/status")
    def growth_prior_status_route():
        return jsonify(growth_prior_status())

    @app.post("/api/growth-prior/predict")
    def growth_prior_predict_route():
        payload = request.get_json(silent=True) if request.is_json else None
        return jsonify(predict_growth_prior(dict(payload or request.form)))

    @app.get("/api/growth-prior/sample")
    def growth_prior_sample_route():
        return jsonify(growth_prior_sample(request.args.get("point_id") or "V001_pohon_sono"))

    @app.get("/api/calibration/status")
    def calibration_status():
        return jsonify(check_calibration_readiness({}))

    @app.post("/api/field/manual-prediction")
    def field_manual_prediction():
        payload = request.get_json(silent=True) if request.is_json else None
        return jsonify(build_manual_prediction(dict(payload or request.form)))

    @app.post("/api/field/snapshot-report")
    def field_snapshot_report():
        payload = request.get_json(silent=True) if request.is_json else None
        result = write_field_trial_snapshot_report(dict(payload or request.form))
        return jsonify(result), 200 if result.get("report_written") else 202

    @app.get("/api/field/realtime-status")
    def field_progress5_4_realtime_status():
        return jsonify(progress5_4_realtime_status())

    @app.get("/api/field/session/status")
    def field_session_status_route():
        return jsonify(session_status(request.args.get("session_id")))

    @app.post("/api/field/session/start")
    def field_session_start_route():
        payload = request.get_json(silent=True) if request.is_json else None
        runtime = Path(app.config["ULP_RUNTIME_ROOT"])
        try:
            return jsonify(start_field_session(dict(payload or request.form), runtime_root=runtime)), 201
        except Exception as exc:  # pragma: no cover - defensive live route guard
            logged = log_session_exception(exc, route="/api/field/session/start", runtime_root=runtime)
            return jsonify(
                {
                    **logged,
                    "ok": False,
                    "status": "FIELD_SESSION_START_FAILED",
                    "error_code": "FIELD_SESSION_START_EXCEPTION_CAUGHT",
                    "degraded": True,
                    "message": "Session start gagal dalam guard aman. Kamera tidak dibuka dari session degraded.",
                    "session_id": "",
                    "camera_url": None,
                    "map_enabled": False,
                    "result_enabled": False,
                    "shutter_required": True,
                    "recording_status": "RECORDING_STOPPED",
                    "model_status": "MODEL_NOT_READY",
                    "no_fake_detection": True,
                }
            ), 202

    @app.post("/api/field/session/stop")
    def field_session_stop_route():
        payload = request.get_json(silent=True) if request.is_json else None
        runtime = Path(app.config["ULP_RUNTIME_ROOT"])
        try:
            return jsonify(stop_field_session(dict(payload or request.form), runtime_root=runtime))
        except Exception as exc:  # pragma: no cover - defensive live route guard
            logged = log_session_exception(exc, route="/api/field/session/stop", runtime_root=runtime)
            return jsonify(
                {
                    **logged,
                    "status": "NO_ACTIVE_SESSION_TO_STOP",
                    "error_code": "FIELD_SESSION_STOP_EXCEPTION_CAUGHT",
                    "message": "Stop record ditutup aman tanpa membuat data palsu.",
                    "recording_status": "RECORDING_STOPPED",
                    "no_fake_detection": True,
                }
            ), 200

    @app.post("/api/field/session/gps-update")
    def field_session_gps_update_route():
        payload = request.get_json(silent=True) if request.is_json else None
        runtime = Path(app.config["ULP_RUNTIME_ROOT"])
        try:
            result = update_field_session_gps(dict(payload or request.form), runtime_root=runtime)
            status_code = int(result.pop("http_status", 200))
            return jsonify(result), status_code
        except Exception as exc:  # pragma: no cover - live guard
            logged = log_session_exception(exc, route="/api/field/session/gps-update", runtime_root=runtime)
            return jsonify(
                {
                    **logged,
                    "status": "GPS_INVALID_SAFE",
                    "error_code": "FIELD_SESSION_GPS_UPDATE_EXCEPTION_CAUGHT",
                    "session_id": str((payload or {}).get("session_id") or ""),
                    "no_fake_gps": True,
                    "no_fake_detection": True,
                }
            ), 202

    @app.post("/api/field/session/frame")
    def field_session_frame_route():
        payload = request.get_json(silent=True) or {}
        runtime = Path(app.config["ULP_RUNTIME_ROOT"])
        try:
            result = process_field_session_frame(dict(payload), runtime_root=runtime)
            status_code = int(result.pop("http_status", 200))
            return jsonify(result), status_code
        except Exception as exc:  # pragma: no cover - live guard
            logged = log_session_exception(exc, route="/api/field/session/frame", runtime_root=runtime)
            return jsonify(
                {
                    **logged,
                    "status": "TREE_MODEL_INFERENCE_FAILED_SAFE",
                    "error_code": "FIELD_SESSION_FRAME_EXCEPTION_CAUGHT",
                    "session_id": str(payload.get("session_id") or ""),
                    "detections": [],
                    "detected_classes": [],
                    "no_fake_detection": True,
                }
            ), 202

    @app.post("/api/field/session/shutter")
    def field_session_shutter_route():
        payload = request.get_json(silent=True) if request.is_json else None
        runtime = Path(app.config["ULP_RUNTIME_ROOT"])
        try:
            result = shutter_field_session(dict(payload or request.form), runtime_root=runtime)
            status_code = int(result.pop("http_status", 200))
            return jsonify(result), status_code
        except Exception as exc:  # pragma: no cover - defensive live route guard
            logged = log_session_exception(exc, route="/api/field/session/shutter", runtime_root=runtime)
            return jsonify(
                {
                    **logged,
                    "status": "FIELD_SESSION_SHUTTER_DEGRADED_NOT_SAVED",
                    "error_code": "FIELD_SESSION_SHUTTER_EXCEPTION_CAUGHT",
                    "message": "Shutter tidak disimpan karena error terkontrol; CSV tidak di-append.",
                    "session_id": str((payload or {}).get("session_id") or ""),
                    "csv_appended": False,
                    "duplicate_ignored": False,
                    "model_status": "MODEL_NOT_READY",
                    "no_fake_detection": True,
                }
            ), 202

    @app.get("/api/field/session/<session_id>/spreadsheet")
    def field_session_spreadsheet_api(session_id: str):
        runtime = Path(app.config["ULP_RUNTIME_ROOT"])
        return jsonify(field_session_spreadsheet(session_id, runtime_root=runtime))

    @app.get("/field-spreadsheet/session/<session_id>")
    def field_session_spreadsheet_page(session_id: str):
        runtime = Path(app.config["ULP_RUNTIME_ROOT"])
        return render_field_session_spreadsheet_html(session_id, runtime_root=runtime)

    @app.post("/api/field/realtime-frame")
    def field_progress5_4_realtime_frame():
        payload = request.get_json(silent=True) or {}
        runtime = Path(app.config["ULP_RUNTIME_ROOT"])
        return jsonify(process_progress5_4_realtime_frame(dict(payload), runtime_root=runtime, debug_coco=False))

    @app.post("/api/field/debug-coco-frame")
    def field_progress5_4_debug_coco_frame():
        payload = request.get_json(silent=True) or {}
        runtime = Path(app.config["ULP_RUNTIME_ROOT"])
        return jsonify(process_progress5_4_realtime_frame(dict(payload), runtime_root=runtime, debug_coco=True))

    @app.post("/api/field/shutter-capture")
    def field_progress5_4_shutter_capture():
        payload = request.get_json(silent=True) if request.is_json else None
        runtime = Path(app.config["ULP_RUNTIME_ROOT"])
        return jsonify(write_progress5_4_shutter_capture(dict(payload or request.form), runtime_root=runtime))

    @app.get("/api/field/latest-measurement")
    def field_progress5_4_latest_measurement():
        return jsonify(latest_progress5_4_measurement())

    @app.get("/api/field/report-latest")
    def field_progress5_4_report_latest():
        return jsonify(latest_progress5_4_report())

    @app.get("/api/field/latest-report")
    def field_progress5_4_latest_report_alias():
        latest = latest_field_session_report(request.args.get("session_id"))
        if request.args.get("session_id"):
            return jsonify(latest)
        if latest.get("status") == "NO_FIELD_SESSION_REPORT_YET":
            return jsonify({**latest_progress5_4_report(), "field_session": latest})
        return jsonify(latest)

    @app.get("/api/field/latest-result")
    def field_session_latest_result_route():
        return jsonify(build_latest_result(request.args.get("session_id")))

    @app.get("/api/field/map-latest")
    def field_progress5_4_map_latest():
        return jsonify(latest_progress5_4_map())

    @app.get("/api/field/latest-map")
    def field_progress5_4_latest_map_alias():
        runtime = Path(app.config["ULP_RUNTIME_ROOT"])
        latest = latest_field_session_map(request.args.get("session_id"), runtime_root=runtime)
        if request.args.get("session_id"):
            return jsonify(latest)
        return jsonify(latest)

    @app.get("/api/field/session/<session_id>/map")
    def field_session_specific_map_api(session_id: str):
        runtime = Path(app.config["ULP_RUNTIME_ROOT"])
        return jsonify(latest_field_session_map(session_id, runtime_root=runtime))

    @app.get("/field-map/session/<session_id>")
    def field_session_specific_map_page(session_id: str):
        runtime = Path(app.config["ULP_RUNTIME_ROOT"])
        latest = latest_field_session_map(session_id, runtime_root=runtime)
        path = Path(str(latest.get("path") or ""))
        if path.exists():
            return send_from_directory(path.parent, path.name, as_attachment=False)
        return jsonify(latest), 404

    @app.get("/api/field/gps-status")
    def field_progress5_4_gps_status():
        return jsonify(latest_progress5_4_gps_status())

    @app.get("/api/field/calibration-status")
    def field_progress5_4_calibration_status():
        return jsonify(progress5_4_calibration_status())

    @app.post("/api/field-trial/hp-result")
    def field_trial_hp_result():
        payload = request.get_json(silent=True) if request.is_json else None
        runtime = Path(app.config["ULP_RUNTIME_ROOT"])
        result = record_hp_result(dict(payload or request.form), evidence_dir=runtime / "field_trial_evidence")
        return jsonify(result), 201

    @app.post("/api/field/manual-input")
    def field_manual_input_route():
        payload = request.get_json(silent=True) if request.is_json else None
        runtime = Path(app.config["ULP_RUNTIME_ROOT"])
        return jsonify(record_manual_input(dict(payload or request.form), runtime_root=runtime)), 201

    @app.post("/api/field/acceptance/start")
    def field_acceptance_start_route():
        payload = request.get_json(silent=True) if request.is_json else None
        runtime = Path(app.config["ULP_RUNTIME_ROOT"])
        return jsonify(start_acceptance(dict(payload or request.form), runtime_root=runtime)), 201

    @app.post("/api/field/acceptance/submit")
    def field_acceptance_submit_route():
        payload = request.get_json(silent=True) if request.is_json else None
        runtime = Path(app.config["ULP_RUNTIME_ROOT"])
        return jsonify(submit_acceptance(dict(payload or request.form), runtime_root=runtime))

    @app.get("/api/field/acceptance/latest")
    def field_acceptance_latest_route():
        return jsonify(latest_acceptance())

    @app.get("/api/field/acceptance/evidence")
    def field_acceptance_evidence_route():
        return jsonify(acceptance_evidence())

    @app.get("/api/field/acceptance/status")
    def field_acceptance_status_route():
        return jsonify(acceptance_status())

    @app.get("/api/field-trial/evidence")
    def field_trial_evidence():
        runtime = Path(app.config["ULP_RUNTIME_ROOT"])
        dry_run = str(request.args.get("dry_run", "")).lower() in {"1", "true", "yes"}
        return jsonify(build_field_trial_evidence_pack(evidence_dir=runtime / "field_trial_evidence", dry_run=dry_run, port=_request_port(request)))

    @app.post("/api/operator/failure-recovery")
    def operator_failure_recovery():
        payload = request.get_json(silent=True) if request.is_json else None
        return jsonify(build_failure_recovery(dict(payload or request.form)))

    @app.get("/field-reports/<path:filename>")
    def field_reports(filename: str):
        return send_from_directory(PROJECT_ROOT / "outputs" / "reports", filename, as_attachment=False)

    @app.get("/field-maps/<path:filename>")
    def field_maps(filename: str):
        runtime_map = Path(app.config["ULP_RUNTIME_ROOT"]) / "field_maps" / filename
        if runtime_map.exists():
            return send_from_directory(runtime_map.parent, runtime_map.name, as_attachment=False)
        data_map = PROJECT_ROOT / "data" / "runtime" / "field_maps" / filename
        if data_map.exists():
            return send_from_directory(data_map.parent, data_map.name, as_attachment=False)
        return send_from_directory(PROJECT_ROOT / "outputs" / "maps", filename, as_attachment=False)

    @app.get("/favicon.ico")
    def favicon_no_content():
        return "", 204

    @app.get("/api/mobile/network/status")
    def legacy_mobile_network_alias():
        return jsonify(
            {
                "status": "FIELD_CAPTURE_NETWORK_MODES_READY",
                "modes": describe_network_modes(),
                "secret_policy": "env_only",
                "legacy_alias": "/api/field-capture/ping",
            }
        )

    @app.post("/api/mobile/upload-inspection")
    def legacy_mobile_upload_alias():
        runtime = Path(app.config["ULP_RUNTIME_ROOT"])
        payload = request.get_json(silent=True) if request.is_json else None
        form_payload = dict(payload or request.form)
        result = accept_field_capture_upload(
            form_payload,
            image_file=request.files.get("image"),
            video_file=request.files.get("video"),
            runtime_root=runtime,
        )
        result["legacy_alias"] = "/api/field-capture/upload"
        return jsonify(result), 202

    @app.get("/api/mobile/job/<job_id>")
    def legacy_mobile_job_alias(job_id: str):
        runtime = Path(app.config["ULP_RUNTIME_ROOT"])
        return jsonify(load_field_capture_job(job_id, runtime))

    @app.get("/api/mobile/result/<job_id>")
    def legacy_mobile_result_alias(job_id: str):
        runtime = Path(app.config["ULP_RUNTIME_ROOT"])
        return jsonify(load_field_capture_result(job_id, runtime))

    @app.get("/api/realtime/session/new")
    def realtime_session_new():
        runtime = Path(app.config["ULP_RUNTIME_ROOT"])
        return jsonify(create_realtime_session(runtime))

    @app.get("/api/realtime/session/status/<session_id>")
    def realtime_session_status(session_id: str):
        return jsonify(get_session_status(session_id))

    @app.get("/api/realtime/model/status")
    def realtime_model_status():
        return jsonify({**resolve_yolo_model(), "transport": websocket_available()})

    @app.get("/api/realtime/latest-result/<session_id>")
    def realtime_latest_result(session_id: str):
        return jsonify(latest_realtime_result(session_id))

    @app.post("/api/realtime/frame")
    def realtime_frame_fallback():
        payload = request.get_json(silent=True) or {}
        result = process_realtime_frame(payload, demo_mock=bool(payload.get("demo_mock")), write_report=False)
        return jsonify(result), 202 if result.get("status") in {"FRAME_RATE_LIMITED", "STALE_FRAME_DROPPED"} else 200

    @app.post("/api/realtime/report-snapshot")
    def realtime_report_snapshot():
        payload = request.get_json(silent=True) or {}
        session_id = str(payload.get("session_id", ""))
        if not validate_session_token(session_id, payload.get("session_token")):
            return jsonify({"status": "REALTIME_SESSION_TOKEN_INVALID", "report_written": False}), 403
        return jsonify(write_realtime_snapshot_report(session_id, report_trigger=str(payload.get("report_trigger") or "operator_snapshot")))

    _register_realtime_websocket(app)


def _network_payload(request) -> dict[str, object]:
    return {
        "server_time": datetime.now().isoformat(),
        "client_ip": request.headers.get("X-Forwarded-For", request.remote_addr or ""),
        "server_host": request.host.split(":")[0],
        "server_port": request.host.split(":")[1] if ":" in request.host else "",
        "status": "OK",
    }


def _request_port(request) -> int:
    try:
        if ":" in request.host:
            return int(request.host.rsplit(":", 1)[1])
    except (TypeError, ValueError):
        pass
    return 5000


def _secure_context_payload(request) -> dict[str, object]:
    return build_secure_context_diagnostic(
        host=request.host,
        scheme=request.scheme,
        forwarded_proto=request.headers.get("X-Forwarded-Proto", ""),
        port=_request_port(request),
        public_url=request.args.get("public_url"),
    )


def _route_registry_payload(app) -> dict[str, object]:
    route_methods: dict[str, set[str]] = {}
    routes: list[dict[str, object]] = []
    for rule in app.url_map.iter_rules():
        methods = sorted(method for method in rule.methods if method not in {"HEAD", "OPTIONS"})
        route_methods.setdefault(rule.rule, set()).update(methods)
        routes.append({"rule": rule.rule, "methods": methods, "endpoint": rule.endpoint})
    required = {
        route: method in route_methods.get(route, set())
        for route, method in REQUIRED_PROGRESS6_8_ROUTES.items()
    }
    return {
        "status": "ROUTE_REGISTRY_READY" if all(required.values()) else "ROUTE_REGISTRY_BROKEN",
        "routes": sorted(routes, key=lambda item: str(item["rule"])),
        "required_routes": required,
        "required_methods": REQUIRED_PROGRESS6_8_ROUTES,
        "missing_routes": [route for route, ok in required.items() if not ok],
    }


def _register_realtime_websocket(app) -> None:
    from flask import jsonify, request

    try:
        from flask_sock import Sock
    except ImportError:
        @app.get("/ws/realtime-detect")
        def realtime_websocket_dependency_missing():
            return jsonify(websocket_available())

        return

    sock = Sock(app)

    @sock.route("/ws/realtime-detect")
    def realtime_detect_socket(ws):  # pragma: no cover - exercised manually with flask-sock installed
        import json

        while True:
            message = ws.receive()
            if message is None:
                break
            try:
                payload = json.loads(message) if isinstance(message, str) else {}
            except json.JSONDecodeError:
                ws.send(json.dumps({"status": "WEBSOCKET_PAYLOAD_INVALID_JSON"}))
                continue
            result = process_realtime_frame(payload, demo_mock=bool(payload.get("demo_mock")), write_report=False)
            ws.send(json.dumps(result, ensure_ascii=False))
