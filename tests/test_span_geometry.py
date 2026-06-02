from ulp_project.span_geometry import bbox_gap_pixels, estimate_span_midpoint, infer_nearest_asset_type


def test_span_midpoint_from_two_pole_bboxes():
    result = estimate_span_midpoint({"bbox": [0, 0, 10, 10]}, {"bbox": [20, 0, 30, 10]})
    assert result["status"] == "SPAN_GEOMETRY_READY"
    assert result["midpoint"] == (15.0, 5.0)


def test_bbox_gap_and_asset_normalization():
    assert bbox_gap_pixels([0, 0, 10, 10], [20, 0, 30, 10]) == 10
    assert infer_nearest_asset_type("trafo") == "transformer"
