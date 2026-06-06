from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ulp_project.safe_inference import run_safe_predict  # noqa: E402
from ulp_project.safe_inference import validate_single_class_pohon_sono_names  # noqa: E402

PROJECT_ROOT = Path(r"E:\Projects\ULP_Project")
DEFAULT_MODEL = PROJECT_ROOT / "runs" / "detect" / "v001_pohon_sono_only_v1" / "weights" / "best.pt"
DEFAULT_SOURCE = PROJECT_ROOT / "data" / "dataset_yolo" / "00_review_candidates" / "V001_pohon_sono" / "images_selected"
CSV_PATH = PROJECT_ROOT / "data" / "metadata" / "v001_threshold_diagnostic.csv"
JSON_PATH = PROJECT_ROOT / "data" / "metadata" / "v001_threshold_diagnostic.json"
THRESHOLDS = [0.50, 0.25, 0.10, 0.05, 0.01, 0.005, 0.001]
OPERATOR_THRESHOLDS = {0.50, 0.25, 0.10, 0.05}


def inspect_model(model_path: Path) -> dict:
    if not model_path.exists():
        return {
            "status": "MODEL_NOT_READY",
            "model_path": str(model_path),
            "model_names": {},
            "rejection_reason": "MODEL_FILE_NOT_FOUND",
            "model": None,
        }
    try:
        from ultralytics import YOLO
    except Exception as exc:
        return {
            "status": "MODEL_NOT_READY",
            "model_path": str(model_path),
            "model_names": {},
            "rejection_reason": f"ULTRALYTICS_IMPORT_FAILED: {exc}",
            "model": None,
        }
    try:
        model = YOLO(str(model_path))
    except Exception as exc:
        return {
            "status": "MODEL_NOT_READY",
            "model_path": str(model_path),
            "model_names": {},
            "rejection_reason": f"MODEL_LOAD_FAILED: {exc}",
            "model": None,
        }
    names_check = validate_single_class_pohon_sono_names(getattr(model, "names", None))
    if names_check["status"] != "V001_SINGLE_CLASS_MODEL_OK":
        return {
            "status": names_check["status"],
            "model_path": str(model_path),
            "model_names": names_check["names"],
            "rejection_reason": names_check["rejection_reason"],
            "model": None,
        }
    return {
        "status": "MODEL_LOADED_SINGLE_CLASS_POHON_SONO",
        "model_path": str(model_path),
        "model_names": names_check["names"],
        "rejection_reason": "",
        "model": model,
    }


def diagnostic_records(model: Path, source: Path, iou: float, imgsz: int, max_det: int) -> list[dict]:
    records = []
    for conf in THRESHOLDS:
        summary = run_safe_predict(model, source, conf=conf, iou=iou, imgsz=imgsz, max_det=max_det)
        counts = list((summary.get("detections_per_image") or {}).values())
        total = int(summary.get("total_detections", 0))
        image_count = max(int(summary.get("image_count", 0)), 1)
        stats = summary.get("confidence_stats", {}) or {}
        record = {
            "model_path": str(model),
            "conf": conf,
            "total_detections": total,
            "average_detections_per_image": total / image_count,
            "max_detections_per_image": max(counts) if counts else 0,
            "class_counts": summary.get("class_counts", {}),
            "min_confidence": stats.get("min"),
            "median_confidence": stats.get("median"),
            "max_confidence": stats.get("max"),
            "runtime_status": summary.get("status"),
            "diagnostic_only": conf < 0.05,
            "visual_saved": False,
        }
        records.append(record)
    return records


def classify_threshold_diagnostic(records: list[dict]) -> dict:
    by_conf = {float(record["conf"]): record for record in records}
    conf_025 = by_conf.get(0.25, {})
    conf_010 = by_conf.get(0.10, {})
    operator_records = [record for record in records if float(record["conf"]) in OPERATOR_THRESHOLDS]
    low_records = [record for record in records if float(record["conf"]) < 0.05]
    if int(conf_025.get("total_detections", 0)) == 0 and int(conf_010.get("total_detections", 0)) == 0:
        if any(int(record["total_detections"]) > 0 for record in low_records):
            return {"final_status": "MODEL_UNSTABLE_LOW_CONF", "rejection_reason": "Detections only appear below operator-safe thresholds."}
        return {"final_status": "MODEL_WEAK_NO_DETECTION", "rejection_reason": "No detections at conf 0.25 and 0.10."}
    if any(float(record["average_detections_per_image"]) > 5 or int(record["max_detections_per_image"]) > 5 for record in operator_records):
        return {"final_status": "MODEL_UNSTABLE_OVERDETECTION", "rejection_reason": "Operator thresholds produce too many detections."}
    stable_records = [record for record in records if float(record["conf"]) >= 0.10]
    if any(int(record["total_detections"]) > 0 for record in stable_records) and all(
        float(record["average_detections_per_image"]) <= 5 and int(record["max_detections_per_image"]) <= 5
        for record in stable_records
    ):
        return {"final_status": "MODEL_CANDIDATE_STABLE", "rejection_reason": ""}
    return {"final_status": "MODEL_UNSTABLE_OVERDETECTION", "rejection_reason": "Threshold behavior is not stable enough for operator visual output."}


def write_outputs(payload: dict) -> None:
    records = payload.get("thresholds", [])
    CSV_PATH.parent.mkdir(parents=True, exist_ok=True)
    with CSV_PATH.open("w", newline="", encoding="utf-8") as handle:
        fieldnames = [
            "model_path",
            "conf",
            "total_detections",
            "average_detections_per_image",
            "max_detections_per_image",
            "class_counts",
            "min_confidence",
            "median_confidence",
            "max_confidence",
            "runtime_status",
            "diagnostic_only",
            "visual_saved",
        ]
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for record in records:
            row = dict(record)
            row["class_counts"] = json.dumps(row["class_counts"], ensure_ascii=False)
            writer.writerow(row)
    JSON_PATH.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Threshold sweep diagnostic for V001 YOLO models.")
    parser.add_argument("--model", default=str(DEFAULT_MODEL))
    parser.add_argument("--source", default=str(DEFAULT_SOURCE))
    parser.add_argument("--iou", type=float, default=0.5)
    parser.add_argument("--imgsz", type=int, default=640)
    parser.add_argument("--max-det", type=int, default=300)
    args = parser.parse_args()
    model_path = Path(args.model)
    inspected = inspect_model(model_path)
    if inspected["status"] != "MODEL_LOADED_SINGLE_CLASS_POHON_SONO":
        payload = {
            "model_path": str(model_path),
            "model_status": inspected["status"],
            "model_names": inspected["model_names"],
            "thresholds": [],
            "final_status": inspected["status"],
            "rejection_reason": inspected["rejection_reason"],
        }
        write_outputs(payload)
        print(f"json: {JSON_PATH}")
        print(f"status: {inspected['status']}")
        print(f"rejection_reason: {inspected['rejection_reason']}")
        return 1
    records = diagnostic_records(model_path, Path(args.source), args.iou, args.imgsz, args.max_det)
    classification = classify_threshold_diagnostic(records)
    payload = {
        "model_path": str(model_path),
        "model_status": inspected["status"],
        "model_names": inspected["model_names"],
        "source": str(args.source),
        "thresholds": records,
        **classification,
    }
    write_outputs(payload)
    print(f"csv: {CSV_PATH}")
    print(f"json: {JSON_PATH}")
    for record in records:
        print(
            f"conf={record['conf']}: total={record['total_detections']} "
            f"avg={record['average_detections_per_image']:.2f} "
            f"max={record['max_detections_per_image']} status={record['runtime_status']}"
        )
    print(f"final_status: {classification['final_status']}")
    print("note: conf < 0.05 diagnostic-only; jangan dipakai sebagai prediksi operator atau bukti model valid.")
    return 0 if classification["final_status"] == "MODEL_CANDIDATE_STABLE" else 1


if __name__ == "__main__":
    raise SystemExit(main())
