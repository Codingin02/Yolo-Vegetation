"""Flask blueprint for Progress 8 Plan C snapshot processing."""

from __future__ import annotations

from typing import Any

from .plan_c_feedback_learning import save_operator_feedback
from .plan_c_free_vision_detector import build_free_vision_status_payload
from .plan_c_map import load_plan_c_map_payload
from .plan_c_processor import process_plan_c_snapshot
from .plan_c_session import build_session_status, create_plan_c_session, load_plan_c_metadata, save_tree_anchor
from .plan_c_storage import PLAN_C_UI_VERSION, read_json, redact_for_display, relative_to_project, session_file

try:
    from flask import Blueprint, jsonify, render_template, request, send_file
except ImportError:  # pragma: no cover
    Blueprint = None
    jsonify = None
    render_template = None
    request = None
    send_file = None


if Blueprint is not None:
    plan_c_bp = Blueprint("plan_c", __name__)
else:  # pragma: no cover
    plan_c_bp = None


def register_plan_c_routes(app: Any) -> None:
    if plan_c_bp is None:
        raise RuntimeError("FLASK_NOT_INSTALLED_FOR_PLAN_C")
    if "plan_c.home" not in app.view_functions:
        app.register_blueprint(plan_c_bp)


@plan_c_bp.get("/plan-c")
def home():
    return render_template("plan_c_home.html")


@plan_c_bp.get("/plan-c/capture/<session_id>")
def capture(session_id: str):
    metadata = load_plan_c_metadata(session_id)
    return render_template("plan_c_capture.html", session_id=session_id, metadata=metadata)


@plan_c_bp.get("/plan-c/processing/<session_id>")
def processing(session_id: str):
    return render_template("plan_c_processing.html", session_id=session_id)


@plan_c_bp.get("/plan-c/result/<session_id>")
def result_page(session_id: str):
    result = read_json(session_file(session_id, "result.json"), default={}) or {}
    metadata = load_plan_c_metadata(session_id)
    result_ready = bool(result)
    if not result_ready:
        result = {
            "status": "PLAN_C_PROCESSING",
            "session_id": session_id,
            "risk_status": "DATA_TIDAK_CUKUP",
            "prediction_window": "data tidak cukup",
            "manual_review_required": True,
            "links": {"processing": f"/plan-c/processing/{session_id}", "developer": f"/plan-c/developer/{session_id}", "map": "/plan-c/map"},
        }
    annotated_path = session_file(session_id, "annotated.jpg")
    return render_template(
        "plan_c_result.html",
        session_id=session_id,
        result=result,
        metadata=metadata,
        result_ready=result_ready,
        annotated_exists=annotated_path.exists(),
    ), 200


@plan_c_bp.get("/plan-c/map")
def map_page():
    payload = load_plan_c_map_payload()
    return render_template("plan_c_map.html", map_payload=payload)


@plan_c_bp.get("/plan-c/developer/<session_id>")
def developer_page(session_id: str):
    files = {
        "metadata": read_json(session_file(session_id, "metadata.json"), default={}),
        "result": read_json(session_file(session_id, "result.json"), default={}),
        "developer": read_json(session_file(session_id, "developer.json"), default={}),
        "yolo_raw": read_json(session_file(session_id, "yolo_raw.json"), default={}),
        "ai_raw": read_json(session_file(session_id, "ai_raw.json"), default={}),
        "geometry": read_json(session_file(session_id, "geometry.json"), default={}),
    }
    file_paths = {name: str(session_file(session_id, filename)) for name, filename in {
        "metadata": "metadata.json",
        "result": "result.json",
        "developer": "developer.json",
        "yolo_raw": "yolo_raw.json",
        "ai_raw": "ai_raw.json",
        "geometry": "geometry.json",
        "original": "original.jpg",
        "annotated": "annotated.jpg",
    }.items()}
    return render_template(
        "plan_c_developer.html",
        session_id=session_id,
        files=redact_for_display(files),
        file_paths={name: relative_to_project(path) for name, path in file_paths.items()},
        plan_c_ui_version=PLAN_C_UI_VERSION,
    )


@plan_c_bp.get("/plan-c/session/<session_id>/annotated.jpg")
def annotated_image(session_id: str):
    path = session_file(session_id, "annotated.jpg")
    if not path.exists():
        return "", 404
    return send_file(path, mimetype="image/jpeg", conditional=False)


@plan_c_bp.post("/api/plan-c/session/start")
def api_start_session():
    payload = _request_payload()
    result = create_plan_c_session(payload)
    return jsonify(result), 201


@plan_c_bp.post("/api/plan-c/session/tree-anchor")
def api_tree_anchor():
    payload = _request_payload()
    session_id = str(payload.get("session_id") or "").strip()
    if not session_id:
        return jsonify({"ok": False, "status": "PLAN_C_SESSION_ID_REQUIRED"}), 400
    result = save_tree_anchor(session_id, payload)
    return jsonify(result), 200


@plan_c_bp.post("/api/plan-c/session/snapshot")
def api_snapshot():
    payload = _request_payload()
    session_id = str(payload.get("session_id") or "").strip()
    if not session_id:
        return jsonify({"ok": False, "status": "PLAN_C_SESSION_ID_REQUIRED"}), 400
    image_file = request.files.get("snapshot") or request.files.get("image") or request.files.get("file")
    try:
        result = process_plan_c_snapshot(session_id, image_file=image_file, payload=payload)
    except Exception as exc:
        return jsonify({"ok": False, "status": "PLAN_C_SNAPSHOT_FAILED", "error": f"{type(exc).__name__}: {exc}"}), 400
    status_code = int(result.pop("http_status", 202))
    return jsonify(result), status_code


@plan_c_bp.post("/api/plan-c/operator-feedback")
def api_operator_feedback():
    result = save_operator_feedback(_request_payload())
    return jsonify(result), 200 if result.get("ok") else 400


@plan_c_bp.get("/api/plan-c/runtime/ui-version")
def api_runtime_ui_version():
    return jsonify(
        {
            "ok": True,
            "plan_c_ui_version": PLAN_C_UI_VERSION,
            "route_status": "PLAN_C_UI_VERSION_READY",
        }
    ), 200


@plan_c_bp.get("/api/plan-c/free-vision/status")
def api_free_vision_status():
    return jsonify(build_free_vision_status_payload()), 200


@plan_c_bp.get("/api/plan-c/session/<session_id>/status")
def api_status(session_id: str):
    return jsonify(build_session_status(session_id)), 200


@plan_c_bp.get("/api/plan-c/session/<session_id>/result")
def api_result(session_id: str):
    result = read_json(session_file(session_id, "result.json"), default=None)
    if not result:
        return jsonify({"ok": True, "status": "PLAN_C_PROCESSING", "session_id": session_id, "result_ready": False}), 200
    return jsonify({"ok": True, "result_ready": True, **result}), 200


def _request_payload() -> dict[str, Any]:
    if request.is_json:
        payload = request.get_json(silent=True)
        return dict(payload or {})
    payload = dict(request.form)
    for key in ["latitude", "longitude", "lat", "lon", "lng", "gps_accuracy_m", "accuracy"]:
        if key in request.args and key not in payload:
            payload[key] = request.args.get(key)
    return payload
