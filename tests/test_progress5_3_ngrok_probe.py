from __future__ import annotations

import json

from ulp_project.ngrok_runtime_probe import probe_ngrok_runtime


class _FakeResponse:
    def __init__(self, payload: dict[str, object]) -> None:
        self._payload = payload

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def read(self) -> bytes:
        return json.dumps(self._payload).encode("utf-8")


def test_ngrok_probe_detects_https_tunnel_without_token() -> None:
    def fake_open(_url: str, timeout: float):
        assert timeout > 0
        return _FakeResponse({"tunnels": [{"public_url": "https://demo.ngrok-free.app"}]})

    result = probe_ngrok_runtime(
        which_func=lambda _name: "C:/Tools/ngrok.exe",
        process_checker=lambda: "RUNNING",
        urlopen_func=fake_open,
    )

    assert result["status"] == "NGROK_HTTPS_TUNNEL_READY"
    assert result["field_capture_public_url"] == "https://demo.ngrok-free.app/field-capture"
    assert "authtoken" in result["operator_note"]
    assert result["token_policy"] == "NO_TOKEN_READ_NO_TOKEN_WRITE_NO_AUTHTOKEN_IN_GIT"


def test_ngrok_probe_not_running_is_honest_and_non_fatal() -> None:
    def fake_open(_url: str, timeout: float):
        raise OSError("connection refused")

    result = probe_ngrok_runtime(
        which_func=lambda _name: "C:/Tools/ngrok.exe",
        process_checker=lambda: "NOT_RUNNING",
        urlopen_func=fake_open,
    )

    assert result["status"] == "NGROK_CLI_FOUND_BUT_TUNNEL_NOT_RUNNING"
    assert result["public_https_url"] is None
    assert result["operator_command"] == "ngrok http 5000"
