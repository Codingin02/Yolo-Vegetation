from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ulp_project.safe_inference import validate_single_class_pohon_sono_names  # noqa: E402
from ulp_project.yolo_label_audit import IMAGE_EXTENSIONS  # noqa: E402

PROJECT_ROOT = Path(r"E:\Projects\ULP_Project")
DEFAULT_MODEL = PROJECT_ROOT / "runs" / "detect" / "v001_pohon_sono_only_v1" / "weights" / "best.pt"
DEFAULT_SOURCE = PROJECT_ROOT / "data" / "dataset_yolo" / "00_review_candidates" / "V001_pohon_sono" / "images_selected"


def verify_artifact(model_path: Path, source: Path = DEFAULT_SOURCE) -> dict:
    result = {
        "status": "V001_TRAINING_ARTIFACT_READY",
        "model_path": str(model_path),
        "file_exists": model_path.exists(),
        "file_size": 0,
        "modified_time": None,
        "model_loadable": False,
        "model_names": {},
        "sample_inference_status": "NOT_RUN",
        "sample_image_count": 0,
        "reason": "",
    }
    if not model_path.exists():
        result.update({"status": "MODEL_NOT_READY", "reason": "MODEL_FILE_NOT_FOUND"})
        return result
    stat = model_path.stat()
    result["file_size"] = stat.st_size
    result["modified_time"] = stat.st_mtime
    if stat.st_size <= 0:
        result.update({"status": "MODEL_FILE_INVALID_SIZE", "reason": "FILE_SIZE_ZERO"})
        return result
    if stat.st_mtime <= 0:
        result.update({"status": "MODEL_FILE_INVALID_MTIME", "reason": "MODIFIED_TIME_INVALID"})
        return result
    try:
        from ultralytics import YOLO
    except Exception as exc:
        result.update({"status": "ULTRALYTICS_IMPORT_FAILED", "reason": str(exc)})
        return result
    try:
        model = YOLO(str(model_path))
        result["model_loadable"] = True
    except Exception as exc:
        result.update({"status": "MODEL_LOAD_FAILED", "reason": str(exc)})
        return result
    names_check = validate_single_class_pohon_sono_names(getattr(model, "names", None))
    result["model_names"] = names_check["names"]
    if names_check["status"] != "V001_SINGLE_CLASS_MODEL_OK":
        result.update({"status": names_check["status"], "reason": names_check["rejection_reason"]})
        return result
    images = sorted(path for path in source.iterdir() if path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS)[:3] if source.exists() else []
    result["sample_image_count"] = len(images)
    if not images:
        result.update({"status": "SAMPLE_IMAGES_NOT_FOUND", "reason": str(source)})
        return result
    try:
        for image in images:
            model.predict(source=str(image), conf=0.25, iou=0.5, imgsz=640, max_det=5, save=False, save_txt=False, verbose=False)
        result["sample_inference_status"] = "PREDICT_SMOKE_OK"
    except Exception as exc:
        result.update({"status": "PREDICT_SMOKE_FAILED", "reason": str(exc)})
        return result
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify V001 single-class training artifact.")
    parser.add_argument("--model", default=str(DEFAULT_MODEL))
    parser.add_argument("--source", default=str(DEFAULT_SOURCE))
    args = parser.parse_args()
    result = verify_artifact(Path(args.model), Path(args.source))
    print(json.dumps(result, indent=2, ensure_ascii=False))
    print(result["status"])
    return 0 if result["status"] == "V001_TRAINING_ARTIFACT_READY" else 1


if __name__ == "__main__":
    raise SystemExit(main())
