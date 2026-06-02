"""Flask route registration for browser-based field capture."""

from __future__ import annotations

from pathlib import Path

from .field_capture import accept_field_capture_upload, load_field_capture_job, load_field_capture_result
from .latency_monitor import ping_latency
from .network_mode import describe_network_modes


def register_field_capture_routes(app) -> None:
    from flask import jsonify, redirect, render_template, request

    @app.get("/field-capture")
    def field_capture_page():
        return render_template("field_capture.html")

    @app.get("/mobile")
    def legacy_mobile_alias():
        return redirect("/field-capture", code=302)

    @app.post("/api/field-capture/upload")
    def field_capture_upload():
        runtime = Path(app.config["ULP_RUNTIME_ROOT"])
        result = accept_field_capture_upload(
            dict(request.form),
            image_file=request.files.get("image"),
            video_file=request.files.get("video"),
            runtime_root=runtime,
        )
        return jsonify(result), 202

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
        return jsonify(ping_latency())

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
        result = accept_field_capture_upload(
            dict(request.form),
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
