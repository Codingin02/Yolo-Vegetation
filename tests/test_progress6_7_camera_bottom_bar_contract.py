from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_progress6_7_camera_bottom_bar_order_and_no_report() -> None:
    html = (ROOT / "src" / "ulp_project" / "templates" / "field_camera.html").read_text(encoding="utf-8")
    start = html.index('<nav class="camera-bottom-bar"')
    end = html.index("</nav>", start)
    bottom = html[start:end]
    order = [bottom.index(token) for token in ["session-home", "open-map-report", "shutter-capture", "session-result", "session-manual-input"]]
    assert order == sorted(order)
    assert "session-report" not in bottom
    assert ">Report<" not in bottom
    assert "disabled" in bottom
