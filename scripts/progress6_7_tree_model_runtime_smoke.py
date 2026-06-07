from __future__ import annotations

import base64
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ulp_project.tree_detection_runtime import TREE_MODEL_PATH, infer_tree_candidate, tree_model_status  # noqa: E402


def run_smoke() -> dict[str, object]:
    image = "data:image/png;base64," + "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+/p9sAAAAASUVORK5CYII="
    status = tree_model_status()
    inference = infer_tree_candidate({"frame_image_base64": image})
    checks = {
        "bestpt_present_or_safe_missing": TREE_MODEL_PATH.exists() == (status.get("tree_model_status") == "TREE_MODEL_READY_CANDIDATE"),
        "tree_model_candidate_if_bestpt_exists": (not TREE_MODEL_PATH.exists()) or status.get("tree_model_status") == "TREE_MODEL_READY_CANDIDATE",
        "inference_no_exception_status": inference.get("status") in {
            "TREE_MODEL_FRAME_PROCESSED_CANDIDATE",
            "TREE_MODEL_INFERENCE_FAILED_SAFE",
            "MODEL_NOT_READY_NO_FAKE_DETECTION",
            "FRAME_DECODE_FAILED_SAFE",
        },
        "no_fake_pole": inference.get("pole_detected") is False,
        "no_fake_conductor": inference.get("conductor_detected") is False,
        "no_fake_detection": inference.get("no_fake_detection") is True,
    }
    return {
        "status": "PROGRESS_6_7_TREE_MODEL_RUNTIME_PASS" if all(checks.values()) else "PROGRESS_6_7_TREE_MODEL_RUNTIME_FAIL",
        "checks": checks,
        "tree_model_status": status,
        "inference_status": inference.get("status"),
    }


def main() -> int:
    result = run_smoke()
    print(json.dumps(result, indent=2, ensure_ascii=False))
    print(result["status"])
    return 0 if result["status"].endswith("_PASS") else 1


if __name__ == "__main__":
    raise SystemExit(main())
