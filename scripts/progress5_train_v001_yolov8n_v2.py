from __future__ import annotations

import argparse
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SAFE_SEED = 1576037691
DEFAULT_DATA = ROOT / "data" / "dataset_yolo" / "v001_pohon_sono_only_v2" / "data.yaml"
DEFAULT_PROJECT = ROOT / "runs" / "detect"
DEFAULT_NAME = "v001_pohon_sono_only_v2"
DEFAULT_SUMMARY_PATH = ROOT / "data" / "metadata" / "progress5_v001_training_v2_summary.json"
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}


def resolve_path(value: str | Path) -> Path:
    path = Path(value)
    return path if path.is_absolute() else ROOT / path


def read_data_yaml_text(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def data_yaml_is_single_class_pohon_sono(path: Path) -> bool:
    text = read_data_yaml_text(path)
    normalized = "\n".join(line.rstrip() for line in text.splitlines())
    return "names:" in normalized and "0: pohon_sono" in normalized and "1:" not in normalized and "2:" not in normalized


def parse_label_file(path: Path) -> tuple[int, list[str]]:
    errors: list[str] = []
    text = path.read_text(encoding="utf-8").strip()
    if not text:
        return 0, ["EMPTY_LABEL_FILE"]
    rows = 0
    for line_number, line in enumerate(text.splitlines(), start=1):
        parts = line.strip().split()
        if len(parts) != 5:
            errors.append(f"{path.name}:{line_number}:EXPECTED_5_COLUMNS")
            continue
        if parts[0] != "0":
            errors.append(f"{path.name}:{line_number}:NON_SINGLE_CLASS_{parts[0]}")
        try:
            values = [float(value) for value in parts[1:]]
        except ValueError:
            errors.append(f"{path.name}:{line_number}:BAD_FLOAT")
            continue
        if not all(math.isfinite(value) and 0.0 <= value <= 1.0 for value in values):
            errors.append(f"{path.name}:{line_number}:COORDINATE_OUT_OF_RANGE")
        if values[2] <= 0.0 or values[3] <= 0.0:
            errors.append(f"{path.name}:{line_number}:NON_POSITIVE_BOX_SIZE")
        rows += 1
    return rows, errors


def validate_dataset(data_yaml: Path) -> dict[str, Any]:
    if not data_yaml.exists():
        return {"status": "DATA_YAML_MISSING", "data_yaml": str(data_yaml)}
    if not data_yaml_is_single_class_pohon_sono(data_yaml):
        return {"status": "DATASET_NOT_SINGLE_CLASS", "data_yaml": str(data_yaml)}

    dataset_dir = data_yaml.parent
    errors: list[str] = []
    counts: dict[str, int] = {}
    total_boxes = 0
    for split in ("train", "val"):
        image_dir = dataset_dir / "images" / split
        label_dir = dataset_dir / "labels" / split
        images = sorted(path for path in image_dir.glob("*") if path.suffix.lower() in IMAGE_EXTENSIONS)
        labels = sorted(label_dir.glob("*.txt")) if label_dir.exists() else []
        image_stems = {path.stem for path in images}
        label_stems = {path.stem for path in labels}
        missing = sorted(image_stems - label_stems)
        orphan = sorted(label_stems - image_stems)
        counts[f"{split}_images"] = len(images)
        counts[f"{split}_labels"] = len(labels)
        if missing:
            errors.append(f"{split}:MISSING_LABEL:{len(missing)}")
        if orphan:
            errors.append(f"{split}:ORPHAN_LABEL:{len(orphan)}")
        for label_path in labels:
            rows, label_errors = parse_label_file(label_path)
            total_boxes += rows
            errors.extend(f"{split}:{error}" for error in label_errors)

    if total_boxes <= 0:
        errors.append("NO_POHON_SONO_LABEL")
    if errors:
        return {
            "status": "DATASET_VALIDATION_FAILED",
            "data_yaml": str(data_yaml),
            "counts": counts,
            "total_pohon_sono_boxes": total_boxes,
            "errors": errors,
        }
    return {
        "status": "DATASET_V2_VALID_SINGLE_CLASS",
        "data_yaml": str(data_yaml),
        "counts": counts,
        "total_pohon_sono_boxes": total_boxes,
        "class_names": {"0": "pohon_sono"},
    }


def choose_device(requested: str) -> str:
    if requested != "auto":
        return requested
    try:
        import torch  # type: ignore

        return "0" if torch.cuda.is_available() else "cpu"
    except Exception:
        return "cpu"


def write_summary(summary: dict[str, Any], summary_path: Path) -> None:
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")


def train_v2(args: argparse.Namespace) -> dict[str, Any]:
    data_yaml = resolve_path(args.data)
    project = resolve_path(args.project)
    run_dir = project / args.name
    best_pt = run_dir / "weights" / "best.pt"
    last_pt = run_dir / "weights" / "last.pt"
    summary_path = resolve_path(args.summary)
    dataset_status = validate_dataset(data_yaml)

    command_preview = {
        "api": "from ultralytics import YOLO; YOLO(model).train(...)",
        "model": args.model,
        "data": str(data_yaml),
        "epochs": args.epochs,
        "imgsz": args.imgsz,
        "batch": args.batch,
        "device": choose_device(args.device),
        "project": str(project),
        "name": args.name,
        "seed": SAFE_SEED,
        "exist_ok": False,
    }

    if dataset_status["status"] != "DATASET_V2_VALID_SINGLE_CLASS":
        summary = {
            "status": "TRAINING_SKIPPED_DATASET_INVALID",
            "dataset_status": dataset_status,
            "command_preview": command_preview,
        }
        write_summary(summary, summary_path)
        return summary

    if not args.run:
        summary = {
            "status": "TRAINING_DRY_RUN_READY",
            "dataset_status": dataset_status,
            "command_preview": command_preview,
            "run_dir": str(run_dir),
            "best_pt": str(best_pt),
            "best_pt_exists": best_pt.exists(),
        }
        write_summary(summary, summary_path)
        return summary

    if run_dir.exists():
        summary = {
            "status": "TRAINING_REFUSED_RUN_DIR_EXISTS_NO_OVERWRITE",
            "run_dir": str(run_dir),
            "best_pt": str(best_pt),
            "dataset_status": dataset_status,
            "command_preview": command_preview,
        }
        write_summary(summary, summary_path)
        return summary

    from ultralytics import YOLO  # type: ignore

    started_at = datetime.now(timezone.utc)
    model = YOLO(args.model)
    model.train(
        data=str(data_yaml),
        epochs=args.epochs,
        imgsz=args.imgsz,
        batch=args.batch,
        device=command_preview["device"],
        project=str(project),
        name=args.name,
        seed=SAFE_SEED,
        exist_ok=False,
    )

    best_exists = best_pt.exists()
    best_mtime_ok = False
    if best_exists:
        best_mtime = datetime.fromtimestamp(best_pt.stat().st_mtime, tz=timezone.utc)
        best_mtime_ok = best_mtime >= started_at

    if not best_exists:
        status = "TRAINING_FINISHED_BUT_BEST_PT_MISSING"
    elif not best_mtime_ok:
        status = "TRAINING_FINISHED_BUT_BEST_PT_STALE"
    else:
        status = "TRAINING_FINISHED"

    summary = {
        "status": status,
        "started_at_utc": started_at.isoformat(),
        "finished_at_utc": datetime.now(timezone.utc).isoformat(),
        "dataset_status": dataset_status,
        "command_preview": command_preview,
        "run_dir": str(run_dir),
        "best_pt": str(best_pt),
        "last_pt": str(last_pt),
        "best_pt_exists": best_exists,
        "last_pt_exists": last_pt.exists(),
        "best_pt_mtime_after_start": best_mtime_ok,
    }
    write_summary(summary, summary_path)
    return summary


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Train YOLOv8n V001 pohon_sono single-class v2 candidate.")
    parser.add_argument("--data", default=str(DEFAULT_DATA))
    parser.add_argument("--model", default="yolov8n.pt")
    parser.add_argument("--epochs", type=int, default=50)
    parser.add_argument("--imgsz", type=int, default=640)
    parser.add_argument("--batch", type=int, default=4)
    parser.add_argument("--device", default="auto")
    parser.add_argument("--project", default=str(DEFAULT_PROJECT))
    parser.add_argument("--name", default=DEFAULT_NAME)
    parser.add_argument("--summary", default=str(DEFAULT_SUMMARY_PATH))
    parser.add_argument("--run", action="store_true")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    summary = train_v2(args)
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    print(summary["status"])
    if summary["status"] == "TRAINING_FINISHED":
        print("result: TRAINING_FINISHED")
        print(f"best_pt: {summary['best_pt']}")
        print(f"last_pt: {summary['last_pt'] if summary.get('last_pt_exists') else ''}")
        print(f"best_pt_exists: {summary['best_pt_exists']}")
    return 0 if summary["status"] in {"TRAINING_DRY_RUN_READY", "TRAINING_FINISHED"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
