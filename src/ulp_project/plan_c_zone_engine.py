"""Risk zone classification for Plan C upload mode."""

from __future__ import annotations

from typing import Any


def classify_plan_c_zone(
    geometry: dict[str, Any],
    detections: list[dict[str, Any]],
    *,
    ai_validator: dict[str, Any] | None = None,
) -> dict[str, Any]:
    ai_validator = ai_validator or {}
    warnings: list[str] = []
    warnings.extend(_listify(geometry.get("warnings")))

    conductor = _best_detection(detections, "konduktor")
    tree = _best_detection(detections, "pohon_sono") or _best_detection(detections, "pohon_non_sono")
    structure = _best_detection(detections, "struktur_penyangga")
    conductor_conf = float((conductor or {}).get("confidence") or 0.0)
    if conductor is None or conductor_conf < 0.35:
        warnings.append("CONDUCTOR_CLASS_WEAK_OR_NOT_DETECTED")
        return _data_not_enough("CONDUCTOR_CLASS_WEAK_OR_NOT_DETECTED", warnings)
    if tree is None:
        return _data_not_enough("TREE_NOT_DETECTED", warnings)
    if structure is None:
        return _data_not_enough("STRUCTURE_NOT_DETECTED", warnings)

    clearance = _number(geometry.get("clearance_estimate_m"))
    if clearance is None:
        return _data_not_enough("CLEARANCE_NOT_COMPUTABLE", warnings)

    validator_text = " ".join(str(value).lower() for value in ai_validator.values() if isinstance(value, str))
    validator_serious = any(term in validator_text for term in ["serious", "contact", "overlap", "pemangkasan", "tebang"])
    suggestion = "AI_VALIDATOR_SUGGESTION" if validator_serious else ""

    if clearance <= 1.5 or validator_serious:
        zone = "ZONA_TEBANG"
    elif clearance <= 3.0:
        zone = "ZONA_PANTAU"
    else:
        zone = "ZONA_AMAN"

    return {
        "status": "PLAN_C_ZONE_READY",
        "risk_status": zone,
        "zone": zone,
        "clearance_m": round(clearance, 3),
        "manual_review_required": bool(geometry.get("manual_review_required")) or bool(suggestion),
        "warnings": warnings + ([suggestion] if suggestion else []),
    }


def _data_not_enough(reason: str, warnings: list[str]) -> dict[str, Any]:
    return {
        "status": "DATA_TIDAK_CUKUP",
        "risk_status": "DATA_TIDAK_CUKUP",
        "zone": "DATA_TIDAK_CUKUP",
        "clearance_m": None,
        "manual_review_required": True,
        "reason": reason,
        "warnings": _dedupe([*warnings, reason]),
    }


def _best_detection(detections: list[dict[str, Any]], class_name: str) -> dict[str, Any] | None:
    candidates = [item for item in detections if item.get("class_name") == class_name]
    if not candidates:
        return None
    return max(candidates, key=lambda item: float(item.get("confidence") or 0.0))


def _number(value: Any) -> float | None:
    if value in {None, ""}:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _listify(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value if str(item)]
    if value:
        return [str(value)]
    return []


def _dedupe(items: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        if item and item not in seen:
            result.append(item)
            seen.add(item)
    return result
