"""Explainability helpers for rule-based risk outputs."""

from __future__ import annotations

from typing import Any


def rank_explanation_factors(factors: list[dict[str, Any]], limit: int = 5) -> list[dict[str, Any]]:
    """Return top factors sorted by absolute impact without inventing values."""
    normalized: list[dict[str, Any]] = []
    for factor in factors:
        impact = factor.get("impact", 0)
        try:
            numeric_impact = float(impact)
        except (TypeError, ValueError):
            numeric_impact = 0.0
        normalized.append({**factor, "impact": round(numeric_impact, 2)})
    return sorted(normalized, key=lambda item: abs(float(item.get("impact", 0))), reverse=True)[:limit]


def confidence_from_missing(required_fields: list[str], missing_fields: list[str], optional_present_count: int = 0) -> str:
    if not required_fields or missing_fields:
        return "LOW"
    if optional_present_count >= 6:
        return "HIGH"
    if optional_present_count >= 3:
        return "MEDIUM"
    return "LOW"
