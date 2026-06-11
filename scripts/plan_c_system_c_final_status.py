"""Print a safe read-only status summary for System C final."""

from __future__ import annotations

import json
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from ulp_project.plan_c_system_c_download_manager import DATASET_FINAL_ROOT, SHARED_DOWNLOAD_ROOT  # noqa: E402
from ulp_project.plan_c_system_c_model_registry import load_model_registry  # noqa: E402
from ulp_project.plan_c_system_c_runtime_selector import select_plan_c_runtime_model  # noqa: E402
from ulp_project.plan_c_system_c_source_registry import system_c_source_registry  # noqa: E402
from ulp_project.plan_c_system_c_training_gate import run_training_gate  # noqa: E402

DOCS_DIR = PROJECT_ROOT / "docs" / "progress8" / "system_c_final"
REQUIRED_DOCS = [
    "00_README_SYSTEM_C_FINAL.md",
    "01_SYSTEM_C_ARCHITECTURE_FINAL.md",
    "02_DATASET_FINAL_TARGET_AND_FOLDER_POLICY.md",
    "03_SOURCE_REGISTRY_25_PLUS.md",
    "04_LEGAL_LICENSE_AND_DOWNLOAD_POLICY.md",
    "05_AUTOLABEL_AND_BOUNDING_POLICY.md",
    "06_ROBOFLOW_REVIEW_PACKAGE_WORKFLOW.md",
    "07_YOLOV8_TRAINING_GATE_AND_TRAINING_PLAN.md",
    "08_MODEL_REGISTRY_AND_RUNTIME_INTEGRATION.md",
    "09_RUNTIME_PLAN_C_FINAL_ACCEPTANCE.md",
    "10_FIELD_TEST_HP_NGROK_FINAL_RUNBOOK.md",
    "11_FINAL_REPORT_WORDING_AND_CLAIM_POLICY.md",
    "12_CODEX_MASTER_PROMPT_SYSTEM_C_FINAL.md",
    "13_POWERSHELL_INSTALL_AND_RUNBOOK.md",
    "14_FAILURE_RECOVERY_AND_ANTI_REPEAT.md",
    "LOCAL_PATHS_SYSTEM_C_FINAL.md",
    "MANIFEST_SYSTEM_C_FINAL.json",
]


def _count_files(root: Path, suffixes: set[str]) -> int:
    if not root.exists():
        return 0
    return sum(1 for path in root.rglob("*") if path.is_file() and path.suffix.lower() in suffixes)


def main() -> int:
    missing_docs = [name for name in REQUIRED_DOCS if not (DOCS_DIR / name).exists()]
    gate = run_training_gate()
    result = {
        "status": "SYSTEM_C_FINAL_STATUS_READY",
        "project_root": str(PROJECT_ROOT),
        "docs_dir": str(DOCS_DIR),
        "missing_expected_docs": missing_docs,
        "missing_expected_count": len(missing_docs),
        "source_registry_count": len(system_c_source_registry()),
        "download_root": str(SHARED_DOWNLOAD_ROOT),
        "dataset_final_root": str(DATASET_FINAL_ROOT),
        "dataset_root_exists": DATASET_FINAL_ROOT.exists(),
        "classes_txt_exists": (DATASET_FINAL_ROOT / "classes.txt").exists(),
        "data_yaml_exists": (DATASET_FINAL_ROOT / "data.yaml").exists(),
        "dataset_image_count": _count_files(DATASET_FINAL_ROOT / "images", {".jpg", ".jpeg", ".png", ".webp"}),
        "dataset_label_count": _count_files(DATASET_FINAL_ROOT / "labels", {".txt"}),
        "training_gate": gate,
        "model_registry": load_model_registry(),
        "runtime_selector": select_plan_c_runtime_model(),
    }
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
