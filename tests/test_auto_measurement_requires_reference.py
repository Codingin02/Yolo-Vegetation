from __future__ import annotations

from ulp_project.auto_measurement import measure_from_detections


def test_auto_measurement_requires_pole_reference_height() -> None:
    detections = [
        {"class_name": "struktur_penyangga", "bbox": [100, 100, 140, 500], "confidence": 0.9},
        {"class_name": "pohon_sono", "bbox": [250, 260, 320, 500], "confidence": 0.9},
        {"class_name": "konduktor", "bbox": [80, 180, 360, 190], "confidence": 0.8},
    ]
    result = measure_from_detections(detections, asset_profile={"pole_height_reference_m": None, "reference_status": "CONFIG_NEEDS_FIELD_CONFIRMATION"})
    assert result["measurement_status"] == "REFERENCE_HEIGHT_REQUIRED"
    assert result["selected_clearance_m"] is None


def test_auto_measurement_requires_reference_object() -> None:
    result = measure_from_detections([{"class_name": "pohon_sono", "bbox": [250, 260, 320, 500], "confidence": 0.9}], asset_profile={"pole_height_reference_m": 12})
    assert result["measurement_status"] == "INSUFFICIENT_REFERENCE_OBJECT"
