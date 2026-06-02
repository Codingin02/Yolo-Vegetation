"""Phase 5 runtime orchestrator."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .environmental_risk import score_environmental_risk
from .map_runtime import build_system_map
from .network_mode import describe_network_modes
from .paths import PROJECT_ROOT
from .report_export import build_operator_report, export_report
from .spreadsheet_export import build_rows
from .system_status import collect_project_status
from .vegetation_risk_model import score_pohon_sono_risk


VALID_MODES = {
    "status",
    "dashboard-dry-run",
    "map-dry-run",
    "spreadsheet-dry-run",
    "risk-dry-run",
    "report-dry-run",
    "all-dry-run",
}


def run_pipeline_mode(mode: str, project_root: Path = PROJECT_ROOT) -> dict[str, Any]:
    if mode not in VALID_MODES:
        raise ValueError(f"Unknown mode: {mode}")
    if mode == "status":
        status = collect_project_status(project_root)
        return {"status": "SYSTEM_READY_WAITING_FOR_LABELS" if status["overall_status"] == "WAITING_FOR_LABELS" else status["overall_status"], "details": status}
    if mode == "dashboard-dry-run":
        return {
            "status": "SYSTEM_RUNTIME_DRY_RUN_READY",
            "dashboard": "READY_TO_RUN_LOCALLY",
            "mobile_page": "/mobile",
            "model": "MODEL_NOT_READY",
            "network_modes": describe_network_modes(),
        }
    if mode == "map-dry-run":
        return build_system_map(project_root / "data" / "templates" / "field_point_registry_template.csv", mode="dry-run")
    if mode == "spreadsheet-dry-run":
        rows = build_rows()
        return {"status": "SYSTEM_RUNTIME_DRY_RUN_READY", "rows": len(rows), "written": False}
    if mode == "risk-dry-run":
        legacy_risk = score_environmental_risk({})
        phase6_risk = score_pohon_sono_risk({"point_id": "V001_pohon_sono"})
        return {"status": "ENVIRONMENTAL_DATA_NOT_READY", "risk": legacy_risk, "phase6_risk": phase6_risk}
    if mode == "report-dry-run":
        return export_report(build_operator_report(project_root), mode="dry-run")
    results = {submode: run_pipeline_mode(submode, project_root) for submode in VALID_MODES if submode != "all-dry-run"}
    return {"status": "SYSTEM_RUNTIME_DRY_RUN_READY", "results": results}
