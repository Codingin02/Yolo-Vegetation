from __future__ import annotations

from pathlib import Path

from ulp_project.phase5_2_field_trial import build_manual_prediction, build_report_row, write_field_trial_map, write_field_trial_snapshot_report


def test_phase5_2_no_gps_does_not_create_map_marker(tmp_path) -> None:
    prediction = build_manual_prediction({"clearance_m": 5.0, "growth_rate_m_per_day": 0.01})
    row = build_report_row(prediction, report_id="no_gps", timestamp="2026-06-04T00:00:00")
    result = write_field_trial_map(row, tmp_path / "map.html")
    assert result["written"] is False
    assert result["status"] == "NO_GPS_NO_MARKER"
    assert not Path(result["path"]).exists()


def test_phase5_2_dummy_gps_is_labeled_not_field_data(tmp_path) -> None:
    result = write_field_trial_snapshot_report(
        {
            "point_id": "V001_pohon_sono",
            "clearance_m": 5.0,
            "growth_rate_m_per_day": 0.01,
            "latitude": -7.0,
            "longitude": 112.0,
            "gps_source": "test_internal",
        },
        output=tmp_path / "snapshot.csv",
        map_output=tmp_path / "map.html",
    )
    assert result["map_status"] == "TEST_INTERNAL_NOT_FIELD_DATA"
    assert result["row"]["gps_source"] == "TEST_INTERNAL_NOT_FIELD_DATA"
