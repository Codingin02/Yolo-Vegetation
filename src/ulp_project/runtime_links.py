"""Runtime link helpers for laptop-to-HP field trial access."""

from __future__ import annotations

import os
import socket
from datetime import datetime
from typing import Any

from .ngrok_runtime_probe import probe_ngrok_runtime


PUBLIC_TUNNEL_ENV_KEYS = ("TUNNEL_PUBLIC_URL", "PUBLIC_TUNNEL_URL", "NGROK_PUBLIC_URL", "CLOUDFLARED_PUBLIC_URL")


def detect_lan_ips() -> list[str]:
    candidates: list[str] = []
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.connect(("8.8.8.8", 80))
            candidates.append(sock.getsockname()[0])
    except OSError:
        pass
    try:
        for info in socket.getaddrinfo(socket.gethostname(), None, socket.AF_INET):
            candidates.append(info[4][0])
    except OSError:
        pass
    stable: list[str] = []
    for candidate in candidates:
        if _is_field_lan_ip(candidate) and candidate not in stable:
            stable.append(candidate)
    return stable


def build_public_links(port: int = 5000, public_url: str | None = None) -> dict[str, Any]:
    lan_urls = [f"http://{ip}:{port}/field-capture" for ip in detect_lan_ips()]
    tunnel = probe_ngrok_runtime(port=port, timeout_s=0.35)
    public_base = _runtime_public_url(public_url) or tunnel.get("public_https_url")
    public_field_capture_url = f"{public_base}/field-capture" if public_base else None
    public_checklist_url = f"{public_base}/field-trial-checklist" if public_base else None
    public_map_url = f"{public_base}/api/field/latest-map" if public_base else None
    public_ready = bool(public_field_capture_url and str(public_field_capture_url).startswith("https://"))
    return {
        "status": "READY" if public_ready else "NO_PUBLIC_TUNNEL_CONFIGURED",
        "public_url_status": "PUBLIC_HTTPS_TUNNEL_READY" if public_ready else "PUBLIC_TUNNEL_NOT_RUNNING",
        "tunnel_status": tunnel.get("status", "PUBLIC_TUNNEL_NOT_RUNNING"),
        "ngrok": tunnel,
        "local_field_capture_url": f"http://127.0.0.1:{port}/field-capture",
        "lan_field_capture_url": lan_urls[0] if lan_urls else None,
        "lan_field_capture_urls": lan_urls,
        "public_https_url": public_base if public_ready else None,
        "public_field_capture_url": public_field_capture_url,
        "public_checklist_url": public_checklist_url,
        "public_map_url": public_map_url,
        "health_url": f"http://127.0.0.1:{port}/api/network/health",
        "ping_url": f"http://127.0.0.1:{port}/api/latency/ping",
        "server_time": datetime.now().isoformat(),
        "secure_context_note": _secure_context_note(public_field_capture_url),
        "operator_note": "Use HTTPS tunnel for camera/GPS permissions on mobile browsers",
        "manual_tunnel_commands": [f"ngrok http {port}", f"cloudflared tunnel --url http://localhost:{port}"],
        "token_policy": "Do not store ngrok/cloudflared tokens or runtime tunnel URLs in Git.",
    }


def build_secure_context_diagnostic(
    *,
    host: str,
    scheme: str = "http",
    forwarded_proto: str = "",
    port: int = 5000,
    public_url: str | None = None,
) -> dict[str, Any]:
    links = build_public_links(port=port, public_url=public_url)
    hostname = (host or "").split(":", 1)[0].lower()
    effective_scheme = (forwarded_proto or scheme or "http").split(",", 1)[0].strip().lower()
    is_localhost = hostname in {"localhost", "127.0.0.1", "::1"}
    is_lan = _is_field_lan_ip(hostname)
    is_public_tunnel_host = any(token in hostname for token in ("ngrok", "trycloudflare", "cloudflare"))
    if (effective_scheme == "https" or is_public_tunnel_host) and not is_localhost:
        current_url_mode = "HTTPS_PUBLIC_READY"
        secure_context_status = "SECURE_CONTEXT_OK"
    elif is_localhost:
        current_url_mode = "LOCALHOST_DEBUG_ONLY"
        secure_context_status = "LOCAL_DEV_CONTEXT"
    elif is_lan:
        current_url_mode = "LAN_HTTP_DEBUG_ONLY"
        secure_context_status = "INSECURE_CONTEXT_CAMERA_GPS_BLOCKED"
    else:
        current_url_mode = "LAN_HTTP_DEBUG_ONLY" if effective_scheme == "http" else "HTTPS_PUBLIC_READY"
        secure_context_status = "INSECURE_CONTEXT_CAMERA_GPS_BLOCKED" if effective_scheme == "http" else "SECURE_CONTEXT_OK"
    return {
        "status": "SECURE_CONTEXT_DIAGNOSTIC_READY",
        "host": host,
        "scheme": scheme,
        "forwarded_proto": forwarded_proto,
        "effective_scheme": effective_scheme,
        "current_url_mode": current_url_mode,
        "current_context": "LAN_HTTP_INSECURE" if current_url_mode == "LAN_HTTP_DEBUG_ONLY" else current_url_mode,
        "secure_context_status": secure_context_status,
        "public_tunnel_status": links.get("tunnel_status"),
        "public_url_status": links.get("public_url_status"),
        "recommended_url": links.get("public_field_capture_url"),
        "lan_http_warning": "Anda sedang membuka LAN HTTP. Ini hanya debug. Field trial beda jaringan wajib memakai Public HTTPS URL."
        if current_url_mode == "LAN_HTTP_DEBUG_ONLY"
        else "",
        "operator_command": "ngrok http 5000" if not links.get("public_field_capture_url") else "",
        "public_links": links,
    }


def format_startup_links(host: str = "0.0.0.0", port: int = 5000, public_url: str | None = None) -> str:
    links = build_public_links(port=port, public_url=public_url)
    lines = [
        "ULP Progress 5.2 field trial server starting",
        f"Bind host        : {host}:{port}",
        f"Local URL        : {links['local_field_capture_url']}",
    ]
    lan_urls = links.get("lan_field_capture_urls") or []
    if lan_urls:
        for url in lan_urls:
            lines.append(f"LAN URL kandidat : {url}")
    else:
        lines.append("LAN URL kandidat : IP belum terdeteksi otomatis. Jalankan ipconfig dan cari IPv4 WiFi/hotspot.")
    lines.extend(
        [
            f"Health URL       : {links['health_url']}",
            f"Ping URL         : {links['ping_url']}",
        ]
    )
    if links.get("public_field_capture_url"):
        lines.append(f"Public tunnel URL: {links['public_field_capture_url']}")
    else:
        lines.extend(
            [
                "Public tunnel URL: NO_PUBLIC_TUNNEL_CONFIGURED",
                f"Manual ngrok     : ngrok http {port}",
                f"Manual cloudflare: cloudflared tunnel --url http://localhost:{port}",
            ]
        )
    lines.extend(
        [
            "Secure context   : HTTPS tunnel disarankan untuk kamera/GPS browser HP.",
            "Token policy     : jangan simpan token/tunnel URL runtime ke Git.",
        ]
    )
    return "\n".join(lines)


def _runtime_public_url(public_url: str | None = None) -> str | None:
    raw = (public_url or "").strip()
    if not raw:
        for key in PUBLIC_TUNNEL_ENV_KEYS:
            raw = os.environ.get(key, "").strip()
            if raw:
                break
    if not raw:
        return None
    if "://" not in raw:
        raw = f"https://{raw}"
    return raw.rstrip("/")


def _secure_context_note(public_url: str | None) -> str:
    if public_url and public_url.startswith("https://"):
        return "SECURE_CONTEXT_EXPECTED"
    return "LOCAL_DEV_OR_LAN_HTTP_REQUIRES_MANUAL_HTTPS_TUNNEL_FOR_CAMERA_GPS"


def _is_field_lan_ip(value: str) -> bool:
    if not value or value.startswith("127.") or value.startswith("169.254."):
        return False
    return "." in value
