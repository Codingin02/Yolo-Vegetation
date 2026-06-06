from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ulp_project.safe_inference import run_safe_predict, save_prediction_summary_json  # noqa: E402
from ulp_project.safe_inference import validate_single_class_pohon_sono_names  # noqa: E402

PROJECT_ROOT = Path(r"E:\Projects\ULP_Project")
DEFAULT_MODEL = PROJECT_ROOT / "runs" / "detect" / "v001_pohon_sono_only_v1" / "weights" / "best.pt"
DEFAULT_SOURCE = PROJECT_ROOT / "data" / "dataset_yolo" / "00_review_candidates" / "V001_pohon_sono" / "images_selected"
DEFAULT_SUMMARY = PROJECT_ROOT / "data" / "metadata" / "v001_pohon_sono_safe_predict_summary.json"
PREDICT_PROJECT = PROJECT_ROOT / "runs" / "predict"
LOW_CONF_VISUAL_FLOOR = 0.05
OVERDETECTION_LIMIT = 5


def is_conf_allowed_for_visual(conf: float, diagnostic_unsafe: bool) -> bool:
    return conf >= LOW_CONF_VISUAL_FLOOR or diagnostic_unsafe


def inspect_single_class_model(model_path: Path) -> dict:
    if not model_path.exists():
        return {"status": "MODEL_NOT_READY", "model_names": {}, "rejection_reason": "MODEL_FILE_NOT_FOUND", "model": None}
    try:
        from ultralytics import YOLO
    except Exception as exc:
        return {"status": "MODEL_NOT_READY", "model_names": {}, "rejection_reason": f"ULTRALYTICS_IMPORT_FAILED: {exc}", "model": None}
    try:
        model = YOLO(str(model_path))
    except Exception as exc:
        return {"status": "MODEL_NOT_READY", "model_names": {}, "rejection_reason": f"MODEL_LOAD_FAILED: {exc}", "model": None}
    names_check = validate_single_class_pohon_sono_names(getattr(model, "names", None))
    if names_check["status"] != "V001_SINGLE_CLASS_MODEL_OK":
        return {"status": names_check["status"], "model_names": names_check["names"], "rejection_reason": names_check["rejection_reason"], "model": None}
    return {"status": "MODEL_LOADED_SINGLE_CLASS_POHON_SONO", "model_names": names_check["names"], "rejection_reason": "", "model": model}


def overdetects(summary: dict, max_det: int) -> bool:
    counts = [int(value) for value in (summary.get("detections_per_image") or {}).values()]
    if not counts:
        return False
    average = int(summary.get("total_detections", 0)) / max(int(summary.get("image_count", 1)), 1)
    return max(counts) > OVERDETECTION_LIMIT or average > OVERDETECTION_LIMIT or (max(counts) >= max_det and max_det >= OVERDETECTION_LIMIT)


def main() -> int:
    parser = argparse.ArgumentParser(description="Safe V001 prediction wrapper with confidence and max_det guards.")
    parser.add_argument("--model", default=str(DEFAULT_MODEL))
    parser.add_argument("--source", default=str(DEFAULT_SOURCE))
    parser.add_argument("--conf", type=float, default=0.25)
    parser.add_argument("--iou", type=float, default=0.5)
    parser.add_argument("--imgsz", type=int, default=640)
    parser.add_argument("--max-det", type=int, default=5)
    parser.add_argument("--name", default="v001_pohon_sono_safe_predict")
    parser.add_argument("--save-visual", action="store_true")
    parser.add_argument("--save-txt", action="store_true")
    parser.add_argument("--diagnostic-sweep", action="store_true")
    parser.add_argument("--diagnostic-unsafe", action="store_true")
    args = parser.parse_args()

    if not is_conf_allowed_for_visual(args.conf, args.diagnostic_unsafe):
        summary = {
            "model_path": args.model,
            "model_status": "NOT_LOADED_LOW_CONF_REFUSED",
            "confidence": args.conf,
            "max_det": args.max_det,
            "total_detections": 0,
            "detections_per_image": {},
            "visual_output_path": "",
            "final_status": "REFUSED_LOW_CONF_OPERATOR_OUTPUT",
            "warnings": ["conf < 0.05 requires --diagnostic-unsafe and is not valid operator output."],
        }
        save_prediction_summary_json(summary, DEFAULT_SUMMARY)
        print("result: REFUSED_LOW_CONF_OPERATOR_OUTPUT")
        print("reason: conf < 0.05 perlu --diagnostic-unsafe dan tidak valid sebagai output operator.")
        return 2

    model_path = Path(args.model)
    inspected = inspect_single_class_model(model_path)
    if inspected["status"] != "MODEL_LOADED_SINGLE_CLASS_POHON_SONO":
        summary = {
            "model_path": args.model,
            "model_status": inspected["status"],
            "model_names": inspected["model_names"],
            "confidence": args.conf,
            "max_det": args.max_det,
            "total_detections": 0,
            "detections_per_image": {},
            "visual_output_path": "",
            "final_status": inspected["status"],
            "rejection_reason": inspected["rejection_reason"],
        }
        save_prediction_summary_json(summary, DEFAULT_SUMMARY)
        print(f"summary_json: {DEFAULT_SUMMARY}")
        print(f"status: {inspected['status']}")
        print(f"rejection_reason: {inspected['rejection_reason']}")
        print("visual_output: SKIPPED_BY_SAFE_GUARD")
        return 1

    visual_allowed = True
    summary = run_safe_predict(args.model, args.source, args.conf, args.iou, args.imgsz, args.max_det)
    summary["model_status"] = inspected["status"]
    summary["model_names"] = inspected["model_names"]
    summary["confidence"] = args.conf
    summary["visual_output_path"] = str(PREDICT_PROJECT / args.name)
    if args.conf < 0.10:
        summary.setdefault("warnings", []).append("LOW_OPERATOR_CONF_NOT_RECOMMENDED")
    if args.diagnostic_unsafe:
        summary.setdefault("warnings", []).append("UNSAFE_DIAGNOSTIC_ONLY")
    if summary["status"] in {"MODEL_UNSTABLE_TOO_MANY_BOXES", "MODEL_UNSTABLE_LOW_CONF"}:
        summary.setdefault("warnings", []).append("INVALID_VISUALIZATION")
        visual_allowed = False
    if overdetects(summary, args.max_det):
        summary.setdefault("warnings", []).append("OVERDETECTION_GUARD_TRIGGERED")
        summary["final_status"] = "VISUAL_SKIPPED_OVERDETECTION_GUARD"
        visual_allowed = False
    else:
        summary["final_status"] = summary["status"]
    save_prediction_summary_json(summary, DEFAULT_SUMMARY)
    print(f"summary_json: {DEFAULT_SUMMARY}")
    print(f"status: {summary['status']}")
    print(f"total_detections: {summary['total_detections']}")

    if (args.save_visual or args.save_txt) and visual_allowed and summary["status"] != "MODEL_NOT_READY":
        max_det_visual = min(args.max_det, 20)
        model = inspected["model"]
        model.predict(
            source=args.source,
            conf=args.conf,
            iou=args.iou,
            imgsz=args.imgsz,
            max_det=max_det_visual,
            save=args.save_visual,
            save_txt=args.save_txt,
            project=str(PREDICT_PROJECT),
            name=args.name,
            exist_ok=True,
            verbose=False,
        )
        print(f"visual_output: {PREDICT_PROJECT / args.name}")
    elif args.save_visual or args.save_txt:
        print("visual_output: SKIPPED_BY_SAFE_GUARD")
    return 0 if summary["final_status"] in {"V001_SMOKE_MODEL_CANDIDATE", "MODEL_WEAK_NO_DETECTION"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
