"""Small PWA manifest contract for the mobile field page."""

from __future__ import annotations


def build_pwa_manifest() -> dict[str, object]:
    return {
        "name": "ULP Field Runtime",
        "short_name": "ULP Field",
        "start_url": "/mobile",
        "display": "standalone",
        "background_color": "#ffffff",
        "theme_color": "#185a4d",
        "description": "Mobile inspection queue for ULP Project system runtime.",
    }
