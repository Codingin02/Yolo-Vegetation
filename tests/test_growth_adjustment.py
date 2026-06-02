from __future__ import annotations

from ulp_project.realtime_eta_pipeline import adjusted_growth_from_profile


def test_pohon_sono_provisional_growth_profile_available() -> None:
    result = adjusted_growth_from_profile("pohon_sono", {})
    assert result["adjusted_growth_rate_m_per_day"] == 0.01
    assert result["confidence_status"] == "PROVISIONAL_OPERATOR_CONFIG"


def test_vegetation_other_requires_confirmation() -> None:
    result = adjusted_growth_from_profile("vegetation_other", {})
    assert result["adjusted_growth_rate_m_per_day"] is None
    assert "base_growth_rate_m_per_day" in result["missing_inputs"]
