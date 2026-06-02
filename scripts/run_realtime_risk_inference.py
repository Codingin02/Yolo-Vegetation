from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ulp_project.clearance_estimation import estimate_clearance_to_asset  # noqa: E402
from ulp_project.inference_runtime import run_image_inference  # noqa: E402
from ulp_project.risk_decision_engine import build_risk_decision  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Realtime risk inference skeleton; no fake detections.")
    parser.add_argument("--image", default="field-capture-placeholder.jpg")
    parser.add_argument("--mode", choices=["dry-run"], default="dry-run")
    parser.add_argument("--manual-clearance-m", type=float, default=None)
    args = parser.parse_args(argv)
    inference = run_image_inference(args.image)
    clearance = estimate_clearance_to_asset(None, None, None, "span")
    decision = build_risk_decision(args.manual_clearance_m, {}, nearest_asset_type="span")
    print(
        json.dumps(
            {
                "status": "MODEL_NOT_READY" if inference["status"] == "MODEL_NOT_READY" else "MODEL_READY_PROVISIONAL",
                "inference": inference,
                "clearance": clearance,
                "risk_decision": decision,
                "not_accuracy_claim": True,
            },
            indent=2,
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
