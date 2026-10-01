from __future__ import annotations

from io import BytesIO
from pathlib import Path

import cv2
import numpy as np
import pytest
import ultralytics

from scripts import train_detector
from vegetation_monitoring import detection, geometry, growth, pipeline, predictor
from vegetation_monitoring.app import create_app
from vegetation_monitoring.storage import PROJECT_ROOT, read_json, session_file


def test_capture_flow_is_safe_without_tree_model(tmp_path, monkeypatch):
    monkeypatch.setenv("VEGETATION_DATA_ROOT", str(tmp_path / "data"))
    monkeypatch.setenv("ENABLE_EXTERNAL_AI", "false")
    baseline_available = detection.BASELINE_MODEL_PATH.is_file()
    app = create_app({"TESTING": True})
    client = app.test_client()
    assert app.config["MAX_CONTENT_LENGTH"] == 4 * 1024 * 1024

    home = client.get("/vegetation")
    assert home.status_code == 200
    assert home.headers["X-Content-Type-Options"] == "nosniff"
    assert home.headers["Referrer-Policy"] == "strict-origin-when-cross-origin"
    assert home.headers["X-Frame-Options"] == "DENY"
    assert "frame-ancestors 'none'" in home.headers["Content-Security-Policy"]
    assert home.headers["Permissions-Policy"] == "camera=(self), microphone=(), geolocation=()"
    assert "Access-Control-Allow-Origin" not in home.headers
    assert "Strict-Transport-Security" not in home.headers
    assert b'<select id="location" name="location" required>' in home.data
    assert b'<option value="surabaya">Surabaya</option>' in home.data
    assert home.data.count(b"<option") == 2
    assert b'name="location_name"' not in home.data
    unsupported_location = client.post("/api/vegetation/session/start", json={"location": "sidoarjo"})
    assert unsupported_location.status_code == 400
    health = client.get("/api/vegetation/status").get_json()
    assert health["realtime_route"] == "/api/vegetation/realtime/frame"
    assert health["backend_ready"] is True
    assert health["realtime_runtime_ready"] is baseline_available
    assert health["detector"] == {
        "mode": "baseline",
        "model": "models/yolov8n.pt",
        "ready": baseline_available,
        "status": "ready" if baseline_available else "model_not_ready",
    }
    assert health["tracking"]["status"] == ("ready" if baseline_available else "unavailable")
    assert health["prediction"]["status"] == "available_with_required_inputs"
    assert health["angsana_model_ready"] is False

    started = client.post("/api/vegetation/session/start", json={"location": "surabaya"})
    assert started.status_code == 201
    session_id = started.get_json()["session_id"]
    metadata = read_json(session_file(session_id, "metadata.json"))
    assert metadata["location"] == "surabaya"
    assert metadata["location_name"] == "Surabaya"
    capture_page = client.get(started.get_json()["capture_url"])
    assert capture_page.status_code == 200
    assert b"Mulai deteksi" in capture_page.data
    assert b'id="lighting-button"' in capture_page.data
    assert b"Cahaya: Auto" in capture_page.data
    assert b'id="flash-button"' in capture_page.data
    assert b'aria-pressed="false"' in capture_page.data
    assert capture_page.data.count(b"<video") == 1
    assert b'<canvas id="detection-overlay"' in capture_page.data
    assert b'id="preview"' not in capture_page.data
    assert b"<img" not in capture_page.data

    success, image_buffer = cv2.imencode(".jpg", np.full((480, 320, 3), (0, 128, 0), dtype=np.uint8))
    assert success
    image_bytes = image_buffer.tobytes()
    invalid_frame = client.post(
        "/api/vegetation/realtime/frame",
        data={"session_id": session_id, "frame": (BytesIO(b"not-an-image"), "frame.jpg")},
        content_type="multipart/form-data",
    )
    assert invalid_frame.status_code == 400
    assert invalid_frame.get_json() == {"status": "frame_rejected", "error": "invalid frame"}
    invalid_type = client.post(
        "/api/vegetation/realtime/frame",
        data={"session_id": session_id, "frame": (BytesIO(image_bytes), "frame.jpg", "text/plain")},
        content_type="multipart/form-data",
    )
    assert invalid_type.status_code == 400
    oversized = client.post(
        "/api/vegetation/realtime/frame",
        data={
            "session_id": session_id,
            "frame": (BytesIO(b"\xff\xd8\xff" + b"0" * (4 * 1024 * 1024)), "frame.jpg", "image/jpeg"),
        },
        content_type="multipart/form-data",
    )
    assert oversized.status_code == 413
    assert oversized.get_json()["status"] == "request_too_large"
    assert client.get("/api/vegetation/status").status_code == 200
    sample_path = Path(ultralytics.__file__).resolve().parent / "assets" / "bus.jpg"
    realtime_bytes = sample_path.read_bytes() if baseline_available and sample_path.is_file() else image_bytes
    realtime_frame = cv2.imdecode(np.frombuffer(realtime_bytes, dtype=np.uint8), cv2.IMREAD_COLOR)
    render_calls = 0
    detect_calls = 0
    render_result = pipeline.render_result
    detect_objects = pipeline.detect_objects

    def count_render(*args, **kwargs):
        nonlocal render_calls
        render_calls += 1
        return render_result(*args, **kwargs)

    def count_detect(*args, **kwargs):
        nonlocal detect_calls
        detect_calls += 1
        return detect_objects(*args, **kwargs)

    monkeypatch.setattr(pipeline, "render_result", count_render)
    monkeypatch.setattr(pipeline, "detect_objects", count_detect)
    realtime = client.post(
        "/api/vegetation/realtime/frame",
        data={"session_id": session_id, "frame": (BytesIO(realtime_bytes), "frame.jpg")},
        content_type="multipart/form-data",
    )
    assert realtime.status_code == 200
    realtime_result = realtime.get_json()
    assert realtime_result["detector_status"] == ("ready" if baseline_available else "model_not_ready")
    assert realtime_result["detector"] == {
        "mode": "baseline",
        "model": "models/yolov8n.pt",
        "ready": baseline_available,
        "status": "ready" if baseline_available else "model_not_ready",
        "error": None,
    }
    assert realtime_result["tracking_status"] == ("active" if baseline_available else "unavailable")
    assert realtime_result["lighting"]["mode"] == "auto"
    assert "annotated_image" not in realtime_result
    assert realtime_result["frame"] == {"width": realtime_frame.shape[1], "height": realtime_frame.shape[0]}
    assert render_calls == 0
    assert detect_calls == 1
    assert realtime_result["prediction"]["prediction_status"] == "not_applicable"
    assert all({"class", "confidence", "bbox_xyxy", "track_id"} <= item.keys() for item in realtime_result["detections"])
    assert not {item["class"] for item in realtime_result["detections"]} & set(detection.TREE_CLASSES)
    if baseline_available and sample_path.is_file():
        assert realtime_result["detection_count"] > 0
        first_tracks = {(item["class_name"], item["track_id"]) for item in realtime_result["detections"]}
        assert all(track_id is not None for _, track_id in first_tracks)
        second_realtime = client.post(
            "/api/vegetation/realtime/frame",
            data={"session_id": session_id, "frame": (BytesIO(realtime_bytes), "frame.jpg")},
            content_type="multipart/form-data",
        ).get_json()
        assert {(item["class_name"], item["track_id"]) for item in second_realtime["detections"]} == first_tracks

    def fail_prediction(**_):
        raise RuntimeError("prediction unavailable")

    with monkeypatch.context() as prediction_failure:
        prediction_failure.setattr(growth, "_predict_growth", fail_prediction)
        non_blocking = client.post(
            "/api/vegetation/realtime/frame",
            data={"session_id": session_id, "frame": (BytesIO(realtime_bytes), "frame.jpg")},
            content_type="multipart/form-data",
        ).get_json()
        assert non_blocking["detector"]["ready"] is baseline_available
        assert non_blocking["prediction"]["prediction_status"] == "error"
        assert non_blocking["prediction"]["error"] == "prediction unavailable"

    cloud_prediction = client.post(
        "/api/vegetation/prediction",
        json={"species": "angsana", "growth_stage": "unknown"},
    )
    assert cloud_prediction.status_code == 200
    assert cloud_prediction.get_json()["prediction_status"] == "insufficient_data"
    invalid_number = client.post(
        "/api/vegetation/prediction",
        json={"clearance_m": "NaN", "measurement_source": "field"},
    )
    assert invalid_number.status_code == 400
    out_of_range = client.post(
        "/api/vegetation/prediction",
        json={"clearance_m": 101, "measurement_source": "field"},
    )
    assert out_of_range.status_code == 400
    rejected = client.post(
        "/api/vegetation/session/snapshot",
        data={"session_id": session_id, "clearance_m": "1.5", "snapshot": (BytesIO(image_bytes), "capture.jpg")},
        content_type="multipart/form-data",
    )
    assert rejected.status_code == 400
    image = BytesIO(image_bytes)
    response = client.post(
        "/api/vegetation/session/snapshot",
        data={
            "session_id": session_id,
            "location_name": "Sidoarjo",
            "snapshot": (image, "capture.jpg"),
        },
        content_type="multipart/form-data",
    )
    assert response.status_code == 201
    result = response.get_json()["result"]
    assert result["detector_status"] == ("ready" if baseline_available else "model_not_ready")
    assert result["detector_role"] == "baseline_coco"
    assert result["production_detector_ready"] is False
    assert result["tracking_status"] == "disabled"
    assert result["location_name"] == "Surabaya"
    assert not {item["class_name"] for item in result["detections"]} & set(detection.TREE_CLASSES)
    assert result["clearance_m"] is None
    assert result["prediction"]["prediction_status"] == "not_applicable"
    assert "gps" not in result
    assert "external_ai_status" not in result
    assert session_file(session_id, "annotated.jpg").is_file()
    assert render_calls == 1
    assert read_json(session_file(session_id, "result.json"))["status"] == "ready"
    assert client.get(f"/vegetation/result/{session_id}").status_code == 200
    assert client.get("/vegetation/map").status_code == 404

    duplicate_image = BytesIO(image_bytes)
    duplicate = client.post(
        "/api/vegetation/session/snapshot",
        data={"session_id": session_id, "snapshot": (duplicate_image, "capture.jpg")},
        content_type="multipart/form-data",
    )
    assert duplicate.status_code == 201
    assert duplicate.get_json()["result"]["duplicate_ignored"] is True
    records = tmp_path / "data" / "runtime" / "records"
    assert len((records / "records.csv").read_text(encoding="utf-8").splitlines()) == 2
    assert len((records / "records.jsonl").read_text(encoding="utf-8").splitlines()) == 1

    feedback = client.post(
        "/api/vegetation/operator-feedback",
        json={"session_id": session_id, "decision": "rejected"},
    )
    assert feedback.status_code == 200
    assert read_json(session_file(session_id, "result.json"))["active"] is False

    flooded = [
        client.post(
            "/api/vegetation/realtime/frame",
            data={"session_id": session_id, "frame": (BytesIO(b"bad"), "frame.jpg", "image/jpeg")},
            content_type="multipart/form-data",
        )
        for _ in range(21)
    ]
    assert any(response.status_code == 429 for response in flooded)
    assert client.get("/api/vegetation/status").status_code == 200


def test_model_and_dataset_paths_are_canonical(tmp_path, monkeypatch):
    production = tmp_path / "detector.pt"
    baseline = tmp_path / "yolov8n.pt"
    baseline.touch()
    monkeypatch.setattr(detection, "PRODUCTION_MODEL_PATH", production.resolve())
    monkeypatch.setattr(detection, "BASELINE_MODEL_PATH", baseline.resolve())
    assert detection.model_path() == baseline.resolve()
    assert detection.detector_mode() == "baseline"
    production.touch()
    assert detection.model_path() == production.resolve()
    assert detection.detector_mode() == "production"

    config = (PROJECT_ROOT / "data" / "dataset" / "data.yaml").read_text(encoding="utf-8")
    assert [line.strip() for line in config.splitlines() if line.strip().startswith(("0:", "1:", "2:"))] == [
        "0: angsana",
        "1: konduktor",
        "2: struktur_penyangga_sutm",
    ]
    assert detection.PRODUCTION_CLASSES == geometry.REQUIRED_CLASSES == (
        "angsana",
        "konduktor",
        "struktur_penyangga_sutm",
    )
    assert detection.TREE_METADATA["angsana"] == {
        "display_name": "Angsana",
        "scientific_name": "Pterocarpus indicus",
    }
    geometry_result = geometry.build_geometry_contract(
        [
            {"class_name": "angsana", "mask_polygon_xyn": [[0.1, 0.1], [0.2, 0.1], [0.1, 0.2]]},
            {"class_name": "konduktor", "mask_polygon_xyn": [[0.4, 0.2], [0.8, 0.2], [0.8, 0.21]]},
        ],
        capture_distance_m=10,
    )
    assert geometry_result["status"] == "camera_calibration_required"
    assert geometry_result["thresholds"]["action_threshold_m"] is None
    assert geometry_result["thresholds"]["monitor_threshold_m"] is None
    assert geometry_result["thresholds"]["ready"] is False
    assert all(value is None for value in geometry_result["measurements"].values())
    assert geometry_result["risk_status"] == "not_computed"
    assert train_detector.BASE_MODEL.name == "yolov8m-seg.pt"
    assert train_detector.CLASS_NAMES == ("angsana", "konduktor", "struktur_penyangga_sutm")
    assert train_detector.TRAIN_IMAGE_SIZE == 1024
    monkeypatch.setattr(train_detector.torch.cuda, "is_available", lambda: True)
    gpu_device, gpu_batch, gpu_amp, workers = train_detector._training_options(None, None)
    assert (gpu_device, gpu_batch, gpu_amp) == (0, -1, True)
    assert 1 <= workers <= 4
    monkeypatch.setattr(train_detector.torch.cuda, "is_available", lambda: False)
    assert train_detector._training_options(None, None)[:3] == ("cpu", 2, False)
    valid_polygon = tmp_path / "valid-segment.txt"
    valid_polygon.write_text("0 0.1 0.1 0.2 0.1 0.1 0.2\n", encoding="utf-8")
    train_detector._validate_label(valid_polygon)
    invalid_box = tmp_path / "bbox-only.txt"
    invalid_box.write_text("0 0.5 0.5 0.2 0.2\n", encoding="utf-8")
    with pytest.raises(SystemExit, match="Invalid segmentation polygon"):
        train_detector._validate_label(invalid_box)
    first_asset = tmp_path / "first.bin"
    second_asset = tmp_path / "second.bin"
    first_asset.write_bytes(b"same bytes")
    second_asset.write_bytes(b"same bytes")
    checksum = train_detector._sha256(first_asset)
    assert checksum == train_detector._sha256(second_asset)
    seen_checksums = {}
    train_detector._claim_checksum(seen_checksums, checksum, "first")
    with pytest.raises(SystemExit, match="Exact duplicate image"):
        train_detector._claim_checksum(seen_checksums, checksum, "second")
    training_source = (PROJECT_ROOT / "scripts" / "train_detector.py").read_text(encoding="utf-8")
    assert "mosaic=0.25" in training_source
    assert "close_mosaic=10" in training_source
    assert "perspective=0.0" in training_source
    assert "shear=0.0" in training_source
    deduplicated = detection._suppress_duplicate_detections(
        [
            {"class_name": "book", "confidence": 0.91, "bbox_xyxy": [0, 0, 100, 100], "track_id": 1},
            {"class_name": "book", "confidence": 0.62, "bbox_xyxy": [5, 5, 95, 95], "track_id": 2},
            {"class_name": "cell phone", "confidence": 0.80, "bbox_xyxy": [5, 5, 95, 95], "track_id": 3},
        ]
    )
    assert [item["track_id"] for item in deduplicated] == [1, 3]

    backlit = np.full((180, 320, 3), 235, dtype=np.uint8)
    backlit[36:144, 80:240] = 40
    enhanced_backlit, backlight = pipeline._adaptive_lighting(backlit, "auto", "test-backlight")
    assert backlight["scene"] == "backlight"
    assert backlight["foreground_mean"] < backlight["global_mean"]
    assert backlight["correction_strength"] > 0.8
    assert 0.35 <= backlight["gamma"] < 0.55
    assert enhanced_backlit[50:130, 100:220].mean() > backlit[50:130, 100:220].mean() + 30
    assert enhanced_backlit[:20].mean() <= backlit[:20].mean() + 8
    assert backlight["clahe_strength"] > 0
    assert backlight["clahe_clip_limit"] == 2.3

    low_light_frame = np.full((180, 320, 3), 45, dtype=np.uint8)
    enhanced_low_light, low_light = pipeline._adaptive_lighting(low_light_frame, "low_light", "test-low-light")
    assert low_light["scene"] == "low_light"
    assert low_light["highlight_ratio"] == 0
    assert low_light["correction_strength"] > 0.8
    assert low_light["gamma"] < 0.55
    assert low_light["clahe_clip_limit"] == 2.4
    assert enhanced_low_light.mean() > low_light_frame.mean() + 30

    samples = []
    for value in (45, 110, 135, 160):
        source = np.full((180, 320, 3), value, dtype=np.uint8)
        enhanced, lighting = pipeline._adaptive_lighting(source, "auto", f"test-strength-{value}")
        samples.append((enhanced, lighting))
    assert samples[0][1]["correction_strength"] > samples[1][1]["correction_strength"]
    assert samples[1][1]["correction_strength"] > samples[2][1]["correction_strength"]
    assert samples[2][1]["correction_strength"] > samples[3][1]["correction_strength"]
    assert samples[0][1]["gamma"] < 0.55
    assert 0.3 < samples[1][1]["correction_strength"] < 0.8
    assert samples[3][1]["correction_strength"] == 0
    assert abs(float(samples[3][0].mean()) - 160) < 1

    bright_frame = np.full((180, 320, 3), 180, dtype=np.uint8)
    enhanced_bright, bright = pipeline._adaptive_lighting(bright_frame, "auto", "test-bright")
    assert bright["scene"] == "normal"
    assert bright["gamma"] == 1
    assert bright["correction_strength"] == 0
    assert bright["clahe_strength"] == 0
    assert np.array_equal(enhanced_bright, bright_frame)

    unchanged, manual_normal = pipeline._adaptive_lighting(backlit, "normal", "test-normal")
    assert manual_normal["scene"] == "normal"
    assert manual_normal["gamma"] == 1
    assert manual_normal["correction_strength"] == 0
    assert manual_normal["clahe_strength"] == 0
    assert np.array_equal(unchanged, backlit)
    forced_backlight = pipeline._adaptive_lighting(backlit, "backlight", "test-forced-backlight")[1]
    assert forced_backlight["scene"] == "backlight"
    assert forced_backlight["clahe_clip_limit"] == 2.5

    raw_dark_gamma = pipeline._adaptive_lighting(low_light_frame, "auto", "test-ema-target")[1]["gamma"]
    first_gamma = pipeline._adaptive_lighting(bright_frame, "auto", "test-ema")[1]["gamma"]
    smoothed_gamma = pipeline._adaptive_lighting(low_light_frame, "auto", "test-ema")[1]["gamma"]
    assert abs(smoothed_gamma - (first_gamma * 0.65 + raw_dark_gamma * 0.35)) < 0.03

    luminance = np.full((90, 160), 235, dtype=np.uint8)
    luminance[20:60, 10:50] = 35
    tracked_roi = pipeline._foreground_roi(
        luminance,
        [{"confidence": 0.9, "bbox_xywhn": [0.1875, 0.4444, 0.25, 0.4444], "track_id": 7}],
    )
    assert tracked_roi.mean() < 50
    assert pipeline._foreground_roi(luminance, []).mean() > 200

    app_js = (PROJECT_ROOT / "src" / "vegetation_monitoring" / "static" / "app.js").read_text(encoding="utf-8")
    assert "INFERENCE_INTERVAL_MS" not in app_js
    assert "setInterval" not in app_js
    assert "requestAnimationFrame(inferenceLoop)" in app_js
    assert "if (inferenceBusy || document.hidden)" in app_js
    assert "inferenceBusy = false;" in app_js
    assert "768 / Math.max(video.videoWidth, video.videoHeight)" in app_js
    assert 'value: "auto", label: "Auto"' in app_js
    assert 'value: "normal", label: "Normal"' in app_js
    assert 'value: "backlight", label: "Backlight"' in app_js
    assert 'value: "low_light", label: "Low Light"' in app_js
    assert 'form.append("lighting_mode", lightingModes[lightingIndex].value)' in app_js
    assert 'Cahaya: ${mode.label}' in app_js
    assert "lighting.mode !== mode" in app_js
    assert "now - lastExposureAt < 650" in app_js
    assert "Math.min(1.65" in app_js
    assert "Math.min(1.20" in app_js
    assert "Math.min(0.7" in app_js
    assert "exposureCompensation" in app_js
    assert "normalExposure + (capability.max - normalExposure) * boundedRatio" in app_js
    assert 'context.filter = "none"' in app_js
    assert "cameraFrame(false)" not in app_js
    assert "brightness(1.30)" not in app_js
    assert "brightness(1.40)" not in app_js
    assert 'canvas.toBlob(resolve, "image/jpeg", 0.75)' in app_js
    assert "getCapabilities" in app_js
    assert "applyConstraints" in app_js
    assert 'classList.toggle("screen-flash", flashEnabled)' in app_js
    assert "drawDetections(payload)" in app_js
    assert "overlayContext.clearRect" in app_js
    assert "annotated_image" not in app_js
    assert 'byId("preview")' not in app_js
    assert "video.hidden = true" not in app_js
    app_css = (PROJECT_ROOT / "src" / "vegetation_monitoring" / "static" / "app.css").read_text(encoding="utf-8")
    assert ".video-stage.screen-flash::after" in app_css
    assert "border-radius: 28px" in app_css
    assert "body.screen-flash" not in app_css
    env_example = (PROJECT_ROOT / ".env.example").read_text(encoding="utf-8")
    assert "DETECTION_CONFIDENCE=0.35" in env_example

    monkeypatch.setattr(
        geometry,
        "_load_calibration",
        lambda: {
            "fx": 1000,
            "fy": 1000,
            "cx": 500,
            "cy": 500,
            "dist_coeffs": [0, 0, 0, 0, 0],
            "image_width": 1000,
            "image_height": 1000,
            "capture_distance_m": 10,
            "reprojection_error_px": 0.4,
            "capture_distance_tolerance_m": 0.2,
            "segmentation_boundary_tolerance_px": 1.0,
            "level_camera_confirmed": True,
            "common_depth_confirmed": True,
            "network_type": "SUTM",
            "voltage_kv": 20,
            "network_policy_accepted": True,
            "monitor_threshold_m": 3.5,
            "monitor_threshold_source": "local_distribution_policy",
        },
    )
    calibrated = geometry.build_geometry_contract(
        [
            {
                "class_name": "angsana",
                "confidence": 0.95,
                "track_id": 7,
                "mask_polygon_xyn": [[0.4, 0.5], [0.6, 0.5], [0.6, 0.8], [0.4, 0.8]],
            },
            {
                "class_name": "konduktor",
                "confidence": 0.95,
                "track_id": 8,
                "mask_polygon_xyn": [[0.2, 0.2], [0.8, 0.2], [0.8, 0.22], [0.2, 0.22]],
            },
        ],
        image_width=1000,
        image_height=1000,
        tree_base_visible_confirmed=True,
    )
    assert calibrated["status"] == "inputs_ready"
    assert calibrated["measurement_status"] == "ok"
    assert calibrated["risk_status"] == "PANTAU"
    assert {band["status"] for band in calibrated["risk_bands"]} == {"PANTAU", "TEBANG"}
    assert calibrated["measurements"]["clearance_m"] is not None

    valid_observation = {
        "verified": True,
        "synthetic": False,
        "fabricated": False,
        "observation_type": "individual_longitudinal",
        "species": "angsana",
        "tree_stage": "mature",
        "source_id": "field_obs_1",
        "source_url": "https://example.com",
        "tree_id": "tree-1",
        "conductor_id": "cond-1",
        "measurement_method": "calibrated_planar",
        "comparable_measurements_verified": True,
        "measurement_start_date": "2026-01-01T00:00:00+00:00",
        "measurement_end_date": "2026-01-11T00:00:00+00:00",
        "elapsed_days": 10,
        "previous_clearance_m": 4.0,
        "current_clearance_m": 3.8,
    }
    rate_result = predictor.observed_rate(valid_observation)
    assert rate_result["status"] == "ok"
    assert round(float(rate_result["rate_m_per_day"]), 4) == 0.02
    with pytest.raises(ValueError, match="verified_real_observations_required"):
        predictor.observed_rate({**valid_observation, "verified": False})
