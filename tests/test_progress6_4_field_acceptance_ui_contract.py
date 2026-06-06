from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_progress6_4_field_acceptance_ui_has_live_evidence_contract() -> None:
    html = (ROOT / "src" / "ulp_project" / "templates" / "field_acceptance.html").read_text(encoding="utf-8")
    for token in [
        "Re-check Evidence",
        "Open Map",
        "shutter_recorded",
        "gps_accuracy_m",
        "distance_reliability_status",
        "start_session_status",
        "stop_record_status",
        "Submit HP Evidence",
    ]:
        assert token in html
