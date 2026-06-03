from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ulp_project.flask_app import create_app  # noqa: E402


def build_smoke_status() -> dict[str, object]:
    client = create_app().test_client()
    no_model = client.post("/api/field/manual-prediction", json={"point_id": "V001_pohon_sono"}).get_json() or {}
    manual = client.post(
        "/api/field/manual-prediction",
        json={
            "point_id": "V001_pohon_sono",
            "species": "pohon_sono",
            "asset_type": "span",
            "clearance_m": 5.0,
            "growth_rate_m_per_day": 0.01,
            "measurement_source": "manual",
        },
    ).get_json() or {}
    unsafe = client.post(
        "/api/field/manual-prediction",
        json={
            "point_id": "V001_pohon_sono",
            "clearance_m": 2.75,
            "growth_rate_m_per_day": 0.01,
            "measurement_source": "manual",
        },
    ).get_json() or {}
    checks = {
        "no_model_model_not_ready": no_model.get("model_status") == "MODEL_NOT_READY",
        "no_fake_detection": no_model.get("detections") == [],
        "manual_eta_threshold_3m": manual.get("eta_days") == 200.0 and manual.get("clearance_threshold_m") == 3.0,
        "manual_not_final_claim": manual.get("not_accuracy_claim") is True,
        "unsafe_eta_zero": unsafe.get("eta_days") == 0 and unsafe.get("risk_status") == "ALREADY_WITHIN_UNSAFE_ZONE",
        "unsafe_floor_display": unsafe.get("clearance_display_m_integer_floor") == 2 and unsafe.get("clearance_raw_m") == 2.75,
        "unsafe_action_critical": unsafe.get("action_priority") == "CRITICAL",
    }
    passed = all(checks.values())
    return {
        "status": "PHASE5_2_PREDICTION_SMOKE_PASS" if passed else "PHASE5_2_PREDICTION_SMOKE_FAIL",
        "checks": checks,
        "manual_prediction": manual,
        "unsafe_prediction": unsafe,
    }


def main() -> int:
    result = build_smoke_status()
    print(json.dumps(result, indent=2, ensure_ascii=False))
    print(result["status"])
    return 0 if result["status"].endswith("_PASS") else 1


if __name__ == "__main__":
    raise SystemExit(main())
