from __future__ import annotations

from ulp_project.runtime_links import build_secure_context_diagnostic


def test_progress5_4_https_public_url_is_secure_context() -> None:
    result = build_secure_context_diagnostic(
        host="lend-trunks-unpaid.ngrok-free.dev",
        scheme="http",
        forwarded_proto="https",
        public_url="https://lend-trunks-unpaid.ngrok-free.dev",
    )

    assert result["current_url_mode"] == "HTTPS_PUBLIC_READY"
    assert result["secure_context_status"] == "SECURE_CONTEXT_OK"


def test_progress5_4_lan_http_is_debug_only_and_blocked_for_permissions() -> None:
    result = build_secure_context_diagnostic(host="192.168.1.11:5000", scheme="http")

    assert result["current_url_mode"] == "LAN_HTTP_DEBUG_ONLY"
    assert result["secure_context_status"] == "INSECURE_CONTEXT_CAMERA_GPS_BLOCKED"
    assert "LAN HTTP" in result["lan_http_warning"]
