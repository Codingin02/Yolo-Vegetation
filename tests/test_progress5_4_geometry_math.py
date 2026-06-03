from __future__ import annotations

from ulp_project.progress5_4_clearance_estimator import estimate_clearance_from_detections
from ulp_project.progress5_4_pixel_metric_scaling import calculate_pixel_metric_scale


def test_progress5_4_pixel_metric_scale_from_pole_reference() -> None:
    result = calculate_pixel_metric_scale(550, 11.0)

    assert result["status"] == "PIXEL_METRIC_SCALE_READY"
    assert result["meter_per_px"] == 0.02
    assert result["px_per_meter"] == 50.0


def test_progress5_4_clearance_geometry_uses_pixel_y_direction() -> None:
    detections = [
        {"class_name": "struktur_penyangga", "confidence": 0.9, "bbox_xyxy": [100, 50, 140, 600]},
        {"class_name": "konduktor", "confidence": 0.8, "bbox_xyxy": [60, 198, 420, 202]},
        {"class_name": "pohon_sono", "confidence": 0.85, "bbox_xyxy": [260, 350, 360, 600]},
    ]

    result = estimate_clearance_from_detections(detections, geometry_config={"default_pole_total_height_m": 11.0, "source_status": "TEST_CONFIG"})

    assert result["meter_per_px"] == 0.02
    assert result["pole_pixel_height"] == 550
    assert result["tree_top_px"] == 350
    assert result["cable_px"] == 200
    assert result["tree_height_m"] == 5.0
    assert result["cable_height_m"] == 8.0
    assert result["clearance_m"] == 3.0
    assert result["zone_status"] == "TEBANG"
    assert result["risk_level"] == "CRITICAL"


def test_progress5_4_geometry_without_pole_is_not_final_meter_claim() -> None:
    result = estimate_clearance_from_detections(
        [
            {"class_name": "konduktor", "confidence": 0.8, "bbox_xyxy": [60, 198, 420, 202]},
            {"class_name": "pohon_sono", "confidence": 0.85, "bbox_xyxy": [260, 350, 360, 600]},
        ]
    )

    assert result["clearance_m"] is None
    assert result["calibration_status"] == "CALIBRATION_NOT_READY"
    assert "REFERENCE_OBJECT_NOT_FOUND" in result["reason_codes"]
