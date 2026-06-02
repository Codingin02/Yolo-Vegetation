from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ulp_project.classes import CLASS_ORDER  # noqa: E402
from ulp_project.dataset_split import build_dataset, write_data_yaml  # noqa: E402
from ulp_project.makesense_import import import_makesense_export  # noqa: E402
from ulp_project.paths import DATASET_BOTOL_DIR, FIELD_DATASET_DIR, PROJECT_ROOT  # noqa: E402
from ulp_project.risk_stub import evaluate_vegetation_risk  # noqa: E402


def run_help(script: str) -> tuple[bool, str]:
    completed = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / script), "--help"],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    return completed.returncode == 0, completed.stdout.splitlines()[0] if completed.stdout else ""


def check_temp_import_dry_run() -> tuple[bool, str]:
    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        image_dir = root / "images"
        export_dir = root / "export"
        labels_dir = root / "labels"
        image_dir.mkdir()
        export_dir.mkdir()
        labels_dir.mkdir()
        (image_dir / "V001_sample.jpg").write_bytes(b"not-real-image")
        (export_dir / "V001_sample.txt").write_text("2 0.5 0.5 0.2 0.3\n", encoding="utf-8")
        summary = import_makesense_export(export_dir, image_dir, labels_dir, mode="dry-run")
        copied = list(labels_dir.glob("*.txt"))
        ok = summary.matched_labels == 1 and not copied
        return ok, f"matched={summary.matched_labels}, copied_files={len(copied)}"


def check_temp_data_yaml() -> tuple[bool, str]:
    with tempfile.TemporaryDirectory() as temp_dir:
        target = Path(temp_dir) / "field_multiclass_v1"
        output = write_data_yaml(target)
        text = output.read_text(encoding="utf-8")
        ok = "0: struktur_penyangga" in text and "1: konduktor" in text and "2: pohon_sono" in text
        return ok, str(output)


def main() -> int:
    checks: list[tuple[str, bool, str]] = []
    checks.append(("branch_root", PROJECT_ROOT.name == "ULP_Project", str(PROJECT_ROOT)))
    checks.append(("class_order", CLASS_ORDER == {0: "struktur_penyangga", 1: "konduktor", 2: "pohon_sono"}, str(CLASS_ORDER)))
    checks.append(("dataset_botol_not_main", DATASET_BOTOL_DIR != FIELD_DATASET_DIR, str(FIELD_DATASET_DIR)))
    checks.append(("import_dry_run_no_copy", *check_temp_import_dry_run()))
    checks.append(("data_yaml_order", *check_temp_data_yaml()))

    risk = evaluate_vegetation_risk({})
    checks.append(("risk_no_final_claim", risk.status == "ENV_DATA_NOT_AVAILABLE" and risk.risk_score is None, risk.status))

    for script in [
        "import_makesense_yolo_export.py",
        "validate_yolo_labels.py",
        "build_field_multiclass_dataset.py",
        "generate_data_yaml.py",
        "train_yolov8_field_multiclass.py",
        "build_field_map.py",
        "export_project_metadata_csv.py",
    ]:
        ok, detail = run_help(script)
        checks.append((f"help_{script}", ok, detail))

    summary = build_dataset(
        point="V001_pohon_sono",
        target_dir=FIELD_DATASET_DIR,
        val_ratio=0.2,
        seed=23050874166,
        mode="dry-run",
        force=False,
    )
    checks.append(("real_dataset_dry_run_waits_for_labels", summary.status == "LABELS_NOT_READY", summary.status))

    failed = False
    for name, ok, detail in checks:
        status = "PASS" if ok else "FAIL"
        print(f"{status}: {name}: {detail}")
        failed = failed or not ok

    print("PHASE2_SYSTEM_SMOKE_FAIL" if failed else "PHASE2_SYSTEM_SMOKE_PASS")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
