"""Legacy browser manifest helper.

Phase 8 does not implement a PWA or mobile app. This helper remains only for
backward compatibility and uses browser display semantics.
"""

from __future__ import annotations


def build_pwa_manifest() -> dict[str, object]:
    return {
        "name": "ULP Field Runtime",
        "short_name": "ULP Field",
        "start_url": "/mobile",
        "display": "browser",
        "background_color": "#ffffff",
        "theme_color": "#185a4d",
        "description": "Field capture browser input for ULP Project.",
    }
