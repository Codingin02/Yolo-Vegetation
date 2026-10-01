from __future__ import annotations

from typing import Any

from flask import Blueprint, jsonify, render_template, request, send_file
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from .detection import detector_mode, model_path
from .growth import predict_growth, validate_prediction_features
from .pipeline import decode_image, measurement_values, process_capture, process_frame
from .storage import (
    create_session,
    load_metadata,
    read_json,
    redact,
    relative_path,
    session_file,
    write_json,
)


vegetation = Blueprint("vegetation", __name__)
limiter = Limiter(key_func=get_remote_address, default_limits=[], storage_uri="memory://")


@vegetation.get("/vegetation")
def home():
    return render_template("home.html")


@vegetation.get("/vegetation/capture/<session_id>")
def capture(session_id: str):
    metadata = load_metadata(session_id)
    return render_template("capture.html", session_id=session_id, metadata=metadata) if metadata else ("Sesi tidak ditemukan", 404)


@vegetation.get("/vegetation/processing/<session_id>")
def processing(session_id: str):
    return render_template("processing.html", session_id=session_id)


@vegetation.get("/vegetation/result/<session_id>")
def result(session_id: str):
    payload = read_json(session_file(session_id, "result.json"), {})
    return render_template("result.html", session_id=session_id, result=payload, result_ready=bool(payload))


@vegetation.get("/vegetation/developer/<session_id>")
def developer(session_id: str):
    files = {
        name: read_json(session_file(session_id, filename), {})
        for name, filename in {
            "metadata": "metadata.json",
            "result": "result.json",
            "detection": "detections.json",
            "growth": "growth.json",
            "developer": "developer.json",
        }.items()
    }
    return render_template("developer.html", session_id=session_id, files=redact(files))


@vegetation.get("/vegetation/session/<session_id>/annotated.jpg")
def annotated_image(session_id: str):
    path = session_file(session_id, "annotated.jpg")
    return send_file(path, mimetype="image/jpeg", conditional=False) if path.exists() else ("", 404)


@vegetation.post("/api/vegetation/session/start")
def start_session():
    return jsonify(create_session(_payload())), 201


@vegetation.post("/api/vegetation/session/snapshot")
def snapshot():
    payload = _payload()
    session_id = str(payload.get("session_id") or "")
    image = request.files.get("snapshot") or request.files.get("image") or request.files.get("file")
    try:
        result_payload = process_capture(session_id, image, payload)
    except (FileNotFoundError, ValueError):
        return jsonify({"status": "capture_rejected", "error": "invalid capture"}), 400
    return jsonify(
        {
            "status": "ready",
            "session_id": session_id,
            "result_url": f"/vegetation/result/{session_id}",
            "processing_url": f"/vegetation/processing/{session_id}",
            "result": result_payload,
        }
    ), 201


@vegetation.post("/api/vegetation/realtime/frame")
@limiter.limit("20 per second; 900 per minute")
def realtime_frame():
    payload = _payload()
    session_id = str(payload.get("session_id") or "")
    try:
        metadata = load_metadata(session_id)
        if not metadata:
            raise FileNotFoundError("session not found")
        frame_payload = dict(metadata)
        for name in (
            "species",
            "growth_stage",
            "tree_stage",
            "clearance_m",
            "measurement_source",
            "lighting_mode",
            "capture_distance_m",
            "monitor_threshold_m",
            "action_threshold_m",
            "support_family",
            "support_spec",
            "support_buried_length_m",
            "support_standard_installation_confirmed",
            "support_full_height_confirmed",
            "tree_base_visible_confirmed",
        ):
            if payload.get(name) is not None and payload.get(name) != "":
                frame_payload[name] = payload[name]
        frame = decode_image(request.files.get("frame") or request.files.get("image"))
        height, width = frame.shape[:2]
        result_payload, _ = process_frame(frame, frame_payload, tracking_session=session_id, render=False)
        result_payload.pop("renderer", None)
        result_payload["session_id"] = session_id
        result_payload["frame"] = {"width": int(width), "height": int(height)}
        return jsonify(result_payload)
    except (FileNotFoundError, OSError, ValueError):
        return jsonify({"status": "frame_rejected", "error": "invalid frame"}), 400


@vegetation.post("/api/vegetation/prediction")
@limiter.limit("5 per second; 120 per minute")
def prediction():
    payload = _payload()
    try:
        clearance_m, measurement_source = measurement_values(payload)
        validate_prediction_features(payload)
    except ValueError:
        return jsonify({"status": "prediction_rejected", "error": "invalid prediction input"}), 400
    geometry = _trusted_session_geometry(payload)
    result_payload = predict_growth(
        species=str(payload.get("species") or "").strip() or None,
        growth_stage=str(payload.get("tree_stage") or payload.get("growth_stage") or "").strip() or None,
        clearance_m=clearance_m,
        features=payload,
        geometry_status=geometry.get("measurement_status") or payload.get("geometry_status"),
        risk_status=geometry.get("risk_status") or payload.get("risk_status"),
        geometry=geometry or None,
    )
    return jsonify({**result_payload, "measurement_source": measurement_source})


@vegetation.get("/api/vegetation/session/<session_id>/status")
def session_status(session_id: str):
    metadata = load_metadata(session_id)
    result_payload = read_json(session_file(session_id, "result.json"), {})
    return jsonify(
        {
            "status": metadata.get("status", "session_not_found"),
            "session_id": session_id,
            "result_ready": bool(result_payload),
            "result_url": f"/vegetation/result/{session_id}",
        }
    )


@vegetation.get("/api/vegetation/session/<session_id>/result")
def api_result(session_id: str):
    payload = read_json(session_file(session_id, "result.json"), None)
    return jsonify(payload or {"status": "processing", "session_id": session_id})


@vegetation.post("/api/vegetation/operator-feedback")
def operator_feedback():
    payload = _payload()
    session_id = str(payload.get("session_id") or "")
    result_payload = read_json(session_file(session_id, "result.json"), None)
    if not isinstance(result_payload, dict):
        return jsonify({"status": "result_not_found"}), 404
    accepted = str(payload.get("decision") or "").lower() == "accepted"
    result_payload["active"] = accepted
    result_payload["operator_review"] = "accepted" if accepted else "rejected"
    write_json(session_file(session_id, "result.json"), result_payload)
    return jsonify({"status": "saved", "active": accepted})


@vegetation.get("/api/vegetation/status")
def application_status():
    path = model_path()
    mode = detector_mode(path)
    detector_ready = path.is_file()
    return jsonify(
        {
            "status": "ready",
            "backend_ready": True,
            "realtime_runtime_ready": detector_ready,
            "route": "/vegetation",
            "api_root": "/api/vegetation",
            "realtime_route": "/api/vegetation/realtime/frame",
            "detector": {
                "mode": mode,
                "model": relative_path(path),
                "ready": detector_ready,
                "status": "ready" if detector_ready else "model_not_ready",
            },
            "tracking": {"status": "ready" if detector_ready else "unavailable", "engine": "ByteTrack"},
            "prediction": {"status": "available_with_required_inputs"},
            "angsana_model_ready": detector_ready and mode == "production",
        }
    )


@vegetation.errorhandler(ValueError)
def invalid_request(_: ValueError):
    payload = {"status": "invalid_request", "error": "invalid request"}
    return (jsonify(payload), 400) if request.path.startswith("/api/") else ("Permintaan tidak valid", 400)


def _payload() -> dict[str, Any]:
    if request.is_json:
        return dict(request.get_json(silent=True) or {})
    return dict(request.form)


def _trusted_session_geometry(payload: dict[str, Any]) -> dict[str, Any]:
    session_id = str(payload.get("session_id") or "").strip()
    if not session_id:
        return {}
    result_payload = read_json(session_file(session_id, "result.json"), {})
    trees = (result_payload.get("geometry") or {}).get("trees") or []
    requested_track = str(payload.get("track_id") or "").strip()
    if requested_track:
        return next((tree for tree in trees if str(tree.get("track_id")) == requested_track), {})
    return trees[0] if len(trees) == 1 else {}
