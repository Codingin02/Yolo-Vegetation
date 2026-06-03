from __future__ import annotations

import base64
import csv
from pathlib import Path

from ulp_project.flask_app import create_app
from ulp_project.progress5_4_field_runtime import PROGRESS5_4_REPORT_COLUMNS


def test_progress5_4_shutter_writes_snapshot_and_csv_only_on_shutter(tmp_path: Path) -> None:
    app = create_app(runtime_root=tmp_path)
    client = app.test_client()
    image_b64 = base64.b64encode(b"fake-jpeg-smoke").decode("ascii")

    realtime = client.post("/api/field/realtime-frame", json={"point_id": "V001_pohon_sono", "timestamp_client_ms": 0}).get_json()
    assert realtime["no_autosave_on_realtime_frame"] is True

    response = client.post(
        "/api/field/shutter-capture",
        json={
            "point_id": "V001_pohon_sono",
            "image_jpeg_base64": image_b64,
            "gps_lat": -7.1,
            "gps_lon": 112.7,
            "gps_accuracy_m": 8,
            "gps_source": "GPS_SOURCE_BROWSER",
            "model_status": "MODEL_NOT_READY",
            "measurement_result": {"clearance_m": None, "reason_codes": ["INSUFFICIENT_DATA"]},
            "notes": "shutter smoke",
        },
    )
    payload = response.get_json()

    assert response.status_code == 200
    assert payload["status"] == "PROGRESS5_4_SHUTTER_REPORT_WRITTEN"
    assert payload["snapshot_status"] == "SNAPSHOT_IMAGE_WRITTEN_RUNTIME_ONLY"
    assert Path(payload["snapshot_path"]).is_file()
    assert str(Path(payload["snapshot_path"])).startswith(str(tmp_path / "field_captures"))
    assert payload["map_status"] == "MAP_MARKER_WRITTEN"
    with Path(payload["report_csv_path"]).open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        assert set(PROGRESS5_4_REPORT_COLUMNS).issubset(set(reader.fieldnames or []))
        rows = list(reader)
    assert rows[-1]["point_id"] == "V001_pohon_sono"
    assert rows[-1]["model_status"] == "MODEL_NOT_READY"


def test_progress5_4_shutter_without_gps_keeps_no_marker(tmp_path: Path) -> None:
    payload = create_app(runtime_root=tmp_path).test_client().post(
        "/api/field/shutter-capture",
        json={"point_id": "V001_pohon_sono", "model_status": "MODEL_NOT_READY", "measurement_result": {}},
    ).get_json()

    assert payload["map_status"] == "NO_GPS_NO_MARKER"
    assert payload["row"]["zone_status"] == "INSUFFICIENT_DATA"
