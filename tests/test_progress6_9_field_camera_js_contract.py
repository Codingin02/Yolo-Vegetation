from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_progress6_9_field_camera_js_reads_query_dataset_and_storage() -> None:
    source = (ROOT / "src" / "ulp_project" / "static" / "field_camera.js").read_text(encoding="utf-8")
    assert 'new URLSearchParams(location.search).get("session_id")' in source
    assert "document.body.dataset.sessionId" in source
    assert "document.querySelector(\"[data-session-id]\")" in source
    assert 'sessionStorage.getItem("ulp_active_field_session_id")' in source
    assert "FS_DEGRADED" in source
