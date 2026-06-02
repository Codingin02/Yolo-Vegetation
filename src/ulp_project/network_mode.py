"""Network mode helpers for mobile field operation."""

from __future__ import annotations

VALID_NETWORK_MODES = {"same_lan_mode", "tunnel_mode", "offline_queue_mode"}


def normalize_network_mode(value: str | None) -> dict[str, str]:
    mode = (value or "same_lan_mode").strip()
    if mode not in VALID_NETWORK_MODES:
        return {
            "status": "NETWORK_MODE_UNKNOWN",
            "network_mode": mode,
            "recommended_mode": "same_lan_mode",
        }
    return {"status": "NETWORK_MODE_READY", "network_mode": mode, "recommended_mode": mode}


def describe_network_modes() -> dict[str, dict[str, str]]:
    return {
        "same_lan_mode": {
            "status": "READY_WITH_LOCAL_IP",
            "note": "HP dan laptop pada WiFi/hotspot yang sama.",
        },
        "tunnel_mode": {
            "status": "READY_WITH_MANUAL_TUNNEL",
            "note": "Gunakan ngrok/cloudflared manual; token hanya via environment, bukan Git.",
        },
        "offline_queue_mode": {
            "status": "READY_WITH_BROWSER_QUEUE",
            "note": "Browser menyimpan input sementara saat sinyal buruk.",
        },
    }
