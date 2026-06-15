from __future__ import annotations

import argparse
import csv
from datetime import datetime
import json
from pathlib import Path
import shutil
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DATASET_ROOT = ROOT / "data" / "dataset_yolo"
METADATA_DIR = ROOT / "data" / "metadata"
MODEL_DIR = ROOT / "models" / "plan_c_system_c_detector"


def main() -> int:
    args = parse_args()
    dataset_dir = _resolve_dataset(args.dataset)
    if not dataset_dir:
        raise SystemExit("PLAN_C_SYSTEM_C_DATASET_NOT_FOUND")
    data_yaml = dataset_dir / "data.yaml"
    if not data_yaml.exists():
        raise SystemExit(f"PLAN_C_SYSTEM_C_DATA_YAML_NOT_FOUND: {data_yaml}")
    if not args.train:
        print(
            json.dumps(
                {
                    "status": "TRAINING_NOT_REQUESTED",
                    "dataset_path": str(dataset_dir),
                    "data_yaml": str(data_yaml),
                    "run_command": "python scripts/plan_c_train_system_c_detector.py --train",
                },
                indent=2,
                ensure_ascii=False,
            )
        )
        return 0

    try:
        result = _train_with_fallback(data_yaml, args)
    except Exception as exc:
        METADATA_DIR.mkdir(parents=True, exist_ok=True)
        error_path = METADATA_DIR / f"plan_c_training_error_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        error = {
            "status": "PLAN_C_SYSTEM_C_TRAINING_FAILED",
            "dataset_path": str(dataset_dir),
            "data_yaml": str(data_yaml),
            "error": f"{type(exc).__name__}: {exc}",
        }
        error_path.write_text(json.dumps(error, indent=2, ensure_ascii=False), encoding="utf-8")
        print(json.dumps({**error, "error_report_path": str(error_path)}, indent=2, ensure_ascii=False))
        return 1

    registry = _register_model(result, dataset_dir)
    print(json.dumps(registry, indent=2, ensure_ascii=False))
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train and register Plan C System C YOLOv8 detector.")
    parser.add_argument("--train", action="store_true", help="Run actual Ultralytics training.")
    parser.add_argument("--dataset", default="", help="Dataset folder containing data.yaml.")
    parser.add_argument("--epochs", type=int, default=100)
    parser.add_argument("--imgsz", type=int, default=640)
    parser.add_argument("--batch", default="auto")
    parser.add_argument("--device", default="")
    parser.add_argument("--patience", type=int, default=30)
    parser.add_argument("--workers", type=int, default=0)
    return parser.parse_args()


def _resolve_dataset(value: str) -> Path | None:
    if value:
        path = Path(value)
        path = path if path.is_absolute() else ROOT / path
        return path if path.exists() else None
    candidates = sorted(
        [
            path
            for path in DATASET_ROOT.glob("plan_c_system_c_detector_v2*")
            if path.is_dir() and (path / "data.yaml").exists()
        ],
        key=lambda item: item.stat().st_mtime,
    )
    return candidates[-1] if candidates else None


def _train_with_fallback(data_yaml: Path, args: argparse.Namespace) -> dict[str, Any]:
    first_device = args.device.strip() or _auto_device()
    first_batch = _normalize_batch(args.batch)
    try:
        return _train(data_yaml, args, device=first_device, batch=first_batch)
    except Exception:
        if first_device == "cpu":
            raise
        return _train(data_yaml, args, device="cpu", batch=2)


def _train(data_yaml: Path, args: argparse.Namespace, *, device: str, batch: int | float | str) -> dict[str, Any]:
    from ultralytics import YOLO  # type: ignore

    run_name = f"plan_c_system_c_detector_v2_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    model = YOLO("yolov8n.pt")
    result = model.train(
        data=str(data_yaml),
        epochs=int(args.epochs),
        imgsz=int(args.imgsz),
        batch=batch,
        device=device,
        patience=int(args.patience),
        workers=int(args.workers),
        project=str(ROOT / "runs" / "detect"),
        name=run_name,
        exist_ok=False,
        verbose=True,
    )
    save_dir = Path(getattr(result, "save_dir", ROOT / "runs" / "detect" / run_name))
    return {
        "status": "PLAN_C_SYSTEM_C_TRAINING_COMPLETE",
        "run_dir": str(save_dir),
        "weights_dir": str(save_dir / "weights"),
        "best_pt": str(save_dir / "weights" / "best.pt"),
        "last_pt": str(save_dir / "weights" / "last.pt"),
        "results_csv": str(save_dir / "results.csv"),
        "device": device,
        "batch": batch,
        "epochs": int(args.epochs),
        "imgsz": int(args.imgsz),
    }


def _auto_device() -> str:
    try:
        import torch  # type: ignore

        return "0" if torch.cuda.is_available() else "cpu"
    except Exception:
        return "cpu"


def _normalize_batch(value: str) -> int | float | str:
    cleaned = str(value).strip().lower()
    if cleaned in {"", "auto"}:
        return -1
    try:
        return int(cleaned)
    except ValueError:
        return cleaned


def _register_model(train_result: dict[str, Any], dataset_dir: Path) -> dict[str, Any]:
    best_pt = Path(train_result["best_pt"])
    last_pt = Path(train_result["last_pt"])
    if not best_pt.exists():
        raise FileNotFoundError(f"best.pt not found after training: {best_pt}")
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    shutil.copy2(best_pt, MODEL_DIR / "best.pt")
    if last_pt.exists():
        shutil.copy2(last_pt, MODEL_DIR / "last.pt")

    class_names = _read_class_names(dataset_dir / "data.yaml")
    metrics = _read_metrics(Path(train_result["results_csv"]))
    registry = {
        "status": "PLAN_C_SYSTEM_C_DETECTOR_READY",
        "model_type": "yolov8_object_detector",
        "runtime_detector": "YOLOv8",
        "training_dataset": str(dataset_dir),
        "class_names": {str(key): value for key, value in class_names.items()},
        "class_policy": "system_c_tree_conductor_structure",
        "trained_at": datetime.now().isoformat(timespec="seconds"),
        "best_pt": "models/plan_c_system_c_detector/best.pt",
        "last_pt": "models/plan_c_system_c_detector/last.pt" if (MODEL_DIR / "last.pt").exists() else "",
        "training_run": train_result.get("run_dir"),
        "metrics": metrics,
        "notes": [
            "Model lokal YOLOv8 dilatih dari dataset label lapangan/review.",
            "Gemini, Groq Console, dan OpenRouter hanya dipakai untuk consensus validation, bukan training lokal.",
            "Registry ini tidak mengklaim akurasi final PLN.",
        ],
    }
    (MODEL_DIR / "registry.json").write_text(json.dumps(registry, indent=2, ensure_ascii=False), encoding="utf-8")
    return registry


def _read_class_names(path: Path) -> dict[int, str]:
    names: dict[int, str] = {}
    in_names = False
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if line.startswith("names:"):
            in_names = True
            continue
        if in_names:
            if not raw_line.startswith(" ") and line:
                break
            if ":" not in line:
                continue
            key, value = line.split(":", 1)
            try:
                names[int(key.strip())] = value.strip().strip("'\"")
            except ValueError:
                continue
    return names


def _read_metrics(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"status": "RESULTS_CSV_NOT_FOUND"}
    with path.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    if not rows:
        return {"status": "RESULTS_CSV_EMPTY"}
    last = rows[-1]
    metrics: dict[str, Any] = {"status": "RESULTS_CSV_LOADED"}
    aliases = {
        "precision": ["metrics/precision(B)", "precision"],
        "recall": ["metrics/recall(B)", "recall"],
        "mAP50": ["metrics/mAP50(B)", "mAP50"],
        "mAP50-95": ["metrics/mAP50-95(B)", "mAP50-95"],
    }
    for out_key, candidates in aliases.items():
        for candidate in candidates:
            if candidate in last:
                try:
                    metrics[out_key] = float(last[candidate])
                except ValueError:
                    metrics[out_key] = last[candidate]
                break
    metrics["source"] = str(path)
    return metrics


if __name__ == "__main__":
    raise SystemExit(main())
