"""Operator report export helpers."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from .paths import PROJECT_ROOT
from .system_status import collect_project_status, render_status_markdown

OUTPUT_REPORT_DIR = PROJECT_ROOT / "outputs" / "reports"


def build_operator_report(project_root: Path = PROJECT_ROOT) -> dict[str, Any]:
    status = collect_project_status(project_root)
    return {
        "project_identity": {
            "name": "ULP_Project",
            "context": "PT PLN UP3 Surabaya Utara ULP Perak",
            "author": "Ahmad Bagus Idkholus Surur",
        },
        "dataset_status": status["field_dataset"],
        "labeling_status": status["labels_selected"],
        "gps_status": "READY_OR_PARTIAL",
        "model_status": status.get("model", {"status": "MODEL_NOT_READY"}),
        "risk_engine_status": status.get("risk_engine", {"status": "ENVIRONMENTAL_DATA_NOT_READY"}),
        "mobile_runtime_status": status.get("mobile_runtime", {"status": "MOBILE_RUNTIME_NOT_CONFIGURED"}),
        "map_dashboard_status": {
            "flask": status["components"].get("flask_scaffold"),
            "map_builder": status["components"].get("map_builder"),
            "mobile_page": status.get("mobile_runtime", {}).get("mobile_page_exists", False),
        },
        "blocked_items": status["blocked_items"],
        "next_operator_actions": status["next_actions"],
        "disclaimer": "No fake accuracy, mAP, precision, recall, or confusion matrix is reported before real training/evaluation.",
    }


def export_report(report: dict[str, Any], output_dir: Path = OUTPUT_REPORT_DIR, mode: str = "dry-run") -> dict[str, Any]:
    if mode not in {"dry-run", "write"}:
        raise ValueError("mode must be dry-run or write")
    targets = {
        "json": output_dir / "system_report.json",
        "md": output_dir / "system_report.md",
        "csv": output_dir / "system_report.csv",
        "xlsx": output_dir / "system_report.xlsx",
    }
    if mode == "dry-run":
        return {"status": "SYSTEM_REPORT_DRY_RUN_READY", "written": [], "targets": {key: str(value) for key, value in targets.items()}}
    if not str(output_dir.resolve()).startswith(str(OUTPUT_REPORT_DIR.resolve())):
        return {"status": "OUTPUT_PATH_NOT_ALLOWED", "written": [], "targets": {}}
    output_dir.mkdir(parents=True, exist_ok=True)
    targets["json"].write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    targets["md"].write_text(render_report_markdown(report), encoding="utf-8")
    _write_report_csv(report, targets["csv"])
    written = ["json", "md", "csv"]
    try:
        import openpyxl
    except ImportError:
        xlsx_status = "XLSX_SKIPPED_OPENPYXL_NOT_AVAILABLE"
    else:
        workbook = openpyxl.Workbook()
        sheet = workbook.active
        sheet.title = "system_report"
        sheet.append(["section", "value"])
        for key, value in report.items():
            sheet.append([key, json.dumps(value, ensure_ascii=False)])
        workbook.save(targets["xlsx"])
        written.append("xlsx")
        xlsx_status = "XLSX_READY"
    return {"status": "SYSTEM_REPORT_WRITTEN", "written": written, "xlsx_status": xlsx_status, "targets": {key: str(value) for key, value in targets.items()}}


def render_report_markdown(report: dict[str, Any]) -> str:
    lines = ["# ULP Project System Report", ""]
    for key, value in report.items():
        lines.append(f"## {key}")
        lines.append("")
        lines.append("```json")
        lines.append(json.dumps(value, indent=2, ensure_ascii=False))
        lines.append("```")
        lines.append("")
    return "\n".join(lines)


def _write_report_csv(report: dict[str, Any], output: Path) -> None:
    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["section", "value"])
        for key, value in report.items():
            writer.writerow([key, json.dumps(value, ensure_ascii=False)])
