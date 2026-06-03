from __future__ import annotations

from ulp_project.phase5_2_field_trial import build_manual_prediction


def test_phase5_2_no_model_manual_prediction_still_runs() -> None:
    result = build_manual_prediction({"point_id": "V001_pohon_sono"})
    assert result["model_status"] == "MODEL_NOT_READY"
    assert result["detections"] == []
    assert result["status"] == "MANUAL_PROVISIONAL_INSUFFICIENT_DATA"


def test_phase5_2_manual_eta_uses_3m_threshold() -> None:
    result = build_manual_prediction(
        {
            "point_id": "V001_pohon_sono",
            "species": "pohon_sono",
            "asset_type": "span",
            "clearance_m": 5.0,
            "growth_rate_m_per_day": 0.01,
            "measurement_source": "manual",
        }
    )
    assert result["clearance_threshold_m"] == 3.0
    assert result["eta_days"] == 200.0
    assert result["risk_status"] == "ETA_TO_3M_THRESHOLD_READY"
    assert result["not_accuracy_claim"] is True


def test_phase5_2_unsafe_clearance_eta_zero_and_floor_display() -> None:
    result = build_manual_prediction({"clearance_m": 2.75, "growth_rate_m_per_day": 0.01})
    assert result["clearance_raw_m"] == 2.75
    assert result["clearance_display_m_integer_floor"] == 2
    assert result["eta_days"] == 0
    assert result["risk_status"] == "ALREADY_WITHIN_UNSAFE_ZONE"
    assert result["action_priority"] == "CRITICAL"
