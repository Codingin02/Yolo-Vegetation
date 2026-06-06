from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_progress6_3_runtime_and_status_do_not_use_dataset_botol_as_main_dataset() -> None:
    scanned = [
        ROOT / "src" / "ulp_project" / "field_session_runtime.py",
        ROOT / "src" / "ulp_project" / "field_acceptance_runtime.py",
        ROOT / "src" / "ulp_project" / "gps_reliability_policy.py",
        ROOT / "src" / "ulp_project" / "progress_status_consistency.py",
        ROOT / "src" / "ulp_project" / "templates" / "field_acceptance.html",
        ROOT / "src" / "ulp_project" / "static" / "field_session.js",
        ROOT / "scripts" / "progress6_3_field_acceptance_gate.py",
    ]
    references = [
        path.relative_to(ROOT).as_posix()
        for path in scanned
        if "dataset_botol" in path.read_text(encoding="utf-8", errors="ignore")
    ]
    assert not references
