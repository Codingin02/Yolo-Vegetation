from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ulp_project.realtime_stability_filter import apply_stability_filter, reset_stability_filter  # noqa: E402


def run_smoke() -> dict[str, object]:
    session_id = "P68_STABILITY"
    reset_stability_filter(session_id)
    outputs = []
    raw_sequence = [
        {"tree_detected": True, "detected_classes": ["pohon_sono"], "geometry_status": "GEOMETRY_BLOCKED_NO_MULTICLASS_MODEL"},
        {"tree_detected": False, "detected_classes": [], "geometry_status": "GEOMETRY_BLOCKED_NO_MULTICLASS_MODEL"},
        {"tree_detected": True, "detected_classes": ["pohon_sono"], "geometry_status": "GEOMETRY_BLOCKED_NO_MULTICLASS_MODEL"},
        {"tree_detected": False, "detected_classes": [], "geometry_status": "GEOMETRY_BLOCKED_NO_MULTICLASS_MODEL"},
        {"tree_detected": True, "detected_classes": ["pohon_sono"], "geometry_status": "GEOMETRY_BLOCKED_NO_MULTICLASS_MODEL"},
        {"tree_detected": True, "detected_classes": ["pohon_sono"], "geometry_status": "GEOMETRY_BLOCKED_NO_MULTICLASS_MODEL"},
    ]
    for index, raw in enumerate(raw_sequence):
        outputs.append(apply_stability_filter(session_id, raw, now=1000.0 + index * 3.0))
    checks = {
        "stabilizing_before_window": outputs[0]["stability_status"] == "STABILIZING",
        "stable_after_min_frames": outputs[-1]["stability_status"] == "STABLE_CANDIDATE_READY",
        "latest_confirmed_exists": bool(outputs[-1].get("latest_confirmed_result")),
        "raw_not_published_too_early": outputs[2]["published_result_status"] == "UNSTABLE_DETECTION_NOT_PUBLISHED",
        "no_spam_report_per_frame": all(item.get("no_spam_report_per_frame") is True for item in outputs),
    }
    return {
        "status": "PROGRESS_6_8_STABILITY_FILTER_PASS" if all(checks.values()) else "PROGRESS_6_8_STABILITY_FILTER_FAIL",
        "checks": checks,
        "final": outputs[-1],
    }


def main() -> int:
    result = run_smoke()
    print(json.dumps(result, indent=2, ensure_ascii=False))
    print(result["status"])
    return 0 if result["status"].endswith("_PASS") else 1


if __name__ == "__main__":
    raise SystemExit(main())
