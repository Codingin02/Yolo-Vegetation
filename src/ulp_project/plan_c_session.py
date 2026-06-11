"""Plan C session lifecycle utilities."""

from __future__ import annotations

from datetime import datetime
from typing import Any
import uuid

from .plan_c_storage import ensure_session_dir, read_json, session_file, to_float, utc_now_iso, write_json


def new_session_id() -> str:
    return f"PC_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"


def create_plan_c_session(payload: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = payload or {}
    session_id = str(payload.get("session_id") or "").strip() or new_session_id()
    folder = ensure_session_dir(session_id)
    metadata = {
        "status": "PLAN_C_SESSION_STARTED",
        "session_id": session_id,
        "created_at": utc_now_iso(),
        "updated_at": utc_now_iso(),
        "operator_name": str(payload.get("operator_name") or "").strip(),
        "tree_anchor_status": "TREE_ANCHOR_PENDING",
        "snapshot_status": "SNAPSHOT_PENDING",
        "processing_status": "WAITING_FOR_SNAPSHOT",
        "result_status": "RESULT_NOT_READY",
        "idempotency_keys": {},
        "storage": {"session_dir": str(folder)},
    }
    write_json(session_file(session_id, "metadata.json"), metadata)
    return {
        "ok": True,
        "status": "PLAN_C_SESSION_STARTED",
        "session_id": session_id,
        "capture_url": f"/plan-c/capture/{session_id}",
        "metadata_path": str(session_file(session_id, "metadata.json")),
    }


def load_plan_c_metadata(session_id: str) -> dict[str, Any]:
    return read_json(session_file(session_id, "metadata.json"), default={}) or {}


def save_plan_c_metadata(session_id: str, metadata: dict[str, Any]) -> dict[str, Any]:
    metadata["session_id"] = session_id
    metadata["updated_at"] = utc_now_iso()
    write_json(session_file(session_id, "metadata.json"), metadata)
    return metadata


def update_plan_c_status(session_id: str, *, status: str | None = None, **updates: Any) -> dict[str, Any]:
    metadata = load_plan_c_metadata(session_id)
    if status:
        metadata["status"] = status
    metadata.update(updates)
    return save_plan_c_metadata(session_id, metadata)


def save_tree_anchor(session_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    metadata = load_plan_c_metadata(session_id)
    latitude = to_float(payload.get("latitude") or payload.get("lat"))
    longitude = to_float(payload.get("longitude") or payload.get("lon") or payload.get("lng"))
    accuracy = to_float(payload.get("gps_accuracy_m") or payload.get("accuracy"))
    anchor = {
        "latitude": latitude,
        "longitude": longitude,
        "gps_accuracy_m": accuracy,
        "captured_at": utc_now_iso(),
        "gps_source": "GPS_SOURCE_BROWSER" if latitude is not None and longitude is not None else "GPS_SOURCE_UNAVAILABLE",
    }
    if latitude is None or longitude is None:
        metadata["tree_anchor_status"] = "TREE_ANCHOR_PENDING"
        metadata["tree_anchor"] = {**anchor, "status": "TREE_ANCHOR_PENDING"}
        save_plan_c_metadata(session_id, metadata)
        return {
            "ok": True,
            "status": "TREE_ANCHOR_ACCEPTED_DEGRADED",
            "tree_anchor_status": "TREE_ANCHOR_PENDING",
            "session_id": session_id,
            "gps_valid": False,
            "message": "GPS belum valid; kamera tetap dapat dipakai.",
        }

    metadata["tree_anchor_status"] = "TREE_ANCHOR_SAVED"
    metadata["tree_anchor"] = {**anchor, "status": "TREE_ANCHOR_SAVED"}
    save_plan_c_metadata(session_id, metadata)
    return {
        "ok": True,
        "status": "TREE_ANCHOR_SAVED",
        "tree_anchor_status": "TREE_ANCHOR_SAVED",
        "session_id": session_id,
        "gps_valid": True,
        "tree_anchor": metadata["tree_anchor"],
    }


def build_session_status(session_id: str) -> dict[str, Any]:
    metadata = load_plan_c_metadata(session_id)
    result = read_json(session_file(session_id, "result.json"), default=None)
    result_ready = isinstance(result, dict) and result.get("status") == "PLAN_C_RESULT_READY"
    status = "PLAN_C_RESULT_READY" if result_ready else metadata.get("status", "PLAN_C_SESSION_UNKNOWN")
    return {
        "ok": bool(metadata),
        "status": status,
        "session_id": session_id,
        "result_ready": result_ready,
        "capture_url": f"/plan-c/capture/{session_id}",
        "processing_url": f"/plan-c/processing/{session_id}",
        "result_url": f"/plan-c/result/{session_id}",
        "developer_url": f"/plan-c/developer/{session_id}",
        "metadata": metadata,
    }
