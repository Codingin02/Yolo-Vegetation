from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ulp_project.classes import CLASS_ORDER  # noqa: E402
from ulp_project.environmental_risk import score_environmental_risk  # noqa: E402
from ulp_project.map_builder import build_field_map_status  # noqa: E402
from ulp_project.spreadsheet_export import build_rows  # noqa: E402
from ulp_project.system_status import collect_project_status  # noqa: E402


def run_command(args: list[str]) -> tuple[bool, str]:
    completed = subprocess.run(
        [sys.executable, *args],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    return completed.returncode == 0, completed.stdout.strip()


def config_avoids_dataset_botol() -> bool:
    config = ROOT / "configs" / "project_paths.yaml"
    if not config.exists():
        return False
    text = config.read_text(encoding="utf-8").lower()
    main_path_lines = [
        line
        for line in text.splitlines()
        if any(key in line for key in ("field_dataset", "field_data_yaml", "review_images_selected", "makesense_export"))
    ]
    return all("dataset_botol" not in line for line in main_path_lines)


def flask_contract_importable() -> bool:
    try:
        from ulp_project.flask_app import create_app, get_model_state
    except Exception:
        return False
    model = get_model_state()
    if model["status"] != "MODEL_NOT_READY":
        return False
    try:
        app = create_app()
    except RuntimeError as exc:
        return "FLASK_NOT_INSTALLED" in str(exc)
    rules = {rule.rule for rule in app.url_map.iter_rules()}
    return {"/health", "/status", "/classes", "/points", "/map", "/predict-image"}.issubset(rules)


def main() -> int:
    status = collect_project_status(ROOT)
    checks: list[tuple[str, bool, str]] = []
    checks.append(("class_order", status["class_order_ok"], str(CLASS_ORDER)))
    checks.append(("dataset_botol_not_main", config_avoids_dataset_botol(), "configs/project_paths.yaml"))
    checks.append(("system_status_report", *run_command(["scripts/system_status_report.py", "--format", "text"])))
    checks.append(("import_makesense_dry_run", *run_command(["scripts/import_makesense_yolo_export.py", "--point", "V001_pohon_sono", "--mode", "dry-run"])))
    checks.append(("dataset_build_dry_run", *run_command(["scripts/build_field_multiclass_dataset.py", "--mode", "dry-run", "--val-ratio", "0.2", "--seed", "23050874166"])))
    checks.append(("train_launcher_dry_run", *run_command(["scripts/train_yolov8_field_multiclass.py", "--dry-run"])))
    checks.append(("flask_contract_importable", flask_contract_importable(), "create_app"))

    map_status = build_field_map_status(mode="dry-run")
    checks.append(("map_builder_dry_run", map_status["written"] is False, str(map_status)))
    checks.append(("spreadsheet_contract", isinstance(build_rows(), list), "build_rows"))
    risk_status = score_environmental_risk({})
    checks.append(("risk_stub_no_final_claim", risk_status["status"] == "DATA_NOT_READY" and risk_status["risk_score"] is None, risk_status["status"]))

    failed = False
    for name, ok, detail in checks:
        result = "PASS" if ok else "FAIL"
        first_line = detail.splitlines()[0] if isinstance(detail, str) and detail else str(detail)
        print(f"{result}: {name}: {first_line}")
        failed = failed or not ok

    labels_status = status["labels_selected"]["status"]
    final_status = "PHASE4_READY_FOR_DATASET_BUILD" if labels_status == "LABELS_READY" else "PHASE4_READY_WAITING_FOR_LABELS"
    print(final_status)
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
