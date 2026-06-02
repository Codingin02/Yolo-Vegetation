from __future__ import annotations

from ulp_project.span_measurement import estimate_span_lowest_point


def test_span_lowest_point_uses_lowest_image_y() -> None:
    result = estimate_span_lowest_point([(0, 100), (50, 125), (100, 98)])
    assert result["status"] == "SPAN_LOWEST_POINT_READY"
    assert result["lowest_point"] == {"x": 50, "y": 125}


def test_span_lowest_point_requires_points() -> None:
    assert estimate_span_lowest_point([])["status"] == "SPAN_NOT_DETECTED"
