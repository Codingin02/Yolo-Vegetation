"""Load pohon_sono growth prior proxy datasets without optional Excel deps."""

from __future__ import annotations

import re
import zipfile
from pathlib import Path
from typing import Any
from xml.etree import ElementTree as ET

from .paths import PROJECT_ROOT

DEFAULT_POHON_SONO_XLSX = (
    PROJECT_ROOT
    / "data"
    / "growth_model"
    / "pohon_sono"
    / "dataset_pohon_sono_surabaya_utara_2015_2025_lengkap_v2.xlsx"
)

REQUIRED_SHEETS = ["Dataset_Quarterly_Grid", "Field_Observation_Template", "Placement_Guide"]
_WORKBOOK_CACHE: dict[tuple[str, float], dict[str, list[dict[str, Any]]]] = {}

COLUMN_GROUPS = {
    "year": ["year", "tahun"],
    "quarter": ["quarter", "kuartal", "triwulan"],
    "grid_id": ["grid_id", "point_id", "id_grid", "grid"],
    "ph": ["ph_h2o", "soil_ph_proxy", "soil_ph_h2o_proxy", "soil_ph", "ph"],
    "rainfall": ["rainfall_quarter_mm", "rainfall_mm_quarter_proxy", "rainfall", "curah_hujan", "rain_mm"],
    "temperature": ["mean_temp_c", "mean_temp_c_quarter_proxy", "temperature", "suhu", "temp_c"],
    "humidity": ["relative_humidity", "mean_humidity_pct_quarter_proxy", "humidity", "kelembaban"],
    "solar": ["solar", "radiation", "radiasi", "solar_radiation", "solar_radiation_kwh_m2_day_proxy"],
    "soc": ["soc", "soil_soc_g_kg_proxy", "organic_carbon", "carbon"],
    "nitrogen": ["nitrogen", "soil_nitrogen_g_kg_proxy", "n"],
    "cec": ["cec", "soil_cec_cmol_kg_proxy", "ktk"],
    "growth": ["growth_multiplier", "height_growth_cm_q_prior", "estimated_growth", "growth_m_per_year", "estimated_height_growth_m_per_year"],
}


def growth_prior_dataset_status(path: Path | None = None) -> dict[str, Any]:
    path = path or DEFAULT_POHON_SONO_XLSX
    if not path.exists():
        return {
            "status": "GROWTH_PRIOR_DATASET_NOT_FOUND",
            "path": str(path),
            "source_status": "PROXY_NOT_FIELD_OBSERVED",
            "sheet_status": {},
            "row_count": 0,
            "missing_columns": list(COLUMN_GROUPS),
        }
    try:
        workbook = load_growth_prior_workbook(path)
    except Exception as exc:  # pragma: no cover - defensive corrupted xlsx path
        return {
            "status": "GROWTH_PRIOR_DATASET_INVALID",
            "path": str(path),
            "source_status": "PROXY_NOT_FIELD_OBSERVED",
            "error_type": type(exc).__name__,
            "message": str(exc)[:300],
            "row_count": 0,
        }

    quarterly = workbook.get("Dataset_Quarterly_Grid", [])
    headers = list(quarterly[0].keys()) if quarterly else []
    mapping = map_growth_columns(headers)
    missing_columns = [key for key, value in mapping.items() if not value]
    missing_sheets = [sheet for sheet in REQUIRED_SHEETS if sheet not in workbook]
    status = "GROWTH_PRIOR_READY_PROXY_DATASET"
    if missing_sheets or not quarterly:
        status = "GROWTH_PRIOR_DATASET_INVALID"
    elif missing_columns:
        status = "GROWTH_PRIOR_READY_PROXY_DATASET_WITH_MISSING_COLUMNS"
    return {
        "status": status,
        "path": str(path),
        "source_status": "PROXY_NOT_FIELD_OBSERVED",
        "required_sheets": REQUIRED_SHEETS,
        "sheet_status": {sheet: {"present": sheet in workbook, "row_count": len(workbook.get(sheet, []))} for sheet in REQUIRED_SHEETS},
        "row_count": len(quarterly),
        "headers": headers,
        "column_mapping": mapping,
        "missing_columns": missing_columns,
        "missing_sheets": missing_sheets,
        "not_final_biological_accuracy_claim": True,
    }


def load_growth_prior_workbook(path: Path | None = None) -> dict[str, list[dict[str, Any]]]:
    path = path or DEFAULT_POHON_SONO_XLSX
    cache_key = (str(path), path.stat().st_mtime)
    if cache_key in _WORKBOOK_CACHE:
        return _WORKBOOK_CACHE[cache_key]
    with zipfile.ZipFile(path) as archive:
        shared = _shared_strings(archive)
        sheet_paths = _sheet_paths(archive)
        result: dict[str, list[dict[str, Any]]] = {}
        for sheet_name, sheet_path in sheet_paths.items():
            if sheet_name in REQUIRED_SHEETS:
                result[sheet_name] = _read_sheet(archive, sheet_path, shared)
        _WORKBOOK_CACHE.clear()
        _WORKBOOK_CACHE[cache_key] = result
        return result


def load_proxy_rows(path: Path | None = None) -> list[dict[str, Any]]:
    return load_growth_prior_workbook(path).get("Dataset_Quarterly_Grid", [])


def map_growth_columns(headers: list[str]) -> dict[str, str]:
    normalized = {_normalize(header): header for header in headers}
    mapping: dict[str, str] = {}
    for canonical, aliases in COLUMN_GROUPS.items():
        found = ""
        for alias in aliases:
            key = _normalize(alias)
            if key in normalized:
                found = normalized[key]
                break
        mapping[canonical] = found
    return mapping


def sample_proxy_row(point_id: str = "V001_pohon_sono", path: Path | None = None) -> dict[str, Any]:
    rows = load_proxy_rows(path)
    if not rows:
        return {}
    point = str(point_id or "").lower()
    for row in rows:
        text = " ".join(str(value).lower() for value in row.values())
        if point and point in text:
            return {**row, "source_status": "PROXY_NOT_FIELD_OBSERVED"}
    return {**rows[0], "source_status": "PROXY_NOT_FIELD_OBSERVED"}


def _sheet_paths(archive: zipfile.ZipFile) -> dict[str, str]:
    ns = {"main": "http://schemas.openxmlformats.org/spreadsheetml/2006/main", "rel": "http://schemas.openxmlformats.org/officeDocument/2006/relationships"}
    workbook = ET.fromstring(archive.read("xl/workbook.xml"))
    rels = ET.fromstring(archive.read("xl/_rels/workbook.xml.rels"))
    rel_map = {rel.attrib["Id"]: rel.attrib["Target"] for rel in rels}
    paths: dict[str, str] = {}
    for sheet in workbook.findall(".//main:sheet", ns):
        name = str(sheet.attrib.get("name", ""))
        rel_id = sheet.attrib.get("{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id")
        target = rel_map.get(str(rel_id), "")
        if target:
            clean = target.lstrip("/")
            paths[name] = clean if clean.startswith("xl/") else "xl/" + clean
    return paths


def _shared_strings(archive: zipfile.ZipFile) -> list[str]:
    if "xl/sharedStrings.xml" not in archive.namelist():
        return []
    root = ET.fromstring(archive.read("xl/sharedStrings.xml"))
    ns = {"main": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
    values: list[str] = []
    for item in root.findall(".//main:si", ns):
        parts = [node.text or "" for node in item.findall(".//main:t", ns)]
        values.append("".join(parts))
    return values


def _read_sheet(archive: zipfile.ZipFile, sheet_path: str, shared: list[str]) -> list[dict[str, Any]]:
    root = ET.fromstring(archive.read(sheet_path))
    ns = {"main": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
    rows: list[list[Any]] = []
    for row in root.findall(".//main:sheetData/main:row", ns):
        values: dict[int, Any] = {}
        for cell in row.findall("main:c", ns):
            ref = cell.attrib.get("r", "")
            column_index = _column_index(ref)
            values[column_index] = _cell_value(cell, shared, ns)
        if values:
            max_index = max(values)
            rows.append([values.get(index, "") for index in range(max_index + 1)])
    if not rows:
        return []
    headers = [str(value).strip() for value in rows[0]]
    records: list[dict[str, Any]] = []
    for row in rows[1:]:
        record = {headers[index]: row[index] if index < len(row) else "" for index in range(len(headers)) if headers[index]}
        if any(value not in {"", None} for value in record.values()):
            records.append(record)
    return records


def _cell_value(cell: ET.Element, shared: list[str], ns: dict[str, str]) -> Any:
    cell_type = cell.attrib.get("t")
    if cell_type == "inlineStr":
        text = cell.find(".//main:t", ns)
        return text.text if text is not None else ""
    value_node = cell.find("main:v", ns)
    if value_node is None or value_node.text is None:
        return ""
    value = value_node.text
    if cell_type == "s":
        try:
            return shared[int(value)]
        except (ValueError, IndexError):
            return value
    try:
        number = float(value)
    except ValueError:
        return value
    return int(number) if number.is_integer() else number


def _column_index(ref: str) -> int:
    letters = re.sub(r"[^A-Z]", "", ref.upper())
    value = 0
    for letter in letters:
        value = value * 26 + (ord(letter) - ord("A") + 1)
    return max(value - 1, 0)


def _normalize(value: Any) -> str:
    return re.sub(r"[^a-z0-9]+", "_", str(value or "").strip().lower()).strip("_")
