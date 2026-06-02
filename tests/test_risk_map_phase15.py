from __future__ import annotations

from ulp_project.phase9_monitoring import build_phase9_monitoring_row, write_phase9_risk_map


def test_phase15_map_marker_only_when_gps_valid(tmp_path) -> None:
    no_gps = write_phase9_risk_map(build_phase9_monitoring_row({"point_id": "V001"}), output=tmp_path / "map.html")
    assert no_gps["written"] is False
    with_gps = write_phase9_risk_map(
        build_phase9_monitoring_row(
            {
                "point_id": "V001",
                "latitude": "-7.0",
                "longitude": "112.0",
                "eta_days": 30,
                "risk_priority": "CRITICAL",
                "selected_hazard_target": "cable",
            }
        ),
        output=tmp_path / "map.html",
    )
    assert with_gps["written"] is True
    assert (tmp_path / "map.html").exists()
