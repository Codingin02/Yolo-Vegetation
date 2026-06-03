from ulp_project.span_sag_estimator import asset_visibility_status, estimate_span_sag


def test_span_missing_statuses():
    assert estimate_span_sag([])["span_sag_status"] == "SPAN_NOT_DETECTED"
    assert asset_visibility_status(True, True, False) == "STRUCTURE_VISIBLE_ASSET_MISSING"
