from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _count(text: str, token: str) -> int:
    return text.count(token)


def run_smoke() -> dict[str, object]:
    report = (ROOT / "src" / "ulp_project" / "templates" / "field_report.html").read_text(encoding="utf-8")
    result = (ROOT / "src" / "ulp_project" / "templates" / "field_result.html").read_text(encoding="utf-8")
    css = (ROOT / "src" / "ulp_project" / "static" / "field_capture_glass.css").read_text(encoding="utf-8")
    duplicate_tokens = ["point_id", "base_accuracy_m", "current_accuracy_m", "tree_detected"]
    checks = {
        "report_developer_detail_closed": "<details class=\"developer-debug\">" in report and "Developer Detail" in report,
        "result_developer_detail_closed": "<details class=\"developer-debug\">" in result and "Developer Detail" in result,
        "reason_codes_compact": "renderChips" in report and "renderChips" in result and "reason-chip" in css,
        "growth_prior_section": "Growth Prior" in report and "Growth Prior" in result,
        "no_raw_two_column_dump": "report-raw-json" in report and "result-raw-json" in result,
        "wrap_contract": "overflow-wrap: anywhere" in css and "word-break: break-word" in css,
    }
    for token in duplicate_tokens:
        checks[f"report_no_duplicate_label_{token}"] = _count(report, f"<dt>{token}</dt>") <= 1
    checks["report_no_duplicate_operator_notes"] = _count(report, "<h2>Operator Notes</h2>") <= 1
    return {"status": "PROGRESS_6_6_REPORT_RESULT_COMPACT_SMOKE_PASS" if all(checks.values()) else "PROGRESS_6_6_REPORT_RESULT_COMPACT_SMOKE_FAIL", "checks": checks}


def main() -> int:
    result = run_smoke()
    print(json.dumps(result, indent=2, ensure_ascii=False))
    print(result["status"])
    return 0 if result["status"].endswith("_PASS") else 1


if __name__ == "__main__":
    raise SystemExit(main())
