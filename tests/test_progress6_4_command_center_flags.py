from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_progress6_4_command_center_has_live_acceptance_flags() -> None:
    source = (ROOT / "scripts" / "operator_command_center.py").read_text(encoding="utf-8")
    for token in [
        "--progress6-4-preflight",
        "--progress6-4-print-live-test",
        "--progress6-4-acceptance-validator",
        "--progress6-4-gate",
        "--print-live-hp-test-url",
        "progress6-4-live-hp-acceptance",
    ]:
        assert token in source
