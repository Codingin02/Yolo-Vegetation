from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_progress6_7_report_result_links_are_session_specific_and_compact() -> None:
    report = (ROOT / "src" / "ulp_project" / "templates" / "field_report.html").read_text(encoding="utf-8")
    camera = (ROOT / "src" / "ulp_project" / "templates" / "field_camera.html").read_text(encoding="utf-8")
    for token in ["point_id", "base_accuracy_m", "current_accuracy_m", "tree_detected"]:
        assert report.count(f"<dt>{token}</dt>") <= 1
    assert "/api/field/latest-map" not in camera
    assert "field-spreadsheet/session" in (ROOT / "src" / "ulp_project" / "static" / "field_session.js").read_text(encoding="utf-8")
