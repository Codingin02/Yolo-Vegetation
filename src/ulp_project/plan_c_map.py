"""Map marker access for Plan C."""

from __future__ import annotations

from typing import Any

from .plan_c_storage import PLAN_C_MARKERS_JSON, read_markers


def load_plan_c_map_payload() -> dict[str, Any]:
    markers = read_markers()
    return {
        "status": "PLAN_C_MARKERS_READY" if markers else "NO_MARKERS_YET",
        "marker_count": len(markers),
        "marker_path": str(PLAN_C_MARKERS_JSON),
        "markers": markers,
    }
