from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ulp_project.progress_status_consistency import build_status_consistency_audit


def main() -> int:
    result = build_status_consistency_audit(ROOT)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    status = result["status_consistency"]
    if status in {
        "REAL_MODEL_HANDOFF_READY",
        "PIPELINE_READY_BUT_REAL_MODEL_NOT_AVAILABLE",
        "DATASET_PIPELINE_READY_TRAINING_OUTPUT_NOT_FOUND",
        "MODEL_NOT_READY_STATUS_CONSISTENT",
    }:
        print("PROGRESS_6_3_STATUS_CONSISTENCY_AUDIT_PASS")
        return 0
    print("PROGRESS_6_3_STATUS_CONSISTENCY_FAILED")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
