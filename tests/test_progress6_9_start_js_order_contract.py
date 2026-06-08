from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_progress6_9_start_js_assigns_result_session_before_validation() -> None:
    source = (ROOT / "src" / "ulp_project" / "static" / "field_session.js").read_text(encoding="utf-8")
    assign_index = source.index("const startedSessionId = getOperationalSessionIdFromStartResult(result);")
    validation_index = source.index("!isOperationalSessionId(startedSessionId)")
    storage_index = source.index("rememberOperationalSession(startedSessionId")
    assert assign_index < validation_index < storage_index
    assert "window.sessionStorage.setItem(\"ulp_active_field_session_id\"" in source
    assert "SESSION_START_FAILED_NO_CAMERA_REDIRECT" in source
