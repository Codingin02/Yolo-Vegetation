from ulp_project.realtime_inference_contract import infer_realtime_frame


def test_real_inference_contract_missing_model_no_fake_detection():
    result = infer_realtime_frame(None)
    assert result["inference_status"] == "MODEL_NOT_READY"
    assert result["detections"] == []
    assert result["not_accuracy_claim"] is True
