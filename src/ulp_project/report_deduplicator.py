"""In-memory report deduplication for field trial snapshots."""

from __future__ import annotations

import time
from typing import Any

_RECENT: dict[str, float] = {}


def deduplicate_report(payload: dict[str, Any], cooldown_sec: int = 45) -> dict[str, Any]:
    key = f"{payload.get('session_id')}|{payload.get('point_id')}|{payload.get('risk_priority')}|{payload.get('selected_clearance_m_stable')}"
    now = time.monotonic()
    previous = _RECENT.get(key)
    if previous is not None and now - previous < cooldown_sec and not payload.get("manual_force"):
        return {"status": "REPORT_DUPLICATE_COOLDOWN", "write_report": False, "cooldown_sec": cooldown_sec}
    _RECENT[key] = now
    return {"status": "REPORT_DEDUP_OK", "write_report": True}
