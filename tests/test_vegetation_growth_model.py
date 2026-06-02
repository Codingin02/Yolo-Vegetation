from ulp_project.vegetation_eta import estimate_vegetation_eta
from ulp_project.vegetation_growth_model import adjusted_growth_rate


def test_growth_rate_null_returns_not_ready():
    result = estimate_vegetation_eta(1.0, "pohon_sono", environment={}, allow_provisional=True)
    assert result["eta_status"] == "GROWTH_RATE_NOT_READY"
    assert result["days_to_contact_p50"] is None


def test_environmental_missing_without_provisional_blocks_eta():
    result = adjusted_growth_rate("pohon_sono", {}, allow_provisional=False, base_growth_rate_override=0.01)
    assert result["status"] == "INSUFFICIENT_ENVIRONMENTAL_DATA"
    eta = estimate_vegetation_eta(1.0, "pohon_sono", environment={}, allow_provisional=False, base_growth_rate_override=0.01)
    assert eta["eta_status"] == "INSUFFICIENT_ENVIRONMENTAL_DATA"


def test_provisional_eta_when_allowed_and_base_rate_supplied():
    result = estimate_vegetation_eta(
        1.0,
        "pohon_sono",
        environment={},
        allow_provisional=True,
        base_growth_rate_override=0.01,
    )
    assert result["eta_status"] == "PROVISIONAL_ETA_READY"
    assert result["days_to_contact_p50"] == 100.0
