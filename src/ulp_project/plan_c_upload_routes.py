"""Upload image mode routes for Plan C."""

from __future__ import annotations

from typing import Any

from .plan_c_ai_model_runtime import get_plan_c_ai_model_status
from .plan_c_storage import read_json, redact_for_display, relative_to_project, session_file
from .plan_c_upload_processor import build_upload_status, process_upload_session
from .plan_c_upload_storage import create_upload_session, load_upload_metadata

try:
    from flask import jsonify, render_template, request, send_file
except ImportError:  # pragma: no cover
    jsonify = None
    render_template = None
    request = None
    send_file = None


def register_plan_c_upload_routes(plan_c_bp: Any) -> None:
    if getattr(plan_c_bp, "_plan_c_upload_routes_registered", False):
        return
    plan_c_bp._plan_c_upload_routes_registered = True

    @plan_c_bp.get("/plan-c/upload")
    def plan_c_upload_page():
        return render_template("plan_c_upload.html")

    @plan_c_bp.get("/plan-c/upload/review/<session_id>")
    def plan_c_upload_review_page(session_id: str):
        metadata = load_upload_metadata(session_id)
        return render_template(
            "plan_c_upload_review.html",
            session_id=session_id,
            metadata=metadata,
            model_status=get_plan_c_ai_model_status(),
            original_exists=session_file(session_id, "original.jpg").exists(),
        )

    @plan_c_bp.get("/plan-c/upload/result/<session_id>")
    def plan_c_upload_result_page(session_id: str):
        metadata = load_upload_metadata(session_id)
        result = read_json(session_file(session_id, "result.json"), default={}) or {}
        return render_template(
            "plan_c_upload_result.html",
            session_id=session_id,
            metadata=metadata,
            result=result,
            result_ready=bool(result),
            annotated_exists=session_file(session_id, "annotated.jpg").exists(),
        )

    @plan_c_bp.get("/plan-c/upload/developer/<session_id>")
    def plan_c_upload_developer_page(session_id: str):
        files = {
            "metadata": read_json(session_file(session_id, "metadata.json"), default={}),
            "result": read_json(session_file(session_id, "result.json"), default={}),
            "developer": read_json(session_file(session_id, "developer.json"), default={}),
            "ai_model_raw": read_json(session_file(session_id, "ai_model_raw.json"), default={}),
            "yolo_raw": read_json(session_file(session_id, "yolo_raw.json"), default={}),
            "ai_raw": read_json(session_file(session_id, "ai_raw.json"), default={}),
            "geometry": read_json(session_file(session_id, "geometry.json"), default={}),
            "growth": read_json(session_file(session_id, "growth.json"), default={}),
        }
        file_paths = {
            "metadata": session_file(session_id, "metadata.json"),
            "result": session_file(session_id, "result.json"),
            "developer": session_file(session_id, "developer.json"),
            "ai_model_raw": session_file(session_id, "ai_model_raw.json"),
            "yolo_raw": session_file(session_id, "yolo_raw.json"),
            "ai_raw": session_file(session_id, "ai_raw.json"),
            "geometry": session_file(session_id, "geometry.json"),
            "growth": session_file(session_id, "growth.json"),
            "original": session_file(session_id, "original.jpg"),
            "annotated": session_file(session_id, "annotated.jpg"),
        }
        return render_template(
            "plan_c_upload_developer.html",
            session_id=session_id,
            files=redact_for_display(files),
            file_paths={key: relative_to_project(path) for key, path in file_paths.items()},
            model_status=redact_for_display(get_plan_c_ai_model_status()),
        )

    @plan_c_bp.get("/plan-c/upload/session/<session_id>/<image_name>")
    def plan_c_upload_image(session_id: str, image_name: str):
        if image_name not in {"original.jpg", "annotated.jpg"}:
            return "", 404
        path = session_file(session_id, image_name)
        if not path.exists():
            return "", 404
        return send_file(path, mimetype="image/jpeg", conditional=False)

    @plan_c_bp.post("/api/plan-c/upload/start")
    def api_plan_c_upload_start():
        image_file = request.files.get("image") or request.files.get("file") or request.files.get("upload")
        result = create_upload_session(image_file, dict(request.form))
        status_code = int(result.pop("http_status", 201 if result.get("ok") else 400))
        return jsonify(result), status_code

    @plan_c_bp.post("/api/plan-c/upload/process/<session_id>")
    def api_plan_c_upload_process(session_id: str):
        result = process_upload_session(session_id)
        status_code = int(result.pop("http_status", 200 if result.get("ok") else 400))
        return jsonify(result), status_code

    @plan_c_bp.get("/api/plan-c/upload/status/<session_id>")
    def api_plan_c_upload_status(session_id: str):
        status = build_upload_status(session_id)
        return jsonify(status), 200 if status.get("ok") else 404

    @plan_c_bp.get("/api/plan-c/upload/result/<session_id>")
    def api_plan_c_upload_result(session_id: str):
        result = read_json(session_file(session_id, "result.json"), default={}) or {}
        if not result:
            return jsonify({"ok": True, "session_id": session_id, "result_ready": False, "status": "UPLOAD_ACCEPTED_DETECTION_PENDING"}), 200
        return jsonify({"ok": True, "result_ready": True, **result}), 200
