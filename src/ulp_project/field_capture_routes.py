"""Flask route registration for browser-based field capture."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from .field_capture import accept_field_capture_upload, load_field_capture_job, load_field_capture_result
from .latency_monitor import ping_latency
from .network_mode import describe_network_modes
from .realtime_streaming import (
    create_realtime_session,
    get_session_status,
    latest_realtime_result,
    process_realtime_frame,
    validate_session_token,
    websocket_available,
    write_realtime_snapshot_report,
)
from .yolo_model_resolver import resolve_yolo_model


def register_field_capture_routes(app) -> None:
    from flask import jsonify, redirect, render_template, request

    @app.get("/field-capture")
    def field_capture_page():
        return render_template("field_capture.html")

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
