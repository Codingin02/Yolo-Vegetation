from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_progress6_6_report_result_no_duplicate_fields_and_compact_details() -> None:
    report = (ROOT / "src" / "ulp_project" / "templates" / "field_report.html").read_text(encoding="utf-8")
    result = (ROOT / "src" / "ulp_project" / "templates" / "field_result.html").read_text(encoding="utf-8")
    for token in ["point_id", "base_accuracy_m", "current_accuracy_m", "tree_detected"]:
        assert report.count(f"<dt>{token}</dt>") <= 1
    assert report.count("<h2>Operator Notes</h2>") <= 1
    assert "Developer Detail" in report
    assert "Developer Detail" in result
    assert "renderChips" in report
    assert "renderChips" in result
    assert "Growth Prior" in report
    assert "Growth Prior" in result
