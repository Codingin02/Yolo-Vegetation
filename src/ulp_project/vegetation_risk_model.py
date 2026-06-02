"""Phase 6 pohon_sono vegetation risk model skeleton.

The scoring is deterministic and operator-facing. It is not an accuracy claim,
not an ML model, and not a substitute for field validation.
"""

from __future__ import annotations

from typing import Any

from .risk_explainability import confidence_from_missing, rank_explanation_factors

DEFAULT_AREA = "Surabaya Utara - Perak"
SPECIES = "pohon_sono"

REQUIRED_CONTEXT_FIELDS = ["point_id"]
ENVIRONMENTAL_FIELDS = [
    "temperature_2m_c",
    "relative_humidity_2m_percent",
    "rainfall_7d_mm",
    "rainfall_30d_mm",
    "dry_days_count_14d",
    "wind_speed_10m_ms",
    "wind_gust_ms",
    "soil_ph",
    "soil_clay_percent",
    "soil_sand_percent",
    "soil_silt_percent",
]


def _to_float(value: Any) -> float | None:
    try:
        if value in (None, ""):
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _clamp_score(value: float) -> int:
    return int(max(0, min(100, round(value))))


def _presence(data: dict[str, Any], fields: list[str]) -> tuple[list[str], int]:
    missing = [field for field in fields if data.get(field) in (None, "")]
    return missing, len(fields) - len(missing)


def score_pohon_sono_risk(data: dict[str, Any], area: str = DEFAULT_AREA) -> dict[str, Any]:
    """Score risk from explicit inputs only.

    Missing environmental data lowers confidence and is reported as missing
    rather than filled with fabricated values.
    """
    species = str(data.get("species") or data.get("vegetation_class") or SPECIES)
    point_id = str(data.get("point_id") or "")
    required_missing, _ = _presence(data, REQUIRED_CONTEXT_FIELDS)
    environmental_missing, environmental_present = _presence(data, ENVIRONMENTAL_FIELDS)

    factors: list[dict[str, Any]] = []
    if environmental_present == 0 and _to_float(data.get("distance_to_conductor_m")) is None and _to_float(data.get("current_clearance_m")) is None:
        return {
            "status": "ENVIRONMENTAL_DATA_NOT_READY",
            "species": species,
            "area": area,
            "point_id": point_id,
            "growth_pressure_score": None,
            "trimming_urgency_score": None,
            "electrical_clearance_risk": None,
            "environmental_growth_index": None,
            "confidence_level": "LOW",
            "data_quality_flags": (["NO_REQUIRED_CONTEXT"] if required_missing else []) + ["NO_ENVIRONMENTAL_INPUTS", "VISION_CLEARANCE_NOT_READY"],
            "top_factors": [],
            "missing_sources": required_missing + environmental_missing,
            "operator_note": "Isi data GPS/lingkungan manual atau tunggu hasil model sebelum memakai skor operasional.",
            "not_accuracy_claim": True,
        }

    rainfall_7d = _to_float(data.get("rainfall_7d_mm"))
    rainfall_30d = _to_float(data.get("rainfall_30d_mm"))
    humidity = _to_float(data.get("relative_humidity_2m_percent") or data.get("humidity_percent"))
    temp = _to_float(data.get("temperature_2m_c") or data.get("temperature_c"))
    dry_days = _to_float(data.get("dry_days_count_14d"))
    wind = _to_float(data.get("wind_speed_10m_ms"))
    gust = _to_float(data.get("wind_gust_ms"))
    soil_ph = _to_float(data.get("soil_ph"))
    clearance = _to_float(data.get("distance_to_conductor_m") or data.get("current_clearance_m"))

    growth_score = 0.0
    if rainfall_7d is not None:
        contribution = min(25.0, rainfall_7d / 4.0)
        growth_score += contribution
        factors.append({"factor": "rainfall_7d_mm", "impact": contribution, "note": "Curah hujan 7 hari menaikkan tekanan tumbuh."})
    if rainfall_30d is not None:
        contribution = min(20.0, rainfall_30d / 12.0)
        growth_score += contribution
        factors.append({"factor": "rainfall_30d_mm", "impact": contribution, "note": "Curah hujan 30 hari mendukung potensi pertumbuhan."})
    if humidity is not None:
        contribution = max(0.0, min(15.0, (humidity - 55.0) / 3.0))
        growth_score += contribution
        factors.append({"factor": "relative_humidity_2m_percent", "impact": contribution, "note": "Kelembapan tinggi mendukung pertumbuhan vegetasi."})
    if temp is not None:
        contribution = max(0.0, 15.0 - abs(temp - 29.0) * 2.0)
        growth_score += contribution
        factors.append({"factor": "temperature_2m_c", "impact": contribution, "note": "Suhu tropis stabil mendukung pertumbuhan."})
    if dry_days is not None:
        contribution = -min(20.0, dry_days * 1.5)
        growth_score += contribution
        factors.append({"factor": "dry_days_count_14d", "impact": contribution, "note": "Hari kering menurunkan tekanan tumbuh tetapi perlu cek ranting kering."})
    if soil_ph is not None:
        contribution = 10.0 if 5.5 <= soil_ph <= 7.5 else -5.0
        growth_score += contribution
        factors.append({"factor": "soil_ph", "impact": contribution, "note": "pH tanah dipakai sebagai indikasi kecocokan tumbuh, bukan klaim final."})

    environmental_growth_index = _clamp_score(growth_score)

    if clearance is None:
        clearance_risk: int | None = None
        factors.append({"factor": "distance_to_conductor_m", "impact": 0, "note": "Jarak belum tersedia; tunggu kalibrasi/vision."})
    elif clearance < 1.5:
        clearance_risk = 100
        factors.append({"factor": "distance_to_conductor_m", "impact": 100, "note": "Jarak di bawah ambang operasional 1.5 m."})
    elif clearance < 3.0:
        clearance_risk = _clamp_score(75 - (clearance - 1.5) * 20)
        factors.append({"factor": "distance_to_conductor_m", "impact": clearance_risk, "note": "Jarak berada pada zona peringatan 1.5-3.0 m."})
    else:
        clearance_risk = _clamp_score(max(10.0, 45.0 - (clearance - 3.0) * 10))
        factors.append({"factor": "distance_to_conductor_m", "impact": clearance_risk, "note": "Jarak di atas 3.0 m, tetap perlu monitoring rutin."})

    wind_risk = 0.0
    if wind is not None:
        wind_risk += min(20.0, wind * 3.0)
    if gust is not None:
        wind_risk += min(25.0, gust * 2.0)
    if wind_risk:
        factors.append({"factor": "wind_or_gust", "impact": wind_risk, "note": "Angin/gust dapat menaikkan risiko ayunan cabang."})

    dry_branch_risk = min(20.0, (dry_days or 0.0) * 1.2)
    if dry_branch_risk:
        factors.append({"factor": "dry_branch_proxy", "impact": dry_branch_risk, "note": "Hari kering menjadi proxy risiko ranting kering."})

    if clearance_risk is None:
        trimming_urgency = _clamp_score(environmental_growth_index * 0.55 + wind_risk + dry_branch_risk)
        electrical_risk_value = None
    else:
        electrical_risk_value = _clamp_score(clearance_risk + wind_risk * 0.6)
        trimming_urgency = _clamp_score(electrical_risk_value * 0.65 + environmental_growth_index * 0.35 + dry_branch_risk)

    confidence = confidence_from_missing(REQUIRED_CONTEXT_FIELDS, required_missing, environmental_present)
    if clearance is None or environmental_present < 4:
        confidence = "LOW" if environmental_present < 4 else "MEDIUM"

    data_quality_flags = []
    if environmental_missing:
        data_quality_flags.append("ENVIRONMENTAL_DATA_PARTIAL")
    if clearance is None:
        data_quality_flags.append("VISION_CLEARANCE_NOT_READY")
    if data.get("urban_surface_proxy") in (None, ""):
        data_quality_flags.append("URBAN_SURFACE_UNCERTAINTY")

    status = "RULE_BASED_STUB" if environmental_present or clearance is not None else "ENVIRONMENTAL_DATA_NOT_READY"
    return {
        "status": status,
        "species": species,
        "area": area,
        "point_id": point_id,
        "growth_pressure_score": environmental_growth_index,
        "trimming_urgency_score": trimming_urgency,
        "electrical_clearance_risk": electrical_risk_value,
        "environmental_growth_index": environmental_growth_index,
        "confidence_level": confidence,
        "data_quality_flags": data_quality_flags,
        "top_factors": rank_explanation_factors(factors),
        "missing_sources": required_missing + environmental_missing,
        "operator_note": "Skor ini rule-based untuk prioritas kerja; akurasi akhir menunggu label, training, data lapangan, dan validasi ground truth.",
        "not_accuracy_claim": True,
    }
