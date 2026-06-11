from ulp_project.plan_c_free_vision_schema import normalize_class_name, normalize_detection_payload


def test_free_vision_schema_converts_normalized_1000_bbox():
    result = normalize_detection_payload(
        {
            "detections": [
                {
                    "class_name": "tree",
                    "bbox": [100, 200, 500, 800],
                    "bbox_format": "normalized_1000",
                    "confidence": 0.8,
                }
            ]
        },
        image_width=640,
        image_height=480,
    )

    assert result["status"] == "YOLO_COMPATIBLE_DETECTION_READY"
    detection = result["detections"][0]
    assert detection["class_id"] == 3
    assert detection["class_name"] == "pohon_non_sono"
    assert detection["bbox_xyxy"] == [64.0, 96.0, 320.0, 384.0]


def test_free_vision_schema_rejects_invalid_bbox():
    result = normalize_detection_payload(
        {"detections": [{"class_name": "wire", "bbox": [50, 50, 45, 80], "confidence": 0.9}]},
        image_width=640,
        image_height=480,
    )

    assert result["status"] == "DATA_TIDAK_CUKUP"
    assert result["detections"] == []
    assert result["rejected_detections_redacted"][0]["reason"] == "INVALID_OR_UNSUPPORTED_DETECTION"


def test_free_vision_schema_maps_allowed_synonyms_only():
    assert normalize_class_name("vegetation") == "pohon_non_sono"
    assert normalize_class_name("angsana") == "pohon_sono"
    assert normalize_class_name("power line") == "konduktor"
    assert normalize_class_name("utility pole") == "struktur_penyangga"
    assert normalize_class_name("car") is None
