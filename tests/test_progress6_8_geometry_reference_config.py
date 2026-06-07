from __future__ import annotations

from ulp_project.geometry_reference_scaling import compute_reference_geometry, load_geometry_reference_config


def test_progress6_8_geometry_reference_config_not_final() -> None:
    config = load_geometry_reference_config()
    assert config["reference_policy"] == "CONFIGURABLE_FIELD_REFERENCE_NOT_FINAL"
    assert config["default_reference_status"] == "NEEDS_PLN_CONFIRMATION"
    assert float(config["default_reference_pole_height_m"]) == 12.0


def test_progress6_8_geometry_candidate_with_mock_multiclass_boxes() -> None:
    result = compute_reference_geometry(
        [
            {"class_name": "struktur_penyangga", "bbox_xyxy": [100, 100, 140, 700]},
            {"class_name": "konduktor", "bbox_xyxy": [10, 220, 650, 240]},
            {"class_name": "pohon_sono", "bbox_xyxy": [260, 360, 520, 680]},
        ]
    )
    assert result["geometry_status"] == "GEOMETRY_READY_CANDIDATE"
    assert result["reference_status"] == "NEEDS_PLN_CONFIRMATION"
    assert result["no_fake_clearance"] is True
