from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from ulp_project.plan_c_geometry import compute_plan_c_geometry  # noqa: E402
from ulp_project.plan_c_processor import _build_days_prediction  # noqa: E402
from ulp_project.plan_c_zone_overlay import build_zone_overlay_summary  # noqa: E402


def main() -> int:
    detections = [
        {"class_name": "struktur_penyangga", "bbox_xyxy": [100, 200, 180, 1200], "confidence": 0.92, "review_status": "ACCEPT"},
        {"class_name": "konduktor", "bbox_xyxy": [50, 350, 950, 370], "confidence": 0.9, "review_status": "ACCEPT"},
        {"class_name": "pohon_sono", "bbox_xyxy": [400, 820, 720, 1200], "confidence": 0.91, "review_status": "ACCEPT"},
    ]
    geometry = compute_plan_c_geometry(detections, metadata={}, manual_inputs={})
    prediction = _build_days_prediction(geometry=geometry, growth={"growth_rate_m_per_quarter": 0.3})
    _assert(prediction["prediction_status"] == "PREDICTION_DAYS_READY", f"prediction not ready: {prediction}")
    _assert(isinstance(prediction["prediction_days"], int), "prediction_days not int")
    _assert("bulan" in prediction["prediction_window"] and "hari" in prediction["prediction_window"], "month/day window missing")
    _assert(prediction["growth_rate_m_per_day"] == round(0.3 / 91.25, 6), "daily growth formula mismatch")

    zone = build_zone_overlay_summary(detections, geometry, image_width=1000, image_height=1600)
    _assert(zone["zone_status"] == "precise", f"zone not precise: {zone}")
    _assert(zone["zone_tebang_y1"] == geometry["conductor_y"], "zona tebang not anchored at conductor")
    _assert(zone["zone_tebang_y2"] > zone["zone_tebang_y1"], "3m boundary missing")
    _assert(zone["zone_pantau_y2"] > zone["zone_pantau_y1"], "6m boundary missing")

    tebang = _build_days_prediction(
        geometry={**geometry, "clearance_estimate_m": 2.4, "risk_status": "ZONA_TEBANG"},
        growth={"growth_rate_m_per_quarter": 0.3},
    )
    _assert(tebang["prediction_days"] == 0, "tebang prediction should be immediate")
    _assert(tebang["prediction_window"] == "0 bulan 0 hari", "tebang window should be zero")

    missing = compute_plan_c_geometry([detections[-1]], metadata={}, manual_inputs={})
    _assert(missing["risk_status"].startswith("DATA_TIDAK_CUKUP"), "missing data should stay controlled")

    print("PLAN_C_PREDICTION_DAYS_SMOKE_PASS")
    print(f"prediction_window={prediction['prediction_window']}")
    print(f"zone_tebang_y1={zone['zone_tebang_y1']}")
    print(f"zone_tebang_y2={zone['zone_tebang_y2']}")
    return 0


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


if __name__ == "__main__":
    raise SystemExit(main())
