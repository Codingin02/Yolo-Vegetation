"""Storage helpers for Plan C upload image mode."""

from __future__ import annotations

from io import BytesIO
from pathlib import Path
import uuid
from typing import Any

from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename

from .plan_c_storage import (
    ensure_session_dir,
    is_valid_gps,
    read_json,
    session_file,
    to_float,
    utc_now_iso,
    write_json,
)

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
MAX_UPLOAD_BYTES = 12 * 1024 * 1024
SOURCE_MODE = "UPLOAD_IMAGE_MODE"


def create_upload_session(image_file: FileStorage | None, payload: dict[str, Any]) -> dict[str, Any]:
    if image_file is None or not getattr(image_file, "filename", ""):
        return {"ok": False, "status": "UPLOAD_IMAGE_REQUIRED", "http_status": 400}
    filename = secure_filename(str(image_file.filename or ""))
    suffix = Path(filename).suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        return {"ok": False, "status": "UPLOAD_IMAGE_EXTENSION_NOT_ALLOWED", "http_status": 400}

    raw = image_file.read(MAX_UPLOAD_BYTES + 1)
    if len(raw) > MAX_UPLOAD_BYTES:
        return {"ok": False, "status": "UPLOAD_IMAGE_TOO_LARGE", "http_status": 413}
    if not raw:
        return {"ok": False, "status": "UPLOAD_IMAGE_EMPTY", "http_status": 400}

    session_id = f"PC_UPLOAD_{uuid.uuid4().hex[:18]}"
    session_dir = ensure_session_dir(session_id)
    original_path = session_file(session_id, "original.jpg")
    conversion = _save_original_jpeg(raw, original_path)
    if not conversion.get("ok"):
        return {"ok": False, **conversion, "http_status": 400}

    lat = to_float(payload.get("latitude"))
    lon = to_float(payload.get("longitude"))
    accuracy = to_float(payload.get("accuracy_m") or payload.get("gps_accuracy_m"))
    gps_valid = is_valid_gps(lat, lon)
    metadata = {
        "session_id": session_id,
        "created_at": utc_now_iso(),
        "source_mode": SOURCE_MODE,
        "gps_status": "GPS_READY" if gps_valid else "GPS_NOT_AVAILABLE",
        "latitude": lat if gps_valid else None,
        "longitude": lon if gps_valid else None,
        "accuracy_m": accuracy if gps_valid else None,
        "operator_name": str(payload.get("operator_name") or "").strip(),
        "point_id": str(payload.get("point_id") or "").strip(),
        "notes": str(payload.get("notes") or "").strip(),
        "original_filename": filename,
        "original_image_path": str(original_path),
        "detection_status": "DETECTION_PENDING",
        "upload_status": "UPLOAD_ACCEPTED_DETECTION_PENDING",
        "manual_process_required": True,
        "storage_dir": str(session_dir),
    }
    write_json(session_file(session_id, "metadata.json"), metadata)
    return {
        "ok": True,
        "status": "UPLOAD_ACCEPTED_DETECTION_PENDING",
        "session_id": session_id,
        "review_url": f"/plan-c/upload/review/{session_id}",
        "metadata": metadata,
        "http_status": 201,
    }


def load_upload_metadata(session_id: str) -> dict[str, Any]:
    return read_json(session_file(session_id, "metadata.json"), default={}) or {}


def update_upload_metadata(session_id: str, updates: dict[str, Any]) -> dict[str, Any]:
    metadata = load_upload_metadata(session_id)
    metadata.update(updates)
    write_json(session_file(session_id, "metadata.json"), metadata)
    return metadata


def _save_original_jpeg(raw: bytes, destination: Path) -> dict[str, Any]:
    try:
        from PIL import Image

        with Image.open(BytesIO(raw)) as image:
            image.verify()
        with Image.open(BytesIO(raw)) as image:
            rgb = image.convert("RGB")
            destination.parent.mkdir(parents=True, exist_ok=True)
            rgb.save(destination, format="JPEG", quality=92)
        return {"ok": True, "status": "UPLOAD_IMAGE_SAVED"}
    except Exception as exc:
        return {"ok": False, "status": "UPLOAD_IMAGE_INVALID_OR_UNREADABLE", "error": f"{type(exc).__name__}: {exc}"}
