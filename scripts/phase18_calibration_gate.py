from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ulp_project.calibration_workflow import create_calibration_session, load_calibration_template_columns, validate_calibration_payload  # noqa: E402


def main() -> int:
    columns = load_calibration_template_columns()
    missing = validate_calibration_payload({})["quality_status"] == "CALIBRATION_NOT_READY"
    valid = create_calibration_session(
        {
            "point_id": "V001_pohon_sono",
            "reference_type": "manual_reference",
            "known_height_m": 12,
            "reference_bbox_height_px": 400,
            "image_width_px": 1280,
            "image_height_px": 720,
        },
        write_runtime=False,
    )
    checks = {
        "template_columns": all(name in columns for name in ["calibration_id", "point_id", "known_height_m", "estimated_m_per_px", "quality_status"]),
        "missing_not_ready": missing,
        "valid_scale": valid["session"]["estimated_m_per_px"] == 0.03,
        "runtime_not_required_for_gate": valid["runtime_written"] is False,
    }
    passed = all(checks.values())
    status = "PHASE18_CALIBRATION_WORKFLOW_READY" if passed else "PHASE18_CALIBRATION_WORKFLOW_FAIL"
    print(json.dumps({"status": status, "checks": checks, "valid": valid}, indent=2, ensure_ascii=False))
    print(status)
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
