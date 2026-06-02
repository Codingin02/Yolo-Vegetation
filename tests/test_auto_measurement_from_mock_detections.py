from __future__ import annotations

from ulp_project.auto_measurement import measure_from_detections


def test_mock_pole_tree_cable_measurement_outputs_clearance() -> None:
    detections = [
        {"class_name": "P001_struktur_penyangga", "bbox": [100, 100, 140, 500], "confidence": 0.9},
        {"class_name": "V001_pohon_sono", "bbox": [250, 260, 320, 500], "confidence": 0.9},
        {"class_name": "K001_konduktor", "bbox": [80, 180, 360, 190], "confidence": 0.8},
    ]
    result = measure_from_detections(detections, asset_profile={"pole_height_reference_m": 12}, stabilize=False)
    assert result["measurement_status"] == "AUTO_MEASUREMENT_READY"
    assert result["tree_height_m"] == 7.2
    assert result["pole_height_m"] == 12.0
    assert result["cable_height_m"] == 9.45
    assert result["clearance_to_cable_m"] == 2.25
    assert result["selected_clearance_m"] == 2.25
    assert result["selected_hazard_target"] in {"cable", "span"}
    assert result["not_accuracy_claim"] is True
