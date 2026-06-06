from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_progress6_4_no_fake_acceptance_pass_without_evidence_claim() -> None:
    paths = [
        ROOT / "src" / "ulp_project" / "field_acceptance_validation.py",
        ROOT / "scripts" / "progress6_4_live_hp_acceptance_gate.py",
    ]
    validator = paths[0].read_text(encoding="utf-8")
    assert "NO_HP_PHYSICAL_EVIDENCE_SUBMITTED" in validator
    for path in paths:
        assert "no_fake_acceptance" in path.read_text(encoding="utf-8")
