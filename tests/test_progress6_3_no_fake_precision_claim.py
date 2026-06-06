from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_progress6_3_runtime_has_no_fake_precision_claims() -> None:
    forbidden = ["SANGAT_AKURAT", "HIGH_" + "PRECISION", "SURVEY_" + "GRADE", "MULTI_" + "SATELLITE_CONFIRMED"]
    findings: list[str] = []
    for root in [ROOT / "src" / "ulp_project", ROOT / "scripts"]:
        for path in root.rglob("*"):
            if not path.is_file() or path.suffix.lower() not in {".py", ".js", ".html", ".css"}:
                continue
            if path.name in {"progress6_3_no_fake_precision_smoke.py"}:
                continue
            text = path.read_text(encoding="utf-8", errors="ignore").upper()
            for token in forbidden:
                if token in text:
                    findings.append(path.relative_to(ROOT).as_posix())
    assert not findings
