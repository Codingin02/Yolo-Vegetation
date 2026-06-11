"""Growth profile loader and quarterly prediction helper for Plan C."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from .plan_c_storage import PLAN_C_REFERENCE_DIR, to_float

PREDICTION_DATA_NOT_ENOUGH = "data tidak cukup"


def load_growth_profile(reference_dir: Path | str = PLAN_C_REFERENCE_DIR) -> dict[str, Any]:
    reference_dir = Path(reference_dir)
    json_result = load_json_profile(reference_dir / "plan_c_growth_profile.json")
    csv_result = load_csv_reference(reference_dir / "pohon_sono_growth_reference.csv")
    excel_result = load_excel_reference(reference_dir / "pohon_sono_growth_reference.xlsx")
    sources_result = load_csv_reference(reference_dir / "plan_c_growth_sources.csv")

    if json_result.get("status") == "GROWTH_PROFILE_LOADED":
        profile = dict(json_result.get("profile") or {})
        rate = _resolve_rate(profile, csv_result)
        return {
            **profile,
            "status": "GROWTH_PROFILE_LOADED",
            "loader_status": "GROWTH_PROFILE_LOADED",
            "growth_profile_status": profile.get("growth_profile_status") or "GROWTH_PROFILE_READY_PROXY",
            "growth_rate_m_per_quarter": rate,
            "data_source_type": profile.get("data_source_type") or "proxy",
            "observed_or_proxy": profile.get("observed_or_proxy") or "proxy",
            "json_status": json_result.get("status"),
            "csv_status": csv_result.get("status"),
            "excel_status": excel_result.get("status"),
            "sources_status": sources_result.get("status"),
            "csv_reference": csv_result,
            "excel_reference": excel_result,
            "sources_reference": sources_result,
        }

    if csv_result.get("status") == "CSV_REFERENCE_LOADED":
        rate = _resolve_rate({}, csv_result)
        return {
            "status": "CSV_REFERENCE_LOADED",
            "loader_status": "CSV_REFERENCE_LOADED",
            "growth_profile_status": "GROWTH_PROFILE_READY_PROXY",
            "growth_rate_m_per_quarter": rate,
            "data_source_type": "proxy",
            "observed_or_proxy": "proxy",
            "confidence_level": "proxy_reference_requires_field_validation",
            "limitations": ["CSV proxy terbaca, tetapi JSON profile belum tersedia."],
            "source_summary": {"rows": csv_result.get("row_count"), "path": csv_result.get("path")},
            "json_status": json_result.get("status"),
            "csv_status": csv_result.get("status"),
            "excel_status": excel_result.get("status"),
            "sources_status": sources_result.get("status"),
            "csv_reference": csv_result,
            "excel_reference": excel_result,
            "sources_reference": sources_result,
        }

    return {
        "status": "GROWTH_PROFILE_MISSING",
        "loader_status": "GROWTH_PROFILE_MISSING",
        "growth_profile_status": "GROWTH_PROFILE_MISSING",
        "growth_rate_m_per_quarter": None,
        "prediction_window": PREDICTION_DATA_NOT_ENOUGH,
        "data_source_type": "not_available",
        "observed_or_proxy": "not_available",
        "confidence_level": "not_available",
        "limitations": ["File growth reference belum tersedia di data/reference/pohon_sono_growth."],
        "source_summary": {"reference_dir": str(reference_dir)},
        "json_status": json_result.get("status"),
        "csv_status": csv_result.get("status"),
        "excel_status": excel_result.get("status"),
        "sources_status": sources_result.get("status"),
        "csv_reference": csv_result,
        "excel_reference": excel_result,
        "sources_reference": sources_result,
    }


def load_json_profile(path: Path | str) -> dict[str, Any]:
    path = Path(path)
    if not path.exists():
        return {"status": "GROWTH_PROFILE_MISSING", "path": str(path)}
    try:
        profile = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return {"status": "GROWTH_PROFILE_INVALID", "path": str(path), "error": f"{type(exc).__name__}: {exc}"}
    return {"status": "GROWTH_PROFILE_LOADED", "path": str(path), "profile": profile}


def load_csv_reference(path: Path | str) -> dict[str, Any]:
    path = Path(path)
    if not path.exists():
        return {"status": "CSV_REFERENCE_MISSING", "path": str(path), "rows": []}
    try:
        with path.open("r", newline="", encoding="utf-8-sig") as handle:
            non_empty_lines = [line for line in handle if line.strip()]
        if not non_empty_lines:
            return {"status": "CSV_REFERENCE_EMPTY", "path": str(path), "rows": []}
        reader = csv.DictReader(non_empty_lines)
        rows = [row for row in reader if any(value not in {None, ""} for value in row.values())]
    except OSError as exc:
        return {"status": "CSV_REFERENCE_INVALID", "path": str(path), "error": f"{type(exc).__name__}: {exc}", "rows": []}
    return {
        "status": "CSV_REFERENCE_LOADED",
        "path": str(path),
        "fieldnames": reader.fieldnames or [],
        "row_count": len(rows),
        "rows": rows,
    }


def load_excel_reference(path: Path | str) -> dict[str, Any]:
    path = Path(path)
    if not path.exists():
        return {"status": "EXCEL_REFERENCE_MISSING", "path": str(path)}
    try:
        import openpyxl  # type: ignore
    except Exception as exc:
        return {
            "status": "EXCEL_REFERENCE_SKIPPED_OPENPYXL_NOT_AVAILABLE",
            "path": str(path),
            "error": f"{type(exc).__name__}: {exc}",
        }
    try:
        workbook = openpyxl.load_workbook(path, read_only=True, data_only=True)
        sheet_names = list(workbook.sheetnames)
    except Exception as exc:
        return {"status": "EXCEL_REFERENCE_INVALID", "path": str(path), "error": f"{type(exc).__name__}: {exc}"}
    return {"status": "EXCEL_REFERENCE_LOADED", "path": str(path), "sheet_names": sheet_names}


def get_growth_rate_for_age_or_default(age_class: str | None = None, month: int | None = None) -> float | None:
    profile = load_growth_profile()
    if profile.get("growth_profile_status") == "GROWTH_PROFILE_MISSING":
        return None
    seasonal = profile.get("seasonal_growth_rate_m_per_quarter")
    if month and isinstance(seasonal, dict):
        quarter = str(((int(month) - 1) // 3) + 1)
        seasonal_rate = to_float(seasonal.get(quarter))
        if seasonal_rate is not None:
            return seasonal_rate
    return to_float(profile.get("growth_rate_m_per_quarter"))


def compute_prediction_window(
    clearance_m: float | None,
    threshold_m: float = 3.0,
    growth_rate_m_per_quarter: float | None = None,
) -> str:
    clearance = to_float(clearance_m)
    rate = to_float(growth_rate_m_per_quarter)
    if clearance is None or rate is None or rate <= 0:
        return PREDICTION_DATA_NOT_ENOUGH
    if clearance <= threshold_m:
        return "0-3 bulan"
    months = ((clearance - threshold_m) / rate) * 3
    return classify_prediction_window(months)


def classify_prediction_window(months: float | None) -> str:
    value = to_float(months)
    if value is None:
        return PREDICTION_DATA_NOT_ENOUGH
    if value <= 3:
        return "0-3 bulan"
    if value <= 6:
        return "3-6 bulan"
    if value <= 9:
        return "6-9 bulan"
    if value <= 12:
        return "9-12 bulan"
    return ">12 bulan"


def build_growth_summary(
    clearance_m: float | None = None,
    *,
    threshold_m: float = 3.0,
    reference_dir: Path | str = PLAN_C_REFERENCE_DIR,
    month: int | None = None,
) -> dict[str, Any]:
    profile = load_growth_profile(reference_dir)
    rate = _rate_for_profile(profile, month=month)
    prediction_window = compute_prediction_window(clearance_m, threshold_m=threshold_m, growth_rate_m_per_quarter=rate)
    return {
        "growth_profile_status": profile.get("growth_profile_status", "GROWTH_PROFILE_MISSING"),
        "loader_status": profile.get("loader_status", profile.get("status")),
        "growth_rate_m_per_quarter": rate,
        "prediction_window": prediction_window,
        "data_source_type": profile.get("data_source_type", "not_available"),
        "observed_or_proxy": profile.get("observed_or_proxy", "not_available"),
        "confidence_level": profile.get("confidence_level", "not_available"),
        "limitations": profile.get("limitations", []),
        "source_summary": profile.get("source_summary", {}),
        "diagnostics": {
            "json_status": profile.get("json_status"),
            "csv_status": profile.get("csv_status"),
            "excel_status": profile.get("excel_status"),
            "sources_status": profile.get("sources_status"),
        },
    }


def _rate_for_profile(profile: dict[str, Any], *, month: int | None = None) -> float | None:
    seasonal = profile.get("seasonal_growth_rate_m_per_quarter")
    if month and isinstance(seasonal, dict):
        quarter = str(((int(month) - 1) // 3) + 1)
        seasonal_rate = to_float(seasonal.get(quarter))
        if seasonal_rate is not None:
            return seasonal_rate
    return to_float(profile.get("growth_rate_m_per_quarter"))


def _resolve_rate(profile: dict[str, Any], csv_result: dict[str, Any]) -> float | None:
    direct = to_float(profile.get("growth_rate_m_per_quarter"))
    if direct is not None:
        return direct
    rows = csv_result.get("rows") if isinstance(csv_result, dict) else None
    if not isinstance(rows, list):
        return None
    values = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        value = to_float(row.get("avg_clearance_reduction_m_q") or row.get("growth_rate_m_per_quarter"))
        if value is not None:
            values.append(value)
    return round(sum(values) / len(values), 4) if values else None
