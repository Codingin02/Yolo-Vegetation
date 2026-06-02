from ulp_project.clearance_estimation import estimate_phase8_clearance
from ulp_project.risk_priority import evaluate_pln_vegetation_risk


def test_clearance_eta_around_30_days_for_manual_complete_input():
    risk = evaluate_pln_vegetation_risk(
        0.3,
        "pohon_sono",
        environment={"season_label": "manual", "rainfall_30d_mm": 100, "soil_ph": 6.5, "soil_moisture_proxy": "manual"},
        allow_provisional=True,
        base_growth_rate_override=0.01,
    )
    assert risk["days_to_contact_p50"] == 30.0
    assert risk["risk_priority"] == "CRITICAL"


def test_clearance_less_equal_zero_is_danger_now():
    risk = evaluate_pln_vegetation_risk(
        0,
        "pohon_sono",
        environment={"season_label": "manual", "rainfall_30d_mm": 100, "soil_ph": 6.5, "soil_moisture_proxy": "manual"},
        allow_provisional=True,
        base_growth_rate_override=0.01,
    )
    assert risk["risk_priority"] == "DANGER_NOW"


def test_phase8_clearance_needs_data_without_asset_height():
    clearance = estimate_phase8_clearance(crown_top_m=4.0, asset_height_m=None)
    assert clearance["clearance_status"] == "INSUFFICIENT_DATA"
