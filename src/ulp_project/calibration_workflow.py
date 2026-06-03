"""Field calibration workflow without touching labeling data."""

from __future__ import annotations

import csv
import json
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Any

from .camera_intrinsic_estimator import estimate_scale_m_per_px
from .paths import PROJECT_ROOT
from .reference_object_profile import normalize_reference_type

RUNTIME_CALIBRATION_DIR = PROJECT_ROOT / "data" / "runtime" / "calibration"
TEMPLATE_PATH = PROJECT_ROOT / "data" / "templates" / "calibration_session_template.csv"


@dataclass
class CalibrationSession:
    calibration_id: str
    timestamp: str
    point_id: str
    reference_type: str
    known_height_m: float | None
    reference_bbox_height_px: float | None
    image_width_px: int | None
    image_height_px: int | None
    estimated_m_per_px: float | None
    camera_facing: str
    distance_reference_m: float | None
    operator_notes: str
    quality_status: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def create_calibration_session(payload: dict[str, Any], *, write_runtime: bool = True, runtime_dir: Path = RUNTIME_CALIBRATION_DIR) -> dict[str, Any]:
    point_id = str(payload.get("point_id") or "")
    calibration_id = str(payload.get("calibration_id") or f"cal_{point_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
    known = _float(payload.get("known_height_m"))
    bbox_px = _float(payload.get("reference_bbox_height_px"))
    scale = estimate_scale_m_per_px(known, bbox_px)
    quality = validate_calibration_payload({**payload, "estimated_m_per_px": scale["estimated_m_per_px"]})["quality_status"]
    session = CalibrationSession(
        calibration_id=calibration_id,
        timestamp=str(payload.get("timestamp") or datetime.now().isoformat()),
        point_id=point_id,
        reference_type=normalize_reference_type(payload.get("reference_type")),
        known_height_m=known,
        reference_bbox_height_px=bbox_px,
        image_width_px=_int(payload.get("image_width_px")),
        image_height_px=_int(payload.get("image_height_px")),
        estimated_m_per_px=scale["estimated_m_per_px"],
        camera_facing=str(payload.get("camera_facing") or payload.get("camera_device_hint") or ""),
        distance_reference_m=_float(payload.get("distance_reference_m")),
        operator_notes=str(payload.get("operator_notes") or payload.get("notes") or ""),
        quality_status=quality,
    )
    if write_runtime:
        runtime_dir.mkdir(parents=True, exist_ok=True)
        (runtime_dir / f"{session.calibration_id}.json").write_text(json.dumps(session.to_dict(), indent=2, ensure_ascii=False), encoding="utf-8")
    return {"status": session.quality_status, "session": session.to_dict(), "runtime_written": write_runtime, "runtime_dir": str(runtime_dir)}


def validate_calibration_payload(payload: dict[str, Any]) -> dict[str, Any]:
    reason_codes: list[str] = []
    known = _float(payload.get("known_height_m"))
    bbox_px = _float(payload.get("reference_bbox_height_px"))
    width = _int(payload.get("image_width_px"))
    height = _int(payload.get("image_height_px"))
    scale = _float(payload.get("estimated_m_per_px"))
    if known is None or known <= 0:
        reason_codes.append("KNOWN_HEIGHT_REQUIRED")
    if bbox_px is None or bbox_px <= 0:
        reason_codes.append("REFERENCE_BBOX_HEIGHT_REQUIRED")
    if width is None or height is None:
        reason_codes.append("FRAME_RESOLUTION_REQUIRED")
    if scale is not None and (scale <= 0 or scale > 1.0):
        reason_codes.append("SCALE_EXTREME_REVIEW_REQUIRED")
    if reason_codes:
        quality = "CALIBRATION_NOT_READY" if "KNOWN_HEIGHT_REQUIRED" in reason_codes or "REFERENCE_BBOX_HEIGHT_REQUIRED" in reason_codes else "CALIBRATION_LOW_CONFIDENCE"
    else:
        quality = "CALIBRATION_READY_MANUAL_REFERENCE"
    return {"quality_status": quality, "reason_codes": reason_codes, "point_id_policy": "P_K_V_PREFIX_ALLOWED_NOT_SPATIAL_SEQUENCE"}


def load_calibration_template_columns(path: Path = TEMPLATE_PATH) -> list[str]:
    with path.open(newline="", encoding="utf-8") as handle:
        return csv.DictReader(handle).fieldnames or []


def _float(value: Any) -> float | None:
    try:
        if value in (None, ""):
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _int(value: Any) -> int | None:
    try:
        if value in (None, ""):
            return None
        return int(float(value))
    except (TypeError, ValueError):
        return None
