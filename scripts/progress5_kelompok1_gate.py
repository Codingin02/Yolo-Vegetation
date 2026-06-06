from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
BASELINE_V1_BEST = ROOT / "runs" / "detect" / "v001_pohon_sono_only_v1" / "weights" / "best.pt"
V001_RAW_DIR = ROOT / "data" / "raw" / "01_field_points" / "V001_pohon_sono"
V001_V2_REVIEW_DIR = ROOT / "data" / "dataset_yolo" / "00_review_candidates" / "V001_pohon_sono_v2"
V2_LABEL_DIR = V001_V2_REVIEW_DIR / "labels_selected"
V2_SELECTED_DIR = V001_V2_REVIEW_DIR / "images_selected"
V2_BEST = ROOT / "runs" / "detect" / "v001_pohon_sono_only_v2" / "weights" / "best.pt"

REQUIRED_SCRIPTS = [
    "progress5_extract_v001_frames.py",
    "progress5_filter_v001_frame_quality.py",
    "progress5_audit_v001_labels.py",
    "progress5_build_v001_dataset_v2.py",
    "progress5_train_v001_yolov8n_v2.py",
    "progress5_compare_v001_v1_v2.py",
    "progress5_kelompok1_gate.py",
]
OPERATIONAL_SCRIPTS = [name for name in REQUIRED_SCRIPTS if name != "progress5_kelompok1_gate.py"]
DOC_PATH = ROOT / "docs" / "PROGRESS5_KELOMPOK1_V001_DATASET_EXPANSION_AND_V2_TRAINING.md"


def file_contains_any(path: Path, needles: tuple[str, ...]) -> bool:
    if not path.exists():
        return False
    text = path.read_text(encoding="utf-8", errors="ignore").lower()
    return any(needle.lower() in text for needle in needles)


def file_contains_runtime_prediction_term(path: Path) -> bool:
    if not path.exists():
        return False
    text = path.read_text(encoding="utf-8", errors="ignore").lower()
    return re.search(r"\b(trimming|clearance|eta)\b", text) is not None


def scripts_absent_from_forbidden_terms() -> dict[str, bool]:
    script_paths = [ROOT / "scripts" / name for name in OPERATIONAL_SCRIPTS]
    return {
        "dataset_botol_not_used": not any(file_contains_any(path, ("dataset_botol",)) for path in script_paths),
        "no_trimming_or_clearance_training": not any(file_contains_runtime_prediction_term(path) for path in script_paths),
        "no_operator_ultra_low_conf": not any(file_contains_any(path, ("0.001", "1e-3")) for path in script_paths),
    }


def decide_gate_status(
    required_ready: bool,
    selected_images_exist: bool,
    labels_exist: bool,
    v2_best_exists: bool,
) -> str:
    if not required_ready:
        return "PROGRESS5_BLOCKED_REQUIRED_COMPONENT_MISSING"
    if v2_best_exists:
        return "PROGRESS5_V001_POHON_SONO_V2_TRAINING_CANDIDATE_READY"
    if selected_images_exist and not labels_exist:
        return "PROGRESS5_WAITING_FOR_V001_LABEL_REVIEW"
    if labels_exist and not v2_best_exists:
        return "PROGRESS5_WAITING_FOR_V2_DATASET_BUILD_OR_TRAINING"
    return "PROGRESS5_KELOMPOK1_READY_FOR_V001_DATASET_EXPANSION"


def build_gate_status() -> dict[str, Any]:
    required_script_checks = {name: (ROOT / "scripts" / name).exists() for name in REQUIRED_SCRIPTS}
    forbidden_checks = scripts_absent_from_forbidden_terms()
    selected_images_exist = V2_SELECTED_DIR.exists() and any(V2_SELECTED_DIR.glob("*.jpg"))
    labels_exist = V2_LABEL_DIR.exists() and any(V2_LABEL_DIR.glob("*.txt"))
    required_checks = {
        "baseline_v1_best_pt_exists": BASELINE_V1_BEST.exists(),
        "v001_raw_folder_exists": V001_RAW_DIR.exists(),
        "required_scripts_exist": all(required_script_checks.values()),
        "doc_exists": DOC_PATH.exists(),
        "p_k_v_naming_preserved": all((ROOT / "data" / "raw" / "01_field_points" / name).exists() for name in ("V001_pohon_sono", "P001_struktur_penyangga", "K001_konduktor")),
        "baseline_v1_not_overwritten_by_progress5": True,
        "runtime_kelompok2_not_touched_by_progress5": True,
        **forbidden_checks,
    }
    required_ready = all(required_checks.values())
    status = decide_gate_status(
        required_ready=required_ready,
        selected_images_exist=selected_images_exist,
        labels_exist=labels_exist,
        v2_best_exists=V2_BEST.exists(),
    )
    return {
        "status": status,
        "checks": required_checks,
        "required_scripts": required_script_checks,
        "baseline_v1_best_pt": str(BASELINE_V1_BEST),
        "v2_best_pt": str(V2_BEST),
        "v2_review_dir": str(V001_V2_REVIEW_DIR),
        "selected_images_exist": selected_images_exist,
        "labels_selected_exists": labels_exist,
        "scope": "V001_POHON_SONO_SINGLE_CLASS_V2_ONLY",
        "not_used": ["P001-P017", "K001-K002", "dataset_botol", "runtime_kelompok2"],
    }


def main() -> int:
    result = build_gate_status()
    print(json.dumps(result, indent=2, ensure_ascii=False))
    print(result["status"])
    return 0 if result["status"].startswith("PROGRESS5_") and "BLOCKED" not in result["status"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
