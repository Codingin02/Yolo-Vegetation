from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ulp_project.risk_priority import evaluate_pln_vegetation_risk  # noqa: E402
from ulp_project.spreadsheet_report_writer import build_phase8_report_row, write_phase8_report  # noqa: E402


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run manual provisional vegetation risk estimate without model inference.")
    parser.add_argument("--sample", default="pohon_sono")
    parser.add_argument("--mode", choices=["dry-run", "write"], default="dry-run")
    parser.add_argument("--clearance-m", type=float, default=None)
    parser.add_argument("--growth-rate-m-per-day", type=float, default=None)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    decision = evaluate_pln_vegetation_risk(
        args.clearance_m,
        args.sample,
        environment={"season_label": "manual", "rainfall_30d_mm": 100, "soil_ph": 6.5, "soil_moisture_proxy": "manual"}
        if args.growth_rate_m_per_day is not None
        else {},
        allow_provisional=args.growth_rate_m_per_day is not None,
        base_growth_rate_override=args.growth_rate_m_per_day,
    )
    row = build_phase8_report_row(
        {
            "point_id": "V001_pohon_sono",
            "species": args.sample,
            "asset_type": "span",
            "minimum_clearance_m": args.clearance_m or "",
            "risk_priority": decision["risk_priority"],
            "recommended_action": decision["recommended_action"],
            "recommended_trim_deadline": decision["recommended_trim_deadline"],
            "days_to_contact_p50": decision["days_to_contact_p50"] or "",
            "months_to_contact_p50": decision["months_to_contact_p50"] or "",
            "growth_rate_base_m_per_day": decision.get("growth_rate_base_m_per_day", ""),
            "growth_rate_adjusted_m_per_day": decision.get("growth_rate_adjusted_m_per_day", ""),
            "model_status": "MODEL_NOT_READY",
            "calibration_status": "CALIBRATION_NOT_READY" if args.clearance_m is None else "CALIBRATION_PARTIAL",
            "environmental_data_status": "ENVIRONMENTAL_DATA_NOT_READY",
            "confidence": decision["confidence"],
        }
    )
    report = write_phase8_report([row], mode=args.mode)
    result = {"status": "MANUAL_RISK_DRY_RUN_READY" if args.mode == "dry-run" else report["status"], "decision": decision, "report": report}
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
