from __future__ import annotations

from ulp_project.phase9_monitoring import build_phase9_monitoring_row, write_phase9_risk_map
from ulp_project.realtime_eta_pipeline import run_realtime_eta_pipeline


def test_no_fake_accuracy_claim_in_eta_pipeline() -> None:
    result = run_realtime_eta_pipeline({"selected_clearance_m": 0.3}, species="pohon_sono")
    assert result["not_accuracy_claim"] is True


def test_no_fake_gps_marker_without_coordinates(tmp_path) -> None:
    result = write_phase9_risk_map(build_phase9_monitoring_row({"point_id": "V001"}), output=tmp_path / "map.html")
    assert result["written"] is False
    assert not (tmp_path / "map.html").exists()
