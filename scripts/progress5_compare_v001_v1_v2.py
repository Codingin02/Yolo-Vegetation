from __future__ import annotations

import argparse
import json
import statistics
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_V1_MODEL = ROOT / "runs" / "detect" / "v001_pohon_sono_only_v1" / "weights" / "best.pt"
DEFAULT_V2_MODEL = ROOT / "runs" / "detect" / "v001_pohon_sono_only_v2" / "weights" / "best.pt"
DEFAULT_SOURCE = ROOT / "data" / "dataset_yolo" / "00_review_candidates" / "V001_pohon_sono_v2" / "images_selected"
DEFAULT_OUTPUT_DIR = ROOT / "results" / "progress5_v001_compare_v1_v2"
DEFAULT_SUMMARY_PATH = ROOT / "data" / "metadata" / "progress5_v001_compare_v1_v2_summary.json"


def resolve_path(value: str | Path) -> Path:
    path = Path(value)
    return path if path.is_absolute() else ROOT / path


def validate_single_class_names(names: Any) -> bool:
    if isinstance(names, dict):
        return len(names) == 1 and str(names.get(0, names.get("0", ""))) == "pohon_sono"
    if isinstance(names, list):
        return names == ["pohon_sono"]
    return False


def summarize_prediction_results(results: list[Any], max_det_guard: int = 5) -> dict[str, Any]:
    per_image: list[int] = []
    confidences: list[float] = []
    areas: list[float] = []
    for result in results:
        boxes = getattr(result, "boxes", None)
        count = 0 if boxes is None else len(boxes)
        per_image.append(count)
        if boxes is None or count == 0:
            continue
        conf_values = getattr(boxes, "conf", [])
        for value in conf_values:
            confidences.append(float(value))
        xywhn = getattr(boxes, "xywhn", None)
        if xywhn is not None:
            for item in xywhn:
                width = float(item[2])
                height = float(item[3])
                areas.append(width * height)

    total = sum(per_image)
    avg = total / len(per_image) if per_image else 0.0
    max_per_image = max(per_image) if per_image else 0
    confidence_stats = {
        "min": min(confidences) if confidences else None,
        "mean": statistics.fmean(confidences) if confidences else None,
        "max": max(confidences) if confidences else None,
    }
    loose_box_note = "POSSIBLE_LOOSE_BOX_REVIEW_REQUIRED" if areas and statistics.fmean(areas) > 0.6 else "MANUAL_VISUAL_REVIEW_REQUIRED"
    return {
        "image_count": len(per_image),
        "total_detections": total,
        "avg_detections_per_image": avg,
        "max_detections_per_image": max_per_image,
        "per_image_counts": per_image,
        "confidence": confidence_stats,
        "over_detection_candidate": max_per_image > max_det_guard or avg > max_det_guard,
        "box_tightness_note": loose_box_note,
    }


def write_summary(summary: dict[str, Any], summary_path: Path) -> None:
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")


def compare_models(args: argparse.Namespace) -> dict[str, Any]:
    v1_model_path = resolve_path(args.v1_model)
    v2_model_path = resolve_path(args.v2_model)
    source = resolve_path(args.source)
    output_dir = resolve_path(args.output_dir)
    summary_path = resolve_path(args.summary)

    if args.conf < 0.05:
        summary = {
            "status": "REFUSED_LOW_CONF_OPERATOR_COMPARISON",
            "conf": args.conf,
            "minimum_operator_conf": 0.05,
        }
        write_summary(summary, summary_path)
        return summary
    if not v1_model_path.exists():
        summary = {"status": "BASELINE_V1_MODEL_MISSING", "v1_model": str(v1_model_path)}
        write_summary(summary, summary_path)
        return summary
    if not v2_model_path.exists():
        summary = {
            "status": "SKIPPED_WAITING_V2",
            "v1_model": str(v1_model_path),
            "v2_model": str(v2_model_path),
            "source": str(source),
            "conf": args.conf,
        }
        write_summary(summary, summary_path)
        return summary
    if not source.exists():
        summary = {"status": "TEST_SOURCE_MISSING", "source": str(source)}
        write_summary(summary, summary_path)
        return summary

    from ultralytics import YOLO  # type: ignore

    output_dir.mkdir(parents=True, exist_ok=True)
    summaries: dict[str, Any] = {}
    for tag, model_path in (("v1", v1_model_path), ("v2", v2_model_path)):
        model = YOLO(str(model_path))
        if not validate_single_class_names(getattr(model, "names", None)):
            summary = {
                "status": f"{tag.upper()}_MODEL_NOT_SINGLE_CLASS_POHON_SONO",
                "model": str(model_path),
                "names": getattr(model, "names", None),
            }
            write_summary(summary, summary_path)
            return summary
        results = model.predict(
            source=str(source),
            conf=args.conf,
            iou=args.iou,
            imgsz=args.imgsz,
            max_det=args.max_det,
            save=True,
            project=str(output_dir),
            name=tag,
            exist_ok=True,
            verbose=False,
        )
        summaries[tag] = summarize_prediction_results(list(results), max_det_guard=args.max_det)

    status = "PROGRESS5_V1_V2_COMPARISON_COMPLETE"
    if summaries["v2"]["over_detection_candidate"]:
        status = "PROGRESS5_V2_COMPARISON_OVERDETECTION_REVIEW_REQUIRED"
    summary = {
        "status": status,
        "v1_model": str(v1_model_path),
        "v2_model": str(v2_model_path),
        "source": str(source),
        "visual_output_dir": str(output_dir),
        "conf": args.conf,
        "iou": args.iou,
        "imgsz": args.imgsz,
        "max_det": args.max_det,
        "v1": summaries["v1"],
        "v2": summaries["v2"],
        "operator_policy": "CONF_0_25_OPERATOR_COMPARISON_NO_ULTRA_LOW_CONF",
    }
    write_summary(summary, summary_path)
    return summary


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Compare V001 pohon_sono v1 and v2 candidate detections.")
    parser.add_argument("--v1-model", default=str(DEFAULT_V1_MODEL))
    parser.add_argument("--v2-model", default=str(DEFAULT_V2_MODEL))
    parser.add_argument("--source", default=str(DEFAULT_SOURCE))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--summary", default=str(DEFAULT_SUMMARY_PATH))
    parser.add_argument("--conf", type=float, default=0.25)
    parser.add_argument("--iou", type=float, default=0.5)
    parser.add_argument("--imgsz", type=int, default=640)
    parser.add_argument("--max-det", type=int, default=5)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    summary = compare_models(args)
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    print(summary["status"])
    return 0 if summary["status"] in {"SKIPPED_WAITING_V2", "PROGRESS5_V1_V2_COMPARISON_COMPLETE"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
