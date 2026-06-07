from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ulp_project.growth_regression_model import find_growth_proxy_excel, growth_regression_status, predict_growth_regression  # noqa: E402


def run_smoke() -> dict[str, object]:
    excel = find_growth_proxy_excel()
    status = growth_regression_status()
    without_clearance = predict_growth_regression({"point_id": "V001_pohon_sono"})
    with_clearance = predict_growth_regression({"point_id": "V001_pohon_sono", "clearance_m": 5.0})
    checks = {
        "excel_folder_detected_or_graceful": bool(excel) or status.get("status") == "GROWTH_PRIOR_DATASET_NOT_FOUND",
        "regression_ready_or_graceful": status.get("status")
        in {
            "GROWTH_LINEAR_REGRESSION_READY_PROXY_DATASET",
            "GROWTH_PRIOR_READY_PROXY_DATASET_NO_REGRESSION",
            "GROWTH_PRIOR_DATASET_NOT_FOUND",
            "GROWTH_PRIOR_DATASET_INVALID",
        },
        "source_proxy": status.get("source_status") == "PROXY_NOT_FIELD_OBSERVED",
        "not_final": status.get("not_final_biological_accuracy") is True,
        "eta_requires_clearance": without_clearance.get("eta_3m_status") == "INSUFFICIENT_GEOMETRY_DATA",
        "eta_with_clearance_has_status": with_clearance.get("eta_3m_status") in {"ETA_3M_PROXY_PRIOR_READY", "INSUFFICIENT_GEOMETRY_DATA"},
    }
    return {
        "status": "PROGRESS_6_7_GROWTH_REGRESSION_PASS" if all(checks.values()) else "PROGRESS_6_7_GROWTH_REGRESSION_FAIL",
        "checks": checks,
        "excel_path": str(excel or ""),
        "regression_status": status.get("status"),
    }


def main() -> int:
    result = run_smoke()
    print(json.dumps(result, indent=2, ensure_ascii=False))
    print(result["status"])
    return 0 if result["status"].endswith("_PASS") else 1


if __name__ == "__main__":
    raise SystemExit(main())
