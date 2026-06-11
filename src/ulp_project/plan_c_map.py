"""Map marker access for Plan C."""

from __future__ import annotations

from typing import Any

from .plan_c_feedback_learning import rejected_session_ids
from .plan_c_storage import PLAN_C_MARKERS_JSON, read_markers


def load_plan_c_map_payload() -> dict[str, Any]:
    rejected = rejected_session_ids()
    markers = [marker for marker in read_markers() if str(marker.get("session_id") or "") not in rejected]
    return {
        "status": "PLAN_C_MARKERS_READY" if markers else "NO_MARKERS_YET",
        "marker_count": len(markers),
        "marker_path": str(PLAN_C_MARKERS_JSON),
        "markers": markers,
    }
