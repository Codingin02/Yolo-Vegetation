from __future__ import annotations

from pathlib import Path

from ulp_project.flask_app import create_app


def test_progress5_4_realtime_frame_does_not_write_report_before_shutter(tmp_path: Path) -> None:
    client = create_app(runtime_root=tmp_path).test_client()

    result = client.post("/api/field/realtime-frame", json={"point_id": "V001_pohon_sono", "timestamp_client_ms": 0}).get_json()

    assert result["no_autosave_on_realtime_frame"] is True
    assert client.get("/api/field/report-latest").get_json()["status"] in {
        "NO_PROGRESS5_4_REPORT_YET",
        "PROGRESS5_4_SHUTTER_REPORT_WRITTEN",
    }
