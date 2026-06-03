from __future__ import annotations

from ulp_project.inference_model_adapter import run_model_inference
from ulp_project.phase5_2_field_trial import build_manual_prediction


def test_phase5_2_missing_model_never_emits_fake_detections() -> None:
    inference = run_model_inference(None)
    prediction = build_manual_prediction({"clearance_m": 5.0, "growth_rate_m_per_day": 0.01})
    assert inference["status"] == "MODEL_NOT_READY"
    assert inference["detections"] == []
    assert prediction["model_status"] == "MODEL_NOT_READY"
    assert prediction["detections"] == []
    assert prediction["no_fake_detection"] is True
