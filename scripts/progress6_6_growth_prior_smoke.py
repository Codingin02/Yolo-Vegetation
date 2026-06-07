from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ulp_project.flask_app import create_app  # noqa: E402
from ulp_project.growth_prior_loader import DEFAULT_POHON_SONO_XLSX, growth_prior_dataset_status  # noqa: E402


def run_smoke() -> dict[str, object]:
    client = create_app().test_client()
    status = growth_prior_dataset_status()
    api_status = client.get("/api/growth-prior/status")
    prediction = client.post("/api/growth-prior/predict", json={"point_id": "V001_pohon_sono", "clearance_m": 4.5, "soil_ph_actual": 6.5})
    predict_json = prediction.get_json() or {}
    excel_exists = DEFAULT_POHON_SONO_XLSX.exists()
    checks = {
        "endpoint_status_no_500": api_status.status_code != 500,
        "predict_no_500": prediction.status_code != 500,
        "proxy_source_status": predict_json.get("source_status") == "PROXY_NOT_FIELD_OBSERVED",
        "no_final_claim": predict_json.get("no_fake_final_claim") is True and predict_json.get("not_final_accuracy_claim") is True,
    }
    if excel_exists:
        checks["excel_ready"] = status.get("status") == "GROWTH_PRIOR_READY_PROXY_DATASET"
        checks["required_sheets"] = all((status.get("sheet_status") or {}).get(sheet, {}).get("present") for sheet in ["Dataset_Quarterly_Grid", "Field_Observation_Template", "Placement_Guide"])
        checks["row_count_positive"] = int(status.get("row_count") or 0) > 0
    else:
        checks["dataset_not_found_graceful"] = status.get("status") == "GROWTH_PRIOR_DATASET_NOT_FOUND"
    return {
        "status": "PROGRESS_6_6_GROWTH_PRIOR_SMOKE_PASS" if all(checks.values()) else "PROGRESS_6_6_GROWTH_PRIOR_SMOKE_FAIL",
        "checks": checks,
        "dataset_status": status,
        "prediction_status": predict_json.get("growth_prior_status"),
    }


def main() -> int:
    result = run_smoke()
    print(json.dumps(result, indent=2, ensure_ascii=False))
    print(result["status"])
    return 0 if result["status"].endswith("_PASS") else 1


if __name__ == "__main__":
    raise SystemExit(main())
