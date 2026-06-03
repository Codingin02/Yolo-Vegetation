"""Minimal report map builder facade."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .map_report_policy import should_create_map_marker
from .paths import PROJECT_ROOT

DEFAULT_MAP = PROJECT_ROOT / "outputs" / "reports" / "latest_risk_map.html"


def build_latest_risk_map(row: dict[str, Any], output: Path = DEFAULT_MAP) -> dict[str, Any]:
    policy = should_create_map_marker(row)
    if not policy["write_marker"]:
        return {"status": policy["status"], "written": False, "path": str(output)}
    output.parent.mkdir(parents=True, exist_ok=True)
    popup = "<br>".join(
        [
            f"point_id: {row.get('point_id')}",
            f"species: {row.get('species')}",
            f"clearance_stable: {row.get('selected_clearance_m_stable')}",
            f"display_clearance: {row.get('selected_clearance_display_m')}",
            f"eta_expected: {row.get('eta_expected_days') or row.get('eta_days')}",
            f"risk_priority: {row.get('risk_priority')}",
            f"action: {row.get('action_recommendation')}",
            f"confidence: {row.get('confidence_status')}",
        ]
    )
    output.write_text(f"<html><body><h1>Latest Risk Map</h1><p>color={policy['color']}</p><div>{popup}</div></body></html>", encoding="utf-8")
    return {"status": "MAP_REPORT_WRITTEN", "written": True, "path": str(output), "marker_color": policy["color"]}
