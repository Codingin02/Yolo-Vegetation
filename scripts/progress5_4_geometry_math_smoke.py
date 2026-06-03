from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ulp_project.progress5_4_clearance_estimator import estimate_clearance_from_detections  # noqa: E402
from ulp_project.progress5_4_pixel_metric_scaling import calculate_pixel_metric_scale  # noqa: E402
from ulp_project.progress5_4_temporal_smoothing import Progress54TemporalSmoother  # noqa: E402
from ulp_project.progress5_4_zone_policy import classify_progress5_4_zone  # noqa: E402


def build_smoke_status() -> dict[str, object]:
    scale = calculate_pixel_metric_scale(550, 11.0)
    geometry = estimate_clearance_from_detections(
        [
            {"class_name": "struktur_penyangga", "confidence": 0.9, "bbox_xyxy": [100, 50, 140, 600]},
            {"class_name": "konduktor", "confidence": 0.8, "bbox_xyxy": [60, 198, 420, 202]},
            {"class_name": "pohon_sono", "confidence": 0.85, "bbox_xyxy": [260, 350, 360, 600]},
        ],
        geometry_config={"default_pole_total_height_m": 11.0, "source_status": "SMOKE_TEST"},
    )
    smoother = Progress54TemporalSmoother({"smoothing_window": 5, "max_clearance_jump_m_per_update": 0.75, "track_hold_ms": 2000})
    smooth = [smoother.update(value, now_ms=idx * 1000) for idx, value in enumerate([5.0, 5.4, 5.5])]
    jump = smoother.update(6.5, now_ms=4000)
    checks = {
        "scale_550px_11m": scale["meter_per_px"] == 0.02,
        "clearance_geometry_ready": geometry["clearance_m"] == 3.0,
        "zone_tebang_boundary": classify_progress5_4_zone(3.0)["zone_status"] == "TEBANG",
        "zone_pantauan_boundary": classify_progress5_4_zone(4.0)["zone_status"] == "PANTAUAN",
        "zone_aman_above_4m": classify_progress5_4_zone(4.01)["zone_status"] == "AMAN",
        "smoothing_ready": smooth[-1]["stable_clearance_m"] == 5.4,
        "jitter_rejected": jump["smoothing_status"] == "JITTER_REJECTED",
    }
    passed = all(checks.values())
    return {"status": "PROGRESS5_4_GEOMETRY_MATH_SMOKE_PASS" if passed else "PROGRESS5_4_GEOMETRY_MATH_SMOKE_FAIL", "checks": checks}


def main() -> int:
    result = build_smoke_status()
    print(json.dumps(result, indent=2, ensure_ascii=False))
    print(result["status"])
    return 0 if result["status"].endswith("_PASS") else 1


if __name__ == "__main__":
    raise SystemExit(main())
