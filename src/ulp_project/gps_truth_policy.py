"""GPS truth and marker safety policy for field sessions."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


def coordinate_precision_status(value: Any) -> str:
    if value in {None, ""}:
        return "INVALID_COORDINATE_NULL"
    text = str(value).strip()
    try:
        number = float(text)
    except (TypeError, ValueError):
        return "INVALID_COORDINATE_NULL"
    if number == 0:
        return "INVALID_COORDINATE_ZERO_ZERO"
    decimals = _decimal_count(text)
    if decimals <= 2:
        return "GPS_PRECISION_LOST_ROUNDED_COORDINATE"
    return "GPS_COORDINATE_PRECISION_OK"


def validate_gps_evidence(gps: dict[str, Any] | None) -> dict[str, Any]:
    gps = gps or {}
    lat = _to_float(gps.get("latitude"))
    lon = _to_float(gps.get("longitude"))
    accuracy = _to_float(gps.get("accuracy"))
    timestamp = gps.get("timestamp")
    reasons: list[str] = []
    if lat is None or lon is None:
        reasons.append("INVALID_COORDINATE_NULL")
    elif lat == 0 and lon == 0:
        reasons.append("INVALID_COORDINATE_ZERO_ZERO")
    elif not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
        reasons.append("INVALID_COORDINATE_OUT_OF_RANGE")
    lat_precision = coordinate_precision_status(gps.get("latitude"))
    lon_precision = coordinate_precision_status(gps.get("longitude"))
    if "GPS_PRECISION_LOST_ROUNDED_COORDINATE" in {lat_precision, lon_precision}:
        reasons.append("GPS_PRECISION_LOST_ROUNDED_COORDINATE")
    if _is_stale_timestamp(timestamp):
        reasons.append("GPS_STALE_TIMESTAMP")
    if accuracy is None:
        reasons.append("GPS_ACCURACY_NOT_PROVIDED")
    elif accuracy > 25:
        reasons.append("GPS_ACCURACY_TOO_LOW_FOR_MARKER")
    elif accuracy > 10:
        reasons.append("GPS_ACCURACY_LOW")
    elif accuracy <= 5:
        reasons.append("GPS_READY_FOR_DISTANCE_REFERENCE")

    marker_allowed = not any(
        reason in set(reasons)
        for reason in {
            "INVALID_COORDINATE_NULL",
            "INVALID_COORDINATE_ZERO_ZERO",
            "INVALID_COORDINATE_OUT_OF_RANGE",
            "GPS_PRECISION_LOST_ROUNDED_COORDINATE",
            "GPS_STALE_TIMESTAMP",
            "GPS_ACCURACY_NOT_PROVIDED",
            "GPS_ACCURACY_TOO_LOW_FOR_MARKER",
        }
    )
    status = "GPS_MARKER_READY" if marker_allowed else "NO_GPS_NO_MARKER"
    if "INVALID_COORDINATE_NULL" in reasons:
        gps_precision_status = "INVALID_COORDINATE_NULL"
    elif "INVALID_COORDINATE_ZERO_ZERO" in reasons:
        gps_precision_status = "INVALID_COORDINATE_ZERO_ZERO"
    elif "INVALID_COORDINATE_OUT_OF_RANGE" in reasons:
        gps_precision_status = "INVALID_COORDINATE_OUT_OF_RANGE"
    elif "GPS_PRECISION_LOST_ROUNDED_COORDINATE" in reasons:
        gps_precision_status = "GPS_PRECISION_LOST_ROUNDED_COORDINATE"
    else:
        gps_precision_status = "GPS_PRECISION_OK"
    return {
        "status": status,
        "marker_allowed": marker_allowed,
        "gps_precision_status": gps_precision_status,
        "gps_quality_reasons": _dedupe(reasons) or ["GPS_READY_FOR_EVIDENCE"],
        "latitude_raw": format_coordinate_raw(lat),
        "longitude_raw": format_coordinate_raw(lon),
        "accuracy_m": accuracy,
    }


def format_coordinate_raw(value: Any) -> str:
    number = _to_float(value)
    if number is None:
        return "NOT_PROVIDED"
    return f"{number:.7f}"


def select_best_gps_sample(samples: list[dict[str, Any]]) -> dict[str, Any] | None:
    valid = [sample for sample in samples if validate_gps_evidence(sample)["status"] in {"GPS_MARKER_READY", "NO_GPS_NO_MARKER"} and _to_float(sample.get("latitude")) is not None and _to_float(sample.get("longitude")) is not None]
    if not valid:
        return None
    return sorted(valid, key=lambda item: (_to_float(item.get("accuracy")) if _to_float(item.get("accuracy")) is not None else 999999, str(item.get("timestamp") or "")))[0]


def _decimal_count(text: str) -> int:
    if "." not in text:
        return 0
    return len(text.split(".", 1)[1].rstrip("0"))


def _is_stale_timestamp(value: Any, *, max_age_seconds: int = 300) -> bool:
    if not value:
        return False
    text = str(value).replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return False
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return (datetime.now(timezone.utc) - parsed.astimezone(timezone.utc)).total_seconds() > max_age_seconds


def _dedupe(values: list[str]) -> list[str]:
    result: list[str] = []
    for value in values:
        if value and value not in result:
            result.append(value)
    return result


def _to_float(value: Any) -> float | None:
    if value in {None, ""}:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
