from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ulp_project.geometry_reference_scaling import compute_reference_geometry, load_geometry_reference_config  # noqa: E402
from ulp_project.realtime_yolo_detection_pipeline import model_readiness_status, process_realtime_yolo_frame  # noqa: E402


MOCK_MULTICLASS = [
    {"class_name": "struktur_penyangga", "confidence": 0.9, "bbox_xyxy": [110, 80, 150, 680]},
    {"class_name": "konduktor", "confidence": 0.86, "bbox_xyxy": [20, 210, 620, 230]},
    {"class_name": "pohon_sono", "confidence": 0.88, "bbox_xyxy": [260, 300, 520, 660]},
]


def run_smoke() -> dict[str, object]:
    readiness = model_readiness_status()
    tree_only = process_realtime_yolo_frame({"frame_image_base64": ""})
    geometry_tree_only = tree_only.get("geometry") or {}
    geometry_mock = compute_reference_geometry(MOCK_MULTICLASS, frame_width=720, frame_height=720)
    pipeline_mock = process_realtime_yolo_frame({"mock_multiclass_detections": MOCK_MULTICLASS, "frame_width": 720, "frame_height": 720})
    config = load_geometry_reference_config()
    checks = {
        "tree_model_candidate_or_safe_not_ready": readiness["status"] in {"TREE_MODEL_READY_CANDIDATE", "MODEL_NOT_READY_NO_FAKE_DETECTION", "MULTICLASS_MODEL_READY_CANDIDATE"},
        "tree_model_path_detected_if_available": readiness["status"] != "TREE_MODEL_READY_CANDIDATE" or "v001_pohon_sono_only_v2" in str(readiness.get("tree_model_path", "")),
        "pole_conductor_not_faked_when_tree_only": tree_only.get("pole_model_status") == "POLE_MODEL_NOT_READY" and tree_only.get("conductor_model_status") == "CONDUCTOR_MODEL_NOT_READY",
        "geometry_blocked_without_pole_conductor": "BLOCKED" in str(geometry_tree_only.get("geometry_status")),
        "mock_multiclass_geometry_candidate": geometry_mock.get("geometry_status") == "GEOMETRY_READY_CANDIDATE",
        "pipeline_mock_detects_all_classes": pipeline_mock.get("tree_detected") and pipeline_mock.get("pole_detected") and pipeline_mock.get("conductor_detected"),
        "reference_config_not_final": config.get("reference_policy") == "CONFIGURABLE_FIELD_REFERENCE_NOT_FINAL" and config.get("default_reference_status") == "NEEDS_PLN_CONFIRMATION",
        "no_fake_clearance": geometry_tree_only.get("no_fake_clearance") is True and geometry_mock.get("no_fake_clearance") is True,
    }
    return {
        "status": "PROGRESS_6_8_AUTO_YOLO_GEOMETRY_CONTRACT_PASS" if all(checks.values()) else "PROGRESS_6_8_AUTO_YOLO_GEOMETRY_CONTRACT_FAIL",
        "checks": checks,
        "readiness": readiness,
        "tree_only_geometry_status": geometry_tree_only.get("geometry_status"),
        "mock_geometry_status": geometry_mock.get("geometry_status"),
    }


def main() -> int:
    result = run_smoke()
    print(json.dumps(result, indent=2, ensure_ascii=False))
    print(result["status"])
    return 0 if result["status"].endswith("_PASS") else 1


if __name__ == "__main__":
    raise SystemExit(main())
