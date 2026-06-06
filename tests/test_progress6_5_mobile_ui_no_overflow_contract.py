from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_progress6_5_glass_css_wraps_mobile_text_and_cards() -> None:
    css = (ROOT / "src" / "ulp_project" / "static" / "field_capture_glass.css").read_text(encoding="utf-8")
    assert "overflow-wrap: anywhere" in css
    assert "word-break: break-word" in css
    assert "min-width: 0" in css
    assert "max-width: 480px" in css
    assert "grid-template-columns: 1fr !important" in css


def test_progress6_5_report_result_use_simplified_sections() -> None:
    report = (ROOT / "src" / "ulp_project" / "templates" / "field_report.html").read_text(encoding="utf-8")
    result = (ROOT / "src" / "ulp_project" / "templates" / "field_result.html").read_text(encoding="utf-8")
    assert "Session Evidence" in report
    assert "GPS Evidence" in report
    assert "Developer Detail" in report
    assert "Status Operator" in result
    assert "Reason Codes" in result
    assert "Developer Detail" in result
