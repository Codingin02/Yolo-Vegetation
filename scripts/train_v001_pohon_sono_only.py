from __future__ import annotations

import argparse
import time
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ulp_project.yolo_label_audit import IMAGE_EXTENSIONS, read_yolo_label_file  # noqa: E402

PROJECT_ROOT = Path(r"E:\Projects\ULP_Project")
DEFAULT_DATA = PROJECT_ROOT / "data" / "dataset_yolo" / "v001_pohon_sono_only_v1" / "data.yaml"
DEFAULT_PROJECT = PROJECT_ROOT / "runs" / "detect"
RAW_SEED = 23050874166
MAX_NUMPY_SEED = 2**32 - 1
EXPECTED_TRAIN_IMAGES = 15
EXPECTED_VAL_IMAGES = 4
EXPECTED_POHON_SONO_BOXES = 19


def normalize_seed(raw_seed: int = RAW_SEED) -> int:
    return raw_seed % MAX_NUMPY_SEED


def read_single_class_names(data_yaml: Path) -> dict[int, str]:
    names_started = False
    names: dict[int, str] = {}
    for line in data_yaml.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped == "names:":
            names_started = True
            continue
        if names_started:
            if not stripped:
                continue
            if ":" not in stripped:
                break
            key, value = stripped.split(":", 1)
            key = key.strip()
            if not key.isdigit():
                break
            names[int(key)] = value.strip().strip("'\"")
    return names


def check_dataset(data_yaml: Path) -> dict:
    if not data_yaml.exists():
        return {"status": "DATA_YAML_NOT_FOUND", "ready": False, "reason": str(data_yaml)}
    dataset_root = data_yaml.parent
    result = {
        "status": "READY",
        "ready": True,
        "data_yaml": str(data_yaml),
        "data_yaml_names": read_single_class_names(data_yaml),
        "train_images": 0,
        "train_labels": 0,
        "val_images": 0,
        "val_labels": 0,
        "pohon_sono_boxes": 0,
        "bad_labels": [],
        "empty_labels": [],
        "missing_labels": [],
        "orphan_labels": [],
        "non_zero_class_rows": [],
    }
    for split in ("train", "val"):
        image_dir = dataset_root / "images" / split
        label_dir = dataset_root / "labels" / split
        images = sorted(path for path in image_dir.glob("*") if path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS) if image_dir.exists() else []
        labels = sorted(path for path in label_dir.glob("*.txt") if path.is_file()) if label_dir.exists() else []
        result[f"{split}_images"] = len(images)
        result[f"{split}_labels"] = len(labels)
        image_stems = {path.stem for path in images}
        label_stems = {path.stem for path in labels}
        result["missing_labels"].extend([f"{split}/{stem}.txt" for stem in sorted(image_stems - label_stems)])
        result["orphan_labels"].extend([f"{split}/{stem}.txt" for stem in sorted(label_stems - image_stems)])
        for label in labels:
            parsed = read_yolo_label_file(label)
            if parsed["errors"]:
                result["bad_labels"].append(str(label))
            if parsed["status"] == "EMPTY_LABEL":
                result["empty_labels"].append(str(label))
            for box in parsed["boxes"]:
                if int(box["class_id"]) == 0:
                    result["pohon_sono_boxes"] += 1
                else:
                    result["non_zero_class_rows"].append({"label": str(label), "line": box["line"], "class_id": box["class_id"]})
    if result["data_yaml_names"] != {0: "pohon_sono"}:
        result.update({"status": "DATA_YAML_NOT_SINGLE_CLASS_POHON_SONO", "ready": False})
    elif result["train_images"] == 0 or result["val_images"] == 0:
        result.update({"status": "TRAIN_VAL_SPLIT_NOT_READY", "ready": False})
    elif result["train_images"] != EXPECTED_TRAIN_IMAGES or result["val_images"] != EXPECTED_VAL_IMAGES:
        result.update({"status": "UNEXPECTED_V001_SPLIT_COUNTS", "ready": False})
    elif result["missing_labels"] or result["orphan_labels"]:
        result.update({"status": "IMAGE_LABEL_MISMATCH", "ready": False})
    elif result["bad_labels"] or result["empty_labels"]:
        result.update({"status": "BAD_OR_EMPTY_LABEL_ROWS", "ready": False})
    elif result["non_zero_class_rows"]:
        result.update({"status": "DATASET_NOT_SINGLE_CLASS", "ready": False})
    elif result["pohon_sono_boxes"] != EXPECTED_POHON_SONO_BOXES:
        result.update({"status": "UNEXPECTED_POHON_SONO_BOX_COUNT", "ready": False})
    elif result["pohon_sono_boxes"] <= 0:
        result.update({"status": "NO_POHON_SONO_LABEL", "ready": False})
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Safe V001 pohon_sono-only YOLO training launcher. Default is dry-run.")
    parser.add_argument("--data", default=str(DEFAULT_DATA))
    parser.add_argument("--model", default="yolov8n.pt")
    parser.add_argument("--epochs", type=int, default=30)
    parser.add_argument("--imgsz", type=int, default=640)
    parser.add_argument("--batch", type=int, default=4)
    parser.add_argument("--device", default="0")
    parser.add_argument("--project", default=str(DEFAULT_PROJECT))
    parser.add_argument("--name", default="v001_pohon_sono_only_v1")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--run", action="store_true")
    args = parser.parse_args()

    data_yaml = Path(args.data)
    project = Path(args.project)
    safe_seed = normalize_seed(RAW_SEED)
    check = check_dataset(data_yaml)
    command_preview = (
        f"YOLO('{args.model}').train(data=r'{data_yaml}', epochs={args.epochs}, imgsz={args.imgsz}, "
        f"batch={args.batch}, device='{args.device}', project=r'{project}', name='{args.name}', seed={safe_seed}, exist_ok=True)"
    )
    print(f"raw_seed: {RAW_SEED}")
    print(f"safe_seed: {safe_seed}")
    print(f"dataset_status: {check['status']}")
    print(f"train_images: {check.get('train_images', 0)}")
    print(f"val_images: {check.get('val_images', 0)}")
    print(f"pohon_sono_boxes: {check.get('pohon_sono_boxes', 0)}")
    print(f"data_yaml: {data_yaml}")
    print(f"data_yaml_names: {check.get('data_yaml_names', {})}")
    print("command_preview:")
    print(command_preview)
    if not check["ready"]:
        print("result: TRAINING_REFUSED_DATASET_NOT_READY")
        return 1
    if args.dry_run or not args.run:
        print("result: DRY_RUN_READY")
        print("note: training aktual hanya berjalan jika --run diberikan.")
        return 0
    try:
        from ultralytics import YOLO
    except Exception as exc:
        print("result: ULTRALYTICS_IMPORT_FAILED")
        print(f"error: {exc}")
        return 1
    started_at = time.time()
    print("result: TRAINING_STARTED")
    print(f"training_started_unix: {started_at}")
    model = YOLO(args.model)
    model.train(
        data=str(data_yaml),
        epochs=args.epochs,
        imgsz=args.imgsz,
        batch=args.batch,
        device=args.device,
        project=str(project),
        name=args.name,
        seed=safe_seed,
        exist_ok=True,
    )
    best_pt = project / args.name / "weights" / "best.pt"
    last_pt = project / args.name / "weights" / "last.pt"
    if not best_pt.exists():
        print("result: TRAINING_FINISHED_BUT_BEST_PT_MISSING")
        print(f"best_pt: {best_pt}")
        print("best_pt_exists: False")
        return 1
    best_mtime = best_pt.stat().st_mtime
    if best_mtime <= started_at:
        print("result: TRAINING_FINISHED_BUT_BEST_PT_STALE")
        print(f"best_pt: {best_pt}")
        print(f"best_pt_modified_unix: {best_mtime}")
        print(f"training_started_unix: {started_at}")
        return 1
    print("result: TRAINING_FINISHED")
    print(f"best_pt: {best_pt}")
    print(f"last_pt: {last_pt if last_pt.exists() else ''}")
    print("best_pt_exists: True")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
