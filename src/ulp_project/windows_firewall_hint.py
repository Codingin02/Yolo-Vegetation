def windows_firewall_hint(port: int = 5000) -> dict[str, str]:
    return {
        "status": "WINDOWS_FIREWALL_HINT_READY",
        "hint": f"Allow Python/Flask on Private Network or open TCP port {port} for field trial.",
    }
