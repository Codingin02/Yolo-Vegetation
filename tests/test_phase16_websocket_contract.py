import time

from ulp_project.realtime_streaming import create_realtime_session, validate_realtime_payload_contract, websocket_available


def test_websocket_payload_contract(tmp_path):
    session = create_realtime_session(tmp_path)
    payload = {
        "session_id": session["session_id"],
        "session_token": session["session_token"],
        "frame_id": "f1",
        "timestamp_client_ms": int(time.time() * 1000),
        "point_id": "V001_pohon_sono",
        "species_hint": "pohon_sono",
        "asset_type": "span",
        "client_mode": "remote_https",
        "requested_interval_ms": 1000,
    }
    assert validate_realtime_payload_contract(payload)["status"] == "WEBSOCKET_PAYLOAD_CONTRACT_VALID"
    assert websocket_available()["status"] in {"WEBSOCKET_AVAILABLE", "WEBSOCKET_DEPENDENCY_NOT_INSTALLED"}
