from ulp_project.inference_runtime import run_camera_inference, run_image_inference, run_video_inference


def test_image_inference_without_model_returns_model_not_ready():
    result = run_image_inference("sample.jpg", model_path="missing_model.pt")
    assert result["status"] == "MODEL_NOT_READY"
    assert result["detections"] == []
    assert "Finish makesense labels" in result["next_required_action"]


def test_video_and_camera_inference_without_model():
    assert run_video_inference("sample.mp4", model_path="missing_model.pt")["status"] == "MODEL_NOT_READY"
    assert run_camera_inference(0, model_path="missing_model.pt")["status"] == "MODEL_NOT_READY"
