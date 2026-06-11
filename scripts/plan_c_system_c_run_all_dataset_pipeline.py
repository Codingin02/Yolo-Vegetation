"""Run the safe System C dataset pipeline.

The command is intentionally conservative: it prepares registry manifests,
review packages, gates, and optional train/register steps without inventing
images, labels, metrics, or model files.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from ulp_project.plan_c_system_c_download_manager import (  # noqa: E402
    build_empty_manifest_from_registry,
    collect_candidates_from_registry,
    download_candidate,
    ensure_system_c_dirs,
    write_manifest,
)
from ulp_project.plan_c_system_c_model_registry import register_model_if_valid  # noqa: E402
from ulp_project.plan_c_system_c_roboflow_package import build_roboflow_package  # noqa: E402
from ulp_project.plan_c_system_c_train_yolov8 import train_if_ready  # noqa: E402
from ulp_project.plan_c_system_c_training_gate import run_training_gate  # noqa: E402
from ulp_project.plan_c_system_c_yolo_exporter import build_review_split, write_class_files  # noqa: E402

MANIFEST_PATH = PROJECT_ROOT / "docs" / "progress8" / "system_c_final" / "MANIFEST_SYSTEM_C_FINAL.json"
LOCAL_PATHS_PATH = PROJECT_ROOT / "docs" / "progress8" / "system_c_final" / "LOCAL_PATHS_SYSTEM_C_FINAL.md"


def main() -> int:
    parser = argparse.ArgumentParser(description="Safe System C dataset pipeline")
    parser.add_argument("--download", action="store_true", help="Enable legal candidate downloads when source rows include direct image URLs.")
    parser.add_argument("--autolabel", action="store_true", help="Prepare review-only labels when an explicit engine is available.")
    parser.add_argument("--build-roboflow", action="store_true", help="Build Roboflow manual review package.")
    parser.add_argument("--gate", action="store_true", help="Run YOLO training gate.")
    parser.add_argument("--train-if-ready", action="store_true", help="Train only if the gate passes.")
    parser.add_argument("--register-if-valid", action="store_true", help="Register a valid trained model only after gate/model checks.")
    parser.add_argument("--model-path", default="", help="Optional trained model path for registry validation.")
    parser.add_argument("--limit-per-source", type=int, default=25, help="Maximum API candidates per source when --download is used.")
    args = parser.parse_args()

    ensure_system_c_dirs()
    write_class_files()
    rows = build_empty_manifest_from_registry()
    manifest = write_manifest(rows, stem="system_c_pipeline_manifest")
    result: dict[str, Any] = {
        "status": "SYSTEM_C_PIPELINE_COMPLETED_WITH_SAFE_SKIPS",
        "manifest_contract_exists": MANIFEST_PATH.exists(),
        "local_paths_doc_exists": LOCAL_PATHS_PATH.exists(),
        "manifest": manifest,
        "download": {
            "requested": bool(args.download),
            "status": "SOURCE_REGISTRY_READY_NO_DOWNLOAD_EXECUTED",
            "note": "Registered source adapters only; run source-specific acquisition with legal URLs before final training.",
        },
        "autolabel": {
            "requested": bool(args.autolabel),
            "status": "AUTOLABEL_REVIEW_ONLY_SKIPPED_NO_ENGINE",
            "not_ground_truth": True,
        },
    }

    if args.download:
        collected = collect_candidates_from_registry(limit_per_source=max(1, args.limit_per_source))
        candidate_rows = collected.get("rows", [])
        downloaded_rows = [download_candidate(row) for row in candidate_rows]
        rows = downloaded_rows or candidate_rows
        manifest = write_manifest(rows, stem="system_c_download_manifest")
        result["manifest"] = manifest
        result["download"] = {
            "requested": True,
            "status": "SYSTEM_C_DOWNLOAD_ATTEMPT_COMPLETE",
            "source_status": collected.get("source_status", {}),
            "summary": manifest.get("summary", {}),
            "note": "Only rows passing license/species filters are downloaded; no fake candidates are created.",
        }

    if args.build_roboflow:
        result["roboflow_package"] = build_roboflow_package(rows)

    if args.gate or args.train_if_ready or args.register_if_valid:
        gate = run_training_gate()
        result["training_gate"] = gate
    else:
        gate = None

    if args.train_if_ready:
        if gate and gate.get("status") == "YOLO_TRAINING_READY":
            result["training"] = train_if_ready()
        else:
            result["training"] = {"status": "YOLO_TRAINING_SKIPPED_DATASET_NOT_READY", "training_started": False}

    if args.register_if_valid:
        if args.model_path:
            result["model_registry"] = register_model_if_valid(model_path=args.model_path, gate_status=(gate or {}).get("status", ""))
        else:
            result["model_registry"] = {"status": "MODEL_REGISTRY_SKIPPED_MODEL_PATH_NOT_PROVIDED", "runtime_allowed": False}

    if args.autolabel:
        result["yolo_review_split"] = build_review_split([])

    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
