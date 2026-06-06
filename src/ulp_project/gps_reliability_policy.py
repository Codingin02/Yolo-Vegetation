"""Browser GPS reliability policy for field evidence.

Browser geolocation is useful for location evidence and rough operator movement,
but it is not a calibration source for pixel-to-meter geometry.
"""

from __future__ import annotations

import math
from typing import Any


def gps_accuracy_status(accuracy_m: Any) -> dict[str, Any]:
    accuracy = _to_float(accuracy_m)
    if accuracy is None:
        return {
            "gps_accuracy_status": "GPS_ACCURACY_UNKNOWN",
            "gps_quality_reason": "GPS_ACCURACY_UNKNOWN",
            "operator_message": "GPS belum memberi nilai akurasi.",
        }
    if accuracy <= 5.0:
        return {
            "gps_accuracy_status": "GPS_ACCURACY_GOOD",
            "gps_quality_reason": "GPS_ACCURACY_LE_5M",
            "operator_message": "GPS aktif untuk evidence lokasi lapangan.",
        }
    if accuracy <= 10.0:
        return {
            "gps_accuracy_status": "GPS_ACCURACY_MEDIUM",
            "gps_quality_reason": "GPS_ACCURACY_5_TO_10M",
            "operator_message": "GPS aktif, tetapi jarak tetap dibaca sebagai estimasi lapangan.",
        }
    return {
        "gps_accuracy_status": "GPS_ACCURACY_LOW",
        "gps_quality_reason": "GPS_ACCURACY_GT_10M",
        "operator_message": "GPS aktif, tetapi akurasi belum cukup untuk klaim jarak presisi.",
    }


def compute_haversine_meters(base: dict[str, Any] | None, current: dict[str, Any] | None) -> float | None:
    if not base or not current:
        return None
    lat1 = _to_float(base.get("latitude"))
    lon1 = _to_float(base.get("longitude"))
    lat2 = _to_float(current.get("latitude"))
    lon2 = _to_float(current.get("longitude"))
    if None in {lat1, lon1, lat2, lon2}:
        return None
    radius_m = 6_371_000.0
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lambda = math.radians(lon2 - lon1)
    a = math.sin(d_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2) ** 2
    return round(radius_m * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a)), 3)


def distance_reliability(base: dict[str, Any] | None, current: dict[str, Any] | None) -> dict[str, Any]:
    distance = compute_haversine_meters(base, current)
    base_accuracy = _to_float((base or {}).get("accuracy"))
    current_accuracy = _to_float((current or {}).get("accuracy"))
    accuracy = gps_accuracy_status(current_accuracy)
    movement_status = "GPS_NOT_READY" if distance is None else "MOVED_FROM_TREE_BASE" if distance > 0.5 else "AT_TREE_BASE"
    base_payload = {
        **accuracy,
        "horizontal_distance_from_tree_m": distance,
        "is_distance_reliable": False,
        "movement_status": movement_status,
    }
    if distance is None:
        return {**base_payload, "distance_reliability_status": "DISTANCE_NOT_AVAILABLE"}
    if base_accuracy is None or current_accuracy is None:
        return {**base_payload, "distance_reliability_status": "GPS_ACCURACY_UNKNOWN"}
    max_accuracy = max(base_accuracy, current_accuracy)
    if max_accuracy > distance:
        return {
            **base_payload,
            "distance_reliability_status": "GPS_ACCURACY_GREATER_THAN_DISTANCE",
        }
    if distance < 1.0:
        return {
            **base_payload,
            "distance_reliability_status": "DISTANCE_TOO_SMALL_FOR_GPS_RELIABILITY",
        }
    if distance >= 2 * max_accuracy:
        return {
            **base_payload,
            "distance_reliability_status": "DISTANCE_REASONABLY_RELIABLE_FOR_FIELD_EVIDENCE",
            "is_distance_reliable": True,
        }
    return {
        **base_payload,
        "distance_reliability_status": "DISTANCE_ESTIMATE_WEAK_FOR_FIELD_EVIDENCE",
    }


def _to_float(value: Any) -> float | None:
    if value in {None, ""}:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
