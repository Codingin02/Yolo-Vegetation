"""Append-only storage helpers for Progress 8 Plan C."""

from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path
import re
from typing import Any

from .paths import PROJECT_ROOT

PLAN_C_RUNTIME_ROOT = PROJECT_ROOT / "data" / "runtime" / "plan_c"
PLAN_C_SESSION_ROOT = PLAN_C_RUNTIME_ROOT / "sessions"
PLAN_C_SPREADSHEET_DIR = PLAN_C_RUNTIME_ROOT / "spreadsheet"
PLAN_C_MAP_DIR = PLAN_C_RUNTIME_ROOT / "map"
PLAN_C_REFERENCE_DIR = PROJECT_ROOT / "data" / "reference" / "pohon_sono_growth"

PLAN_C_RECORDS_CSV = PLAN_C_SPREADSHEET_DIR / "plan_c_records.csv"
PLAN_C_RECORDS_JSONL = PLAN_C_SPREADSHEET_DIR / "plan_c_records.jsonl"
PLAN_C_MARKERS_JSON = PLAN_C_MAP_DIR / "plan_c_markers.json"

SESSION_FILES = [
    "original.jpg",
    "annotated.jpg",
    "result.json",
    "developer.json",
    "metadata.json",
    "yolo_raw.json",
    "ai_raw.json",
    "geometry.json",
]

PLAN_C_RECORD_FIELDS = [
    "record_id",
    "session_id",
    "created_at",
    "risk_status",
    "prediction_window",
    "manual_review_required",
    "latitude",
    "longitude",
    "gps_accuracy_m",
    "yolo_status",
    "ai_validator_status",
    "geometry_status",
    "growth_profile_status",
    "growth_rate_m_per_quarter",
    "data_source_type",
    "original_path",
    "annotated_path",
    "result_path",
]

_SESSION_ID_PATTERN = re.compile(r"^[A-Za-z0-9_-]+$")


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def ensure_plan_c_dirs() -> dict[str, str]:
    for path in [PLAN_C_RUNTIME_ROOT, PLAN_C_SESSION_ROOT, PLAN_C_SPREADSHEET_DIR, PLAN_C_MAP_DIR, PLAN_C_REFERENCE_DIR]:
        path.mkdir(parents=True, exist_ok=True)
    return {
        "runtime_root": str(PLAN_C_RUNTIME_ROOT),
        "session_root": str(PLAN_C_SESSION_ROOT),
        "spreadsheet_dir": str(PLAN_C_SPREADSHEET_DIR),
        "map_dir": str(PLAN_C_MAP_DIR),
        "reference_dir": str(PLAN_C_REFERENCE_DIR),
    }


def validate_session_id(session_id: str) -> str:
    cleaned = str(session_id or "").strip()
    if not cleaned or not _SESSION_ID_PATTERN.match(cleaned):
        raise ValueError("PLAN_C_SESSION_ID_INVALID")
    if not cleaned.startswith("PC_"):
        raise ValueError("PLAN_C_SESSION_ID_PREFIX_INVALID")
    return cleaned


def session_dir(session_id: str) -> Path:
    ensure_plan_c_dirs()
    return PLAN_C_SESSION_ROOT / validate_session_id(session_id)


def session_file(session_id: str, filename: str) -> Path:
    if filename not in SESSION_FILES:
        raise ValueError(f"PLAN_C_SESSION_FILE_NOT_ALLOWED: {filename}")
    return session_dir(session_id) / filename


def ensure_session_dir(session_id: str) -> Path:
    path = session_dir(session_id)
    path.mkdir(parents=True, exist_ok=True)
    return path


def write_json(path: Path, payload: dict[str, Any] | list[Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def read_json(path: Path, default: Any | None = None) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return default


def relative_to_project(path: Path | str | None) -> str:
    if not path:
        return ""
    path_obj = Path(path)
    try:
        return str(path_obj.resolve().relative_to(PROJECT_ROOT.resolve())).replace("\\", "/")
    except (OSError, ValueError):
        return str(path_obj).replace("\\", "/")


def append_plan_c_record(record: dict[str, Any]) -> dict[str, Any]:
    ensure_plan_c_dirs()
    before_csv_rows = count_csv_rows(PLAN_C_RECORDS_CSV)
    before_jsonl_rows = count_jsonl_rows(PLAN_C_RECORDS_JSONL)

    normalized = {field: _stringify_csv_value(record.get(field)) for field in PLAN_C_RECORD_FIELDS}
    write_header = not PLAN_C_RECORDS_CSV.exists() or PLAN_C_RECORDS_CSV.stat().st_size == 0
    with PLAN_C_RECORDS_CSV.open("a", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=PLAN_C_RECORD_FIELDS)
        if write_header:
            writer.writeheader()
        writer.writerow(normalized)

    with PLAN_C_RECORDS_JSONL.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False, default=str) + "\n")

    return {
        "status": "PLAN_C_RECORD_APPENDED",
        "csv_path": str(PLAN_C_RECORDS_CSV),
        "jsonl_path": str(PLAN_C_RECORDS_JSONL),
        "csv_rows_before": before_csv_rows,
        "csv_rows_after": count_csv_rows(PLAN_C_RECORDS_CSV),
        "jsonl_rows_before": before_jsonl_rows,
        "jsonl_rows_after": count_jsonl_rows(PLAN_C_RECORDS_JSONL),
    }


def count_csv_rows(path: Path = PLAN_C_RECORDS_CSV) -> int:
    if not path.exists():
        return 0
    with path.open("r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(line for line in handle if line.strip())
        return sum(1 for _ in reader)


def count_jsonl_rows(path: Path = PLAN_C_RECORDS_JSONL) -> int:
    if not path.exists():
        return 0
    with path.open("r", encoding="utf-8") as handle:
        return sum(1 for line in handle if line.strip())


def read_markers() -> list[dict[str, Any]]:
    if not PLAN_C_MARKERS_JSON.exists():
        return []
    data = read_json(PLAN_C_MARKERS_JSON, default=[])
    return data if isinstance(data, list) else []


def append_marker(marker: dict[str, Any]) -> dict[str, Any]:
    ensure_plan_c_dirs()
    if not is_valid_gps(marker.get("latitude"), marker.get("longitude")):
        return {
            "status": "NO_GPS_NO_MARKER",
            "marker_appended": False,
            "marker_count_before": len(read_markers()),
            "marker_count_after": len(read_markers()),
        }
    markers = read_markers()
    before = len(markers)
    markers.append(marker)
    write_json(PLAN_C_MARKERS_JSON, markers)
    return {
        "status": "PLAN_C_MARKER_APPENDED",
        "marker_appended": True,
        "marker_path": str(PLAN_C_MARKERS_JSON),
        "marker_count_before": before,
        "marker_count_after": len(markers),
    }


def is_valid_gps(latitude: Any, longitude: Any) -> bool:
    lat = to_float(latitude)
    lon = to_float(longitude)
    return lat is not None and lon is not None and -90 <= lat <= 90 and -180 <= lon <= 180


def to_float(value: Any) -> float | None:
    if value in {None, ""}:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _stringify_csv_value(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False, default=str)
    return str(value)
