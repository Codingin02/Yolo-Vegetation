from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ulp_project.growth_regression_model import growth_regression_status, predict_growth_regression  # noqa: E402


def run_smoke() -> dict[str, object]:
    status = growth_regression_status()
    prediction = predict_growth_regression({"point_id": "V001_pohon_sono"})
    checks = {
        "proxy_source": status.get("source_status") == "PROXY_NOT_FIELD_OBSERVED",
        "not_final": status.get("not_final_biological_accuracy") is True,
        "model_status_safe": status.get("growth_model_status")
        in {"GROWTH_MODEL_READY_PROXY_VALIDATED", "GROWTH_MODEL_PROXY_FALLBACK_READY", "GROWTH_MODEL_NOT_READY_NO_DATA"},
        "metrics_if_validated": status.get("growth_model_status") != "GROWTH_MODEL_READY_PROXY_VALIDATED"
        or all(status.get(key) is not None for key in ["selected_model_name", "validation_mae", "validation_rmse", "validation_r2"]),
        "eta_requires_geometry": prediction.get("eta_3m_status") == "INSUFFICIENT_GEOMETRY_DATA",
        "prediction_proxy": prediction.get("source_status") == "PROXY_NOT_FIELD_OBSERVED",
    }
    return {
        "status": "PROGRESS_6_9_GROWTH_MODEL_SMOKE_PASS" if all(checks.values()) else "PROGRESS_6_9_GROWTH_MODEL_SMOKE_FAIL",
        "checks": checks,
        "growth_model_status": status.get("growth_model_status"),
        "selected_model_name": status.get("selected_model_name"),
        "validation_mae": status.get("validation_mae"),
        "validation_rmse": status.get("validation_rmse"),
        "validation_r2": status.get("validation_r2"),
        "row_count": status.get("row_count"),
    }


def main() -> int:
    result = run_smoke()
    print(json.dumps(result, indent=2, ensure_ascii=False))
    print(result["status"])
    return 0 if result["status"].endswith("_PASS") else 1


if __name__ == "__main__":
    raise SystemExit(main())
