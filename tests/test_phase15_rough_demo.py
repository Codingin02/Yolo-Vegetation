from __future__ import annotations

from scripts.phase15_rough_realtime_auto_demo import mock_auto


def test_phase15_mock_auto_demo_passes() -> None:
    result = mock_auto()
    assert result["status"] == "PHASE15_ROUGH_REALTIME_AUTO_DEMO_PASS"
    assert result["eta"]["eta_days"] is not None
    assert result["eta"]["report_written"] is True
    assert result["eta"]["map_marker_written"] is True
    assert result["eta"]["not_accuracy_claim"] is True
