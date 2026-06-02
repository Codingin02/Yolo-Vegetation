from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ulp_project.risk_decision_engine import build_risk_decision  # noqa: E402
from ulp_project.species_growth_config import get_species_config  # noqa: E402
from ulp_project.vegetation_report_writer import build_report_row, write_reports  # noqa: E402


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run manual provisional vegetation risk estimate without model inference.")
    parser.add_argument("--sample", default="pohon_sono")
    parser.add_argument("--mode", choices=["dry-run", "write"], default="dry-run")
    parser.add_argument("--clearance-m", type=float, default=None)
    parser.add_argument("--growth-rate-m-per-day", type=float, default=None)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    species_config = get_species_config(args.sample)
    growth_inputs = {
        "species_base_growth_rate_m_per_day": args.growth_rate_m_per_day or species_config.get("base_growth_rate_m_per_day"),
        "season_multiplier": None,
        "rainfall_multiplier": None,
        "humidity_multiplier": None,
        "temperature_multiplier": None,
        "soil_ph_multiplier": None,
        "soil_moisture_multiplier": None,
        "pruning_history_multiplier": None,
        "local_calibration_multiplier": None,
    }
    decision = build_risk_decision(args.clearance_m, growth_inputs, nearest_asset_type="span")
    row = build_report_row(
        {
            "point_id": "V001_pohon_sono",
            "species": args.sample,
            "nearest_electrical_asset": "span",
            "clearance_to_asset_m": args.clearance_m or "",
            "risk_status": decision["risk_status"],
            "recommended_action": decision["recommended_action"],
            "priority_rank": decision["priority_rank"],
            "eta_days_min": decision["eta_days_min"] or "",
            "eta_days_mid": decision["eta_days_mid"] or "",
            "eta_days_max": decision["eta_days_max"] or "",
            "eta_months_mid": decision["eta_months_mid"] or "",
            "model_status": "MODEL_NOT_READY",
            "calibration_status": "CALIBRATION_NOT_READY" if args.clearance_m is None else "CALIBRATION_PARTIAL",
            "environmental_data_status": "ENVIRONMENTAL_DATA_NOT_READY",
            "data_quality_flags": ";".join(decision["data_quality_flags"]),
        }
    )
    report = write_reports([row], mode=args.mode)
    result = {"status": "MANUAL_RISK_DRY_RUN_READY" if args.mode == "dry-run" else report["status"], "decision": decision, "report": report}
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
