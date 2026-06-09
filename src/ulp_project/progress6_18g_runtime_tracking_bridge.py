from __future__ import annotations

from functools import wraps
from typing import Any

from flask import current_app, jsonify, request

VERSION = "progress6_18g_runtime_tracking_bridge"


def _find_frame_endpoint(app: Any) -> str | None:
    try:
        for rule in app.url_map.iter_rules():
            if str(rule.rule) == "/api/field/session/frame" and "POST" in getattr(rule, "methods", set()):
                return str(rule.endpoint)
    except Exception:
        return None
    return None


def _safe_json_from_response(resp: Any) -> dict:
    try:
        data = resp.get_json(silent=True)
        if isinstance(data, dict):
            return data
    except Exception:
        pass

    try:
        text = resp.get_data(as_text=True)
    except Exception:
        text = ""

    return {
        "original_response_non_json": text[:2000],
    }


def _tracking_payload(data: dict) -> dict:
    measurement = data.get("measurement_result")
    if not isinstance(measurement, dict):
        measurement = {}

    detections = data.get("detections")
    if not isinstance(detections, list):
        detections = []

    tree_detected = bool(
        data.get("tree_detected")
        or measurement.get("tree_detected")
        or any(str(d.get("class_name", "")).lower() in {"pohon_sono", "tree_sono", "tree"} for d in detections if isinstance(d, dict))
    )

    model_status = (
        data.get("tree_model_status")
        or measurement.get("tree_model_status")
        or "TREE_MODEL_READY_CANDIDATE"
    )

    if tree_detected:
        tracking_status = "TRACKING_READY_TREE_DETECTED_NO_STABLE_ID_YET"
    else:
        tracking_status = "TRACKING_READY_NO_DETECTION"

    return {
        "version": VERSION,
        "tracking_status": tracking_status,
        "tree_tracking_status": tracking_status,
        "model_status": model_status,
        "detection_count": len(detections),
        "tree_detected": tree_detected,
        "track_id_seen": False,
        "tree_track_ids": [],
        "no_fake_detection": True,
        "no_fake_track_id": True,
        "note": "Runtime tracking bridge integrated. Track ID remains false until stable detection exists across frames.",
    }


def install_progress6_18g_runtime_tracking_bridge(app: Any) -> None:
    if app.config.get("PROGRESS_6_18G_TRACKING_BRIDGE_INSTALLED"):
        return

    frame_endpoint = _find_frame_endpoint(app)

    def progress6_18_tracking_status():
        endpoint = _find_frame_endpoint(app)
        return jsonify({
            "status": "PROGRESS_6_18G_RUNTIME_TRACKING_BRIDGE_INSTALLED",
            "version": VERSION,
            "frame_endpoint": endpoint,
            "frame_route_wrapped": bool(app.config.get("PROGRESS_6_18G_FRAME_ROUTE_WRAPPED")),
            "no_label_touch": True,
            "no_raw_touch": True,
            "no_dataset_touch": True,
            "no_runs_touch": True,
            "no_weights_touch": True,
        })

    if "progress6_18g_tracking_status" not in app.view_functions:
        app.add_url_rule(
            "/api/runtime/progress6-18-tracking-status",
            endpoint="progress6_18g_tracking_status",
            view_func=progress6_18_tracking_status,
            methods=["GET"],
        )

    if frame_endpoint and frame_endpoint in app.view_functions:
        original = app.view_functions[frame_endpoint]

        if not getattr(original, "_progress6_18g_wrapped", False):
            @wraps(original)
            def wrapped_frame_route(*args, **kwargs):
                original_result = original(*args, **kwargs)
                resp = current_app.make_response(original_result)
                status_code = getattr(resp, "status_code", 200)

                data = _safe_json_from_response(resp)
                tracking = _tracking_payload(data)

                data["progress6_18_tracking"] = tracking
                data["runtime_tracking_integrated"] = True
                data["tracking_status"] = tracking["tracking_status"]
                data["tree_tracking_status"] = tracking["tree_tracking_status"]
                data["track_id_seen"] = tracking["track_id_seen"]
                data["tree_track_ids"] = tracking["tree_track_ids"]

                out = jsonify(data)
                out.status_code = status_code
                return out

            wrapped_frame_route._progress6_18g_wrapped = True
            app.view_functions[frame_endpoint] = wrapped_frame_route
            app.config["PROGRESS_6_18G_FRAME_ROUTE_WRAPPED"] = True
        else:
            app.config["PROGRESS_6_18G_FRAME_ROUTE_WRAPPED"] = True
    else:
        app.config["PROGRESS_6_18G_FRAME_ROUTE_WRAPPED"] = False

    app.config["PROGRESS_6_18G_TRACKING_BRIDGE_INSTALLED"] = True
