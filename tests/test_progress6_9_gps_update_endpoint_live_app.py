from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import run_remote_realtime_server as remote_server


def test_progress6_9_gps_update_live_app_accepts_nested_and_flat(tmp_path) -> None:
    client = remote_server.create_app(runtime_root=tmp_path).test_client()
    session_id = client.post("/api/field/session/start", json={"point_id": "V001_pohon_sono"}).get_json()["session_id"]
    nested = client.post(
        "/api/field/session/gps-update",
        json={"session_id": session_id, "coords": {"latitude": -7.2234567, "longitude": 112.7312345, "accuracy": 5.0}},
    )
    assert nested.status_code not in {404, 405, 500}
    assert nested.get_json()["gps"]["latitude"] == -7.2234567

    flat = client.post(
        "/api/field/session/gps-update",
        json={"session_id": session_id, "current_latitude": -7.2234568, "current_longitude": 112.7312346, "current_accuracy_m": 6.0},
    )
    assert flat.status_code not in {404, 405, 500}
    assert flat.get_json()["gps"]["longitude"] == 112.7312346
