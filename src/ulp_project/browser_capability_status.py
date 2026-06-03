"""Browser capability labels for HP field capture browser."""

from __future__ import annotations


def browser_capability_status(is_secure_context: bool, camera_permission: str = "unknown", gps_permission: str = "unknown") -> dict[str, str]:
    protocol = "HTTPS_SECURE" if is_secure_context else "HTTP_LAN"
    camera = "AVAILABLE" if camera_permission == "granted" else ("BLOCKED_INSECURE_CONTEXT" if not is_secure_context else "NOT_TESTED")
    gps = "AVAILABLE" if gps_permission == "granted" else ("BLOCKED_INSECURE_CONTEXT" if not is_secure_context else "NOT_TESTED")
    return {"protocol_status": protocol, "camera_status": camera, "gps_status": gps}
