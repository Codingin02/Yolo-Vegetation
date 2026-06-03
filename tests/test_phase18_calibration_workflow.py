from ulp_project.calibration_workflow import create_calibration_session, validate_calibration_payload


def test_calibration_missing_not_ready():
    assert validate_calibration_payload({})["quality_status"] == "CALIBRATION_NOT_READY"


def test_calibration_valid_scale():
    result = create_calibration_session(
        {"point_id": "V001_pohon_sono", "known_height_m": 12, "reference_bbox_height_px": 400, "image_width_px": 1280, "image_height_px": 720},
        write_runtime=False,
    )
    assert result["session"]["estimated_m_per_px"] == 0.03
    assert result["session"]["quality_status"] == "CALIBRATION_READY_MANUAL_REFERENCE"
