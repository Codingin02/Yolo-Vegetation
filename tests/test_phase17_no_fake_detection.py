from ulp_project.inference_model_adapter import run_model_inference


def test_demo_mock_requires_explicit_flag():
    normal = run_model_inference(None)
    demo = run_model_inference(None, demo_mock=True)
    assert normal["detections"] == []
    assert demo["source"] == "DEMO_MOCK_ONLY"
