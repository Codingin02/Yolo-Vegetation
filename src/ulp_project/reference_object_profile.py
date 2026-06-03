"""Reference object profile helpers for field calibration."""

from __future__ import annotations

from typing import Any


VALID_REFERENCE_TYPES = {"struktur_penyangga_20kv", "known_marker", "manual_reference"}


def normalize_reference_type(value: str | None) -> str:
    raw = (value or "").strip()
    return raw if raw in VALID_REFERENCE_TYPES else "manual_reference"


def build_reference_profile(reference_type: str | None, known_height_m: float | None) -> dict[str, Any]:
    return {
        "reference_type": normalize_reference_type(reference_type),
        "known_height_m": known_height_m,
        "height_source_status": "OPERATOR_PROVIDED_REQUIRED" if known_height_m is None else "OPERATOR_PROVIDED",
    }
