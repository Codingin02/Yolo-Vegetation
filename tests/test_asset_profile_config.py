from __future__ import annotations

from ulp_project.auto_measurement import load_electrical_asset_profile


def test_asset_profile_keeps_unconfirmed_references_nullable() -> None:
    profile = load_electrical_asset_profile()
    assert profile["asset_system"] == "JTM_20KV_DISTRIBUTION"
    assert profile["reference_status"] == "CONFIG_NEEDS_FIELD_CONFIRMATION"
    assert profile["pole_height_reference_m"] is None
    assert 9 in profile["pole_height_candidates_m"]
    assert "PLN" in " ".join(profile["notes"])
