from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from ulp_project.plan_c_geometry import compute_plan_c_geometry  # noqa: E402
from ulp_project.plan_c_processor import _extract_gps  # noqa: E402


DETECTIONS = [
    {"class_name": "struktur_penyangga", "bbox_xyxy": [100, 200, 180, 1200], "confidence": 0.92, "review_status": "ACCEPT"},
    {"class_name": "konduktor", "bbox_xyxy": [50, 340, 950, 360], "confidence": 0.9, "review_status": "ACCEPT"},
    {"class_name": "konduktor", "bbox_xyxy": [50, 380, 950, 400], "confidence": 0.9, "review_status": "ACCEPT"},
    {"class_name": "pohon_sono", "bbox_xyxy": [400, 820, 720, 1200], "confidence": 0.91, "review_status": "ACCEPT"},
]


def main() -> int:
    gps = _extract_gps(
        {
            "tree_anchor_gps": '{"latitude":-7.231,"longitude":112.735,"accuracy_m":5}',
            "shutter_gps": '{"latitude":-7.23105,"longitude":112.73504,"accuracy_m":6}',
            "gps_accuracy_m": "6",
        }
    )
    _assert(gps["gps_valid"], "GPS should be valid")
    _assert(gps["gps_distance_from_anchor_m"] is not None and gps["gps_distance_from_anchor_m"] > 0, "GPS distance missing")
    _assert(gps["estimated_steps_from_anchor"] is not None and gps["estimated_steps_from_anchor"] > 0, "estimated steps missing")
    _assert(gps["gps_distance_status"] == "GPS_DISTANCE_ACCEPTED", "GPS status should be accepted")

    geometry = compute_plan_c_geometry(DETECTIONS, metadata={}, manual_inputs={})
    _assert(geometry["geometry_status"] == "GEOMETRY_READY_PROVISIONAL", f"geometry not ready: {geometry}")
    _assert(geometry["structure_height_source"] == "STRUCTURE_HEIGHT_CONFIG_DEFAULT", "structure source not tagged")
    _assert(geometry["tree_height_estimate_m"] is not None and geometry["tree_height_estimate_m"] > 0, "tree height missing")
    _assert(geometry["conductor_height_m"] is not None and geometry["conductor_height_m"] > 0, "conductor height missing")
    _assert(geometry["clearance_estimate_m"] is not None, "clearance missing")
    _assert(geometry["conductor_group_count"] >= 2, "multiple conductor count missing")
    _assert(geometry["zone_status"] == "precise", "zone should be precise with structure scale")
    _assert(geometry["zone_tebang_y1"] == geometry["conductor_y"], "zona tebang must start at conductor")
    _assert(geometry["zone_tebang_y2"] > geometry["zone_tebang_y1"], "zona tebang 3m boundary missing")
    _assert(geometry["zone_pantau_y2"] > geometry["zone_pantau_y1"], "zona pantau 6m boundary missing")

    print("PLAN_C_GPS_ANCHOR_GEOMETRY_SMOKE_PASS")
    print(f"gps_distance_from_anchor_m={gps['gps_distance_from_anchor_m']}")
    print(f"estimated_steps_from_anchor={gps['estimated_steps_from_anchor']}")
    print(f"clearance_estimate_m={geometry['clearance_estimate_m']}")
    return 0


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


if __name__ == "__main__":
    raise SystemExit(main())
