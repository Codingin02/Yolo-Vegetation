from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_progress6_2_native_session_does_not_use_dataset_botol() -> None:
    for path in [
        ROOT / "src" / "ulp_project" / "field_session_runtime.py",
        ROOT / "src" / "ulp_project" / "static" / "field_session.js",
        ROOT / "src" / "ulp_project" / "templates" / "field_capture.html",
    ]:
        assert "dataset_botol" not in path.read_text(encoding="utf-8")
