from ulp_project.report_deduplicator import deduplicate_report
from ulp_project.report_snapshot_policy import should_write_snapshot_report


def test_report_snapshot_policy_and_dedup():
    assert should_write_snapshot_report({"report_trigger": "MANUAL_SNAPSHOT"})["write_report"] is True
    first = deduplicate_report({"session_id": "s1", "point_id": "V001", "risk_priority": "HIGH", "selected_clearance_m_stable": 2.5})
    second = deduplicate_report({"session_id": "s1", "point_id": "V001", "risk_priority": "HIGH", "selected_clearance_m_stable": 2.5})
    assert first["write_report"] is True
    assert second["write_report"] is False
