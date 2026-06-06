from __future__ import annotations

from pathlib import Path

from ulp_project.flask_app import create_app

ROOT = Path(__file__).resolve().parents[1]


def test_progress6_3_field_session_js_handles_visibility_change() -> None:
    js = (ROOT / "src" / "ulp_project" / "static" / "field_session.js").read_text(encoding="utf-8")
    assert 'document.addEventListener("visibilitychange", handleVisibilityChange)' in js
    assert "PAGE_HIDDEN_BROWSER_MAY_THROTTLE" in js
    assert "frame_process_interval_ms = 3000" in js


def test_progress6_3_backend_records_hidden_foreground_warning(tmp_path: Path) -> None:
    client = create_app(runtime_root=tmp_path).test_client()
    started = client.post(
        "/api/field/session/start",
        json={
            "session_id": "VISIBILITY_TEST",
            "visibility_state": "hidden",
            "foreground_recording_status": "PAGE_HIDDEN_BROWSER_MAY_THROTTLE",
            "browser_throttle_warning": "Halaman tidak aktif. Browser dapat membatasi kamera/timer/GPS.",
        },
    ).get_json()
    assert started["visibility_state"] == "hidden"
    assert started["foreground_recording_status"] == "PAGE_HIDDEN_BROWSER_MAY_THROTTLE"
    assert started["frame_loop_paused_due_to_hidden"] is True
