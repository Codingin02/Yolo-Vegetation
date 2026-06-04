from __future__ import annotations

import csv
from pathlib import Path

from ulp_project.flask_app import create_app


def test_progress5_4_shutter_autosave_has_remote_https_columns(tmp_path: Path) -> None:
    payload = create_app(runtime_root=tmp_path).test_client().post(
        "/api/field/shutter-capture",
        json={
            "point_id": "V001_pohon_sono",
            "operator_name": "operator-test",
            "gps_lat": -7.1,
            "gps_lon": 112.7,
            "gps_accuracy_m": 10,
            "gps_source": "GPS_SOURCE_BROWSER",
            "secure_context_status": "SECURE_CONTEXT_OK",
            "current_url_mode": "HTTPS_PUBLIC_READY",
            "public_tunnel_status": "NGROK_HTTPS_TUNNEL_READY",
            "model_status": "MODEL_NOT_READY",
            "notes": "autosave test",
        },
    ).get_json()

    assert payload["report_csv_url"] == "/field-reports/field_capture_autosave.csv"
    assert payload["google_sheets_status"] == "GOOGLE_SHEETS_NOT_CONFIGURED_LOCAL_CSV_READY"
    with Path(payload["report_csv_path"]).open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    assert rows[-1]["operator_name"] == "operator-test"
    assert rows[-1]["secure_context_status"] == "SECURE_CONTEXT_OK"
    assert rows[-1]["current_url_mode"] == "HTTPS_PUBLIC_READY"
    assert rows[-1]["public_tunnel_status"] == "NGROK_HTTPS_TUNNEL_READY"
    assert rows[-1]["csv_path"].endswith("field_capture_autosave.csv")
