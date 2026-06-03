"""Policy for writing reports only on snapshots/stable cooldown."""

from __future__ import annotations

from typing import Any

VALID_TRIGGERS = {"MANUAL_SNAPSHOT", "STABLE_RESULT_COOLDOWN", "FIELD_REVIEW"}


def should_write_snapshot_report(payload: dict[str, Any], last_report_age_sec: float | None = None, cooldown_sec: int = 45) -> dict[str, Any]:
    trigger = payload.get("report_trigger")
    if trigger not in VALID_TRIGGERS:
        return {"status": "REPORT_NOT_TRIGGERED", "write_report": False, "reason": "Realtime frame only; no snapshot trigger."}
    if trigger != "MANUAL_SNAPSHOT" and last_report_age_sec is not None and last_report_age_sec < cooldown_sec:
        return {"status": "REPORT_DEDUP_COOLDOWN_ACTIVE", "write_report": False, "cooldown_sec": cooldown_sec}
    return {"status": "REPORT_WRITE_ALLOWED", "write_report": True, "report_trigger": trigger}
