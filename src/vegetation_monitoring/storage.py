from __future__ import annotations

import csv
from datetime import datetime, timezone
import json
import math
import os
from pathlib import Path
import re
import tempfile
import threading
from typing import Any
import uuid


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SUPPORTED_LOCATIONS = {"surabaya": "Surabaya"}
SESSION_ID_PATTERN = re.compile(r"^capture_\d{8}_\d{6}_[0-9a-f]{8}$")
SESSION_FILES = {
    "original.jpg",
    "annotated.jpg",
    "metadata.json",
    "detections.json",
    "growth.json",
    "result.json",
    "developer.json",
}
RECORD_FIELDS = [
    "timestamp",
    "session_id",
    "location_name",
    "detector_status",
    "detected_classes",
    "clearance_m",
    "growth_status",
    "prediction_window",
    "result_path",
    "annotated_path",
]
_WRITE_LOCK = threading.Lock()
_SECRET_KEYS = {"api_key", "authorization", "credential", "secret", "token"}


def data_root() -> Path:
    configured = os.getenv("VEGETATION_DATA_ROOT", "").strip()
    return Path(configured).expanduser().resolve() if configured else PROJECT_ROOT / "data"


def runtime_root() -> Path:
    return data_root() / "runtime"


def sessions_root() -> Path:
    return runtime_root() / "sessions"


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def new_session_id() -> str:
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"capture_{stamp}_{uuid.uuid4().hex[:8]}"


def validate_session_id(session_id: str) -> str:
    value = str(session_id or "").strip()
    if not SESSION_ID_PATTERN.fullmatch(value):
        raise ValueError("invalid session_id")
    return value


def session_dir(session_id: str) -> Path:
    return sessions_root() / validate_session_id(session_id)


def session_file(session_id: str, filename: str) -> Path:
    if filename not in SESSION_FILES:
        raise ValueError(f"unsupported session file: {filename}")
    return session_dir(session_id) / filename


def create_session(payload: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = payload or {}
    location = str(payload.get("location") or "").strip()
    if location not in SUPPORTED_LOCATIONS:
        raise ValueError("unsupported location")
    session_id = new_session_id()
    session_dir(session_id).mkdir(parents=True, exist_ok=False)
    metadata = {
        "status": "waiting_for_capture",
        "session_id": session_id,
        "created_at": now_iso(),
        "updated_at": now_iso(),
        "operator_name": str(payload.get("operator_name") or "").strip(),
        "location": location,
        "location_name": SUPPORTED_LOCATIONS[location],
        "species": payload.get("species") or None,
        "growth_stage": payload.get("growth_stage") or None,
        "clearance_m": None,
        "measurement_source": None,
        "processed": False,
    }
    write_json(session_file(session_id, "metadata.json"), metadata)
    return {
        "status": "session_started",
        "session_id": session_id,
        "capture_url": f"/vegetation/capture/{session_id}",
    }


def load_metadata(session_id: str) -> dict[str, Any]:
    return read_json(session_file(session_id, "metadata.json"), {})


def update_metadata(session_id: str, **updates: Any) -> dict[str, Any]:
    metadata = load_metadata(session_id)
    if not metadata:
        raise FileNotFoundError("session not found")
    metadata.update(updates)
    metadata["updated_at"] = now_iso()
    write_json(session_file(session_id, "metadata.json"), metadata)
    return metadata


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    encoded = json.dumps(payload, ensure_ascii=False, indent=2, default=str) + "\n"
    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(encoded)
        os.replace(temporary, path)
    except Exception:
        try:
            os.unlink(temporary)
        except OSError:
            pass
        raise


def read_json(path: Path, default: Any = None) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, OSError, json.JSONDecodeError):
        return default


def append_record(record: dict[str, Any]) -> bool:
    records_dir = runtime_root() / "records"
    csv_path = records_dir / "records.csv"
    jsonl_path = records_dir / "records.jsonl"
    records_dir.mkdir(parents=True, exist_ok=True)
    row = {field: _csv_value(record.get(field)) for field in RECORD_FIELDS}
    session_id = str(record.get("session_id") or "")
    with _WRITE_LOCK:
        csv_exists = _csv_has_session(csv_path, session_id)
        jsonl_exists = _jsonl_has_session(jsonl_path, session_id)
        if not csv_exists:
            write_header = not csv_path.exists() or csv_path.stat().st_size == 0
            with csv_path.open("a", newline="", encoding="utf-8") as handle:
                writer = csv.DictWriter(handle, fieldnames=RECORD_FIELDS)
                if write_header:
                    writer.writeheader()
                writer.writerow(row)
        if not jsonl_exists:
            with jsonl_path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(record, ensure_ascii=False, default=str) + "\n")
    return not (csv_exists and jsonl_exists)


def relative_path(path: Path | str | None) -> str | None:
    if path is None:
        return None
    value = Path(path)
    try:
        return value.resolve().relative_to(PROJECT_ROOT.resolve()).as_posix()
    except (OSError, ValueError):
        return value.name


def redact(value: Any, key: str = "") -> Any:
    if any(secret in key.lower() for secret in _SECRET_KEYS):
        return "[REDACTED]"
    if isinstance(value, dict):
        return {name: redact(item, str(name)) for name, item in value.items()}
    if isinstance(value, list):
        return [redact(item, key) for item in value]
    if isinstance(value, str) and (value.startswith(str(PROJECT_ROOT)) or re.match(r"^[A-Za-z]:[\\/]", value)):
        return relative_path(value)
    return value


def as_float(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    return parsed if math.isfinite(parsed) else None


def _csv_value(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, (list, dict)):
        return json.dumps(value, ensure_ascii=False, default=str)
    return str(value)


def _csv_has_session(path: Path, session_id: str) -> bool:
    if not session_id or not path.is_file():
        return False
    try:
        with path.open(newline="", encoding="utf-8") as handle:
            return any(row.get("session_id") == session_id for row in csv.DictReader(handle))
    except OSError:
        return False


def _jsonl_has_session(path: Path, session_id: str) -> bool:
    if not session_id or not path.is_file():
        return False
    try:
        for line in path.read_text(encoding="utf-8").splitlines():
            try:
                if json.loads(line).get("session_id") == session_id:
                    return True
            except (AttributeError, json.JSONDecodeError):
                continue
    except OSError:
        return False
    return False
