from __future__ import annotations

import json
import os
import sys
import time
import traceback
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


VERSION = "progress6_17_core_vision_pipeline_audit"
ROOT = Path("E:/Projects/ULP_Project").resolve()
REPORTS = ROOT / "reports"
TMP_DIR = REPORTS / "progress6_17_tmp"
REPORT_PATH = REPORTS / "progress6_17_core_vision_audit.json"

MODEL_CANDIDATES = [
    ROOT / "runs" / "detect" / "v001_pohon_sono_only_v2" / "weights" / "best.pt",
    ROOT / "runs" / "detect" / "v001_pohon_sono_only_v1" / "weights" / "best.pt",
]

FORBIDDEN_WRITE_ROOTS = [
    ROOT / "data",
    ROOT / "dataset",
    ROOT / "datasets",
    ROOT / "labels",
    ROOT / "runs",
    ROOT / "weights",
]


def now_iso() -> str:
    import datetime as _dt
    return _dt.datetime.now().isoformat(timespec="seconds")


def safe_write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def rel(p: Path) -> str:
    try:
        return str(p.resolve().relative_to(ROOT)).replace("\\", "/")
    except Exception:
        return str(p)


def ensure_report_only_path(path: Path) -> None:
    resolved = path.resolve()
    for forbidden in FORBIDDEN_WRITE_ROOTS:
        try:
            resolved.relative_to(forbidden.resolve())
            raise RuntimeError(f"FORBIDDEN_WRITE_PATH: {resolved}")
        except ValueError:
            continue


def find_model() -> Optional[Path]:
    for p in MODEL_CANDIDATES:
        if p.exists():
            return p
    return None


def import_stack() -> Dict[str, Any]:
    out: Dict[str, Any] = {
        "python": sys.version,
        "imports": {},
    }

    try:
        import torch
        out["imports"]["torch"] = {
            "ok": True,
            "version": getattr(torch, "__version__", None),
            "cuda_available": bool(torch.cuda.is_available()),
            "cuda_device_count": int(torch.cuda.device_count()) if torch.cuda.is_available() else 0,
            "cuda_name": torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,
        }
    except Exception as e:
        out["imports"]["torch"] = {"ok": False, "error": repr(e)}

    try:
        import cv2
        out["imports"]["cv2"] = {
            "ok": True,
            "version": getattr(cv2, "__version__", None),
        }
    except Exception as e:
        out["imports"]["cv2"] = {"ok": False, "error": repr(e)}

    try:
        import ultralytics
        from ultralytics import YOLO
        out["imports"]["ultralytics"] = {
            "ok": True,
            "version": getattr(ultralytics, "__version__", None),
            "yolo_class": str(YOLO),
        }
    except Exception as e:
        out["imports"]["ultralytics"] = {"ok": False, "error": repr(e)}

    try:
        import numpy as np
        out["imports"]["numpy"] = {
            "ok": True,
            "version": getattr(np, "__version__", None),
        }
    except Exception as e:
        out["imports"]["numpy"] = {"ok": False, "error": repr(e)}

    return out


def create_test_image() -> Path:
    ensure_report_only_path(TMP_DIR / "synthetic_tree_like_test.jpg")
    TMP_DIR.mkdir(parents=True, exist_ok=True)

    import cv2
    import numpy as np

    img = np.zeros((720, 960, 3), dtype=np.uint8)
    img[:] = (225, 225, 225)

    # Synthetic non-field image, only to verify pipeline execution.
    cv2.rectangle(img, (0, 500), (960, 720), (180, 180, 180), -1)
    cv2.rectangle(img, (430, 260), (520, 540), (80, 90, 70), -1)
    cv2.circle(img, (475, 230), 150, (35, 120, 45), -1)
    cv2.circle(img, (390, 270), 115, (40, 135, 55), -1)
    cv2.circle(img, (560, 285), 115, (40, 130, 50), -1)
    cv2.putText(
        img,
        "SYNTHETIC_PIPELINE_TEST_NOT_FIELD_EVIDENCE",
        (40, 690),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (30, 30, 30),
        2,
        cv2.LINE_AA,
    )

    out = TMP_DIR / "synthetic_tree_like_test.jpg"
    cv2.imwrite(str(out), img)
    return out


def create_test_video(image_path: Path) -> Path:
    ensure_report_only_path(TMP_DIR / "synthetic_tracking_test.mp4")
    TMP_DIR.mkdir(parents=True, exist_ok=True)

    import cv2

    img = cv2.imread(str(image_path))
    if img is None:
        raise RuntimeError(f"FAILED_READ_TEST_IMAGE: {image_path}")

    h, w = img.shape[:2]
    out_path = TMP_DIR / "synthetic_tracking_test.mp4"

    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    vw = cv2.VideoWriter(str(out_path), fourcc, 5.0, (w, h))

    if not vw.isOpened():
        raise RuntimeError("VIDEO_WRITER_NOT_OPENED")

    for i in range(8):
        frame = img.copy()
        cv2.putText(
            frame,
            f"frame={i}",
            (40, 50),
            cv2.FONT_HERSHEY_SIMPLEX,
            1.0,
            (0, 0, 0),
            2,
            cv2.LINE_AA,
        )
        vw.write(frame)

    vw.release()
    return out_path


def yolo_predict_test(model_path: Path, image_path: Path) -> Dict[str, Any]:
    from ultralytics import YOLO

    t0 = time.time()
    model = YOLO(str(model_path))
    names = getattr(model, "names", None)

    results = model.predict(
        source=str(image_path),
        conf=0.25,
        imgsz=640,
        verbose=False,
    )

    elapsed = time.time() - t0

    det_count = 0
    boxes_payload: List[Dict[str, Any]] = []

    if results:
        r0 = results[0]
        boxes = getattr(r0, "boxes", None)
        if boxes is not None:
            try:
                det_count = int(len(boxes))
            except Exception:
                det_count = 0

            for b in boxes[:10]:
                try:
                    xyxy = b.xyxy[0].detach().cpu().numpy().tolist()
                    conf = float(b.conf[0].detach().cpu().item()) if b.conf is not None else None
                    cls = int(b.cls[0].detach().cpu().item()) if b.cls is not None else None
                    boxes_payload.append({
                        "xyxy": [round(float(x), 3) for x in xyxy],
                        "confidence": round(conf, 6) if conf is not None else None,
                        "class_id": cls,
                        "class_name": str(names.get(cls, cls)) if isinstance(names, dict) and cls is not None else str(cls),
                    })
                except Exception:
                    continue

    return {
        "status": "PASS",
        "model_path": rel(model_path),
        "model_names": names,
        "elapsed_sec": round(elapsed, 4),
        "detection_count": det_count,
        "detections_preview": boxes_payload,
        "note": "Detection count pada synthetic image bukan evidence PLN; hanya audit pipeline.",
    }


def bytetrack_test(model_path: Path, video_path: Path) -> Dict[str, Any]:
    from ultralytics import YOLO

    model = YOLO(str(model_path))

    t0 = time.time()
    try:
        results = model.track(
            source=str(video_path),
            conf=0.25,
            imgsz=640,
            tracker="bytetrack.yaml",
            persist=True,
            verbose=False,
            stream=False,
        )
    except Exception as e:
        return {
            "status": "FAIL",
            "reason": "ULTRALYTICS_BYTETRACK_CALL_FAILED",
            "error": repr(e),
            "trace_tail": traceback.format_exc().splitlines()[-8:],
        }

    elapsed = time.time() - t0

    frame_count = 0
    id_seen = False

    try:
        frame_count = len(results) if results is not None else 0
        for r in results or []:
            boxes = getattr(r, "boxes", None)
            if boxes is not None and getattr(boxes, "id", None) is not None:
                id_seen = True
                break
    except Exception:
        pass

    return {
        "status": "PASS",
        "tracker": "bytetrack.yaml",
        "elapsed_sec": round(elapsed, 4),
        "frame_result_count": frame_count,
        "track_id_seen": id_seen,
        "note": "track_id_seen bisa false jika synthetic image tidak terdeteksi; yang diuji di sini adalah mode ByteTrack bisa dipanggil tanpa crash.",
    }


def edge_refinement_test(image_path: Path) -> Dict[str, Any]:
    import cv2
    import numpy as np

    img = cv2.imread(str(image_path))
    if img is None:
        return {"status": "FAIL", "reason": "IMAGE_READ_FAILED"}

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (5, 5), 0)
    edges = cv2.Canny(blur, 80, 160)

    edge_pixels = int(np.count_nonzero(edges))
    h, w = edges.shape[:2]
    edge_ratio = edge_pixels / float(h * w)

    out_path = TMP_DIR / "edge_refinement_preview.jpg"
    ensure_report_only_path(out_path)

    preview = img.copy()
    preview[edges > 0] = (0, 0, 255)
    cv2.imwrite(str(out_path), preview)

    return {
        "status": "PASS",
        "method": "cv2.Canny + preview overlay",
        "edge_pixels": edge_pixels,
        "edge_ratio": round(edge_ratio, 6),
        "preview_path": rel(out_path),
        "note": "Edge preview adalah diagnostic-only, belum clearance final.",
    }


def main() -> int:
    report: Dict[str, Any] = {
        "version": VERSION,
        "timestamp": now_iso(),
        "root": str(ROOT),
        "status": "INIT",
        "hard_failures": [],
        "safety": {
            "no_label_touch": True,
            "no_raw_touch": True,
            "no_dataset_touch": True,
            "no_runs_touch": True,
            "no_weights_touch": True,
            "reports_only_write": True,
            "not_final_clearance": True,
            "not_final_pruning_decision": True,
        },
    }

    try:
        if not ROOT.exists():
            raise RuntimeError(f"ROOT_NOT_FOUND: {ROOT}")

        REPORTS.mkdir(parents=True, exist_ok=True)
        TMP_DIR.mkdir(parents=True, exist_ok=True)

        report["imports"] = import_stack()

        import_ok = (
            report["imports"]["imports"].get("ultralytics", {}).get("ok") is True
            and report["imports"]["imports"].get("cv2", {}).get("ok") is True
        )
        if not import_ok:
            report["hard_failures"].append("import_stack_not_ready")

        model_path = find_model()
        if model_path is None:
            report["model_status"] = {
                "status": "TREE_MODEL_NOT_FOUND",
                "checked": [rel(p) for p in MODEL_CANDIDATES],
            }
            report["hard_failures"].append("tree_model_not_found")
        else:
            report["model_status"] = {
                "status": "TREE_MODEL_CANDIDATE_FOUND",
                "selected": rel(model_path),
                "checked": [rel(p) for p in MODEL_CANDIDATES],
            }

            image_path = create_test_image()
            video_path = create_test_video(image_path)

            report["test_assets"] = {
                "image": rel(image_path),
                "video": rel(video_path),
                "diagnostic_only": True,
                "not_field_evidence": True,
            }

            try:
                report["yolo_predict"] = yolo_predict_test(model_path, image_path)
            except Exception as e:
                report["yolo_predict"] = {
                    "status": "FAIL",
                    "error": repr(e),
                    "trace_tail": traceback.format_exc().splitlines()[-10:],
                }
                report["hard_failures"].append("yolo_predict_failed")

            try:
                report["bytetrack"] = bytetrack_test(model_path, video_path)
            except Exception as e:
                report["bytetrack"] = {
                    "status": "FAIL",
                    "error": repr(e),
                    "trace_tail": traceback.format_exc().splitlines()[-10:],
                }
                report["hard_failures"].append("bytetrack_failed")

            try:
                report["edge_refinement"] = edge_refinement_test(image_path)
            except Exception as e:
                report["edge_refinement"] = {
                    "status": "FAIL",
                    "error": repr(e),
                    "trace_tail": traceback.format_exc().splitlines()[-10:],
                }
                report["hard_failures"].append("edge_refinement_failed")

        # Current architectural truth.
        report["current_system_truth"] = {
            "tree_model": "TREE_MODEL_READY_CANDIDATE" if model_path else "TREE_MODEL_NOT_FOUND",
            "pole_model": "POLE_MODEL_NOT_READY",
            "conductor_model": "CONDUCTOR_MODEL_NOT_READY",
            "multiclass_model": "MULTICLASS_MODEL_NOT_READY",
            "clearance": "CLEARANCE_NOT_FINAL_NO_POLE_CONDUCTOR",
            "eta": "INSUFFICIENT_GEOMETRY_DATA",
            "reason": [
                "Tree candidate can be audited.",
                "Pole/conductor detection is still required before monocular clearance.",
                "No fake clearance or pruning ETA is allowed.",
            ],
        }

        if report["hard_failures"]:
            report["status"] = "PROGRESS_6_17_CORE_VISION_AUDIT_FAILED"
            code = 1
        else:
            report["status"] = "PROGRESS_6_17_CORE_VISION_AUDIT_PASS"
            code = 0

        safe_write_json(REPORT_PATH, report)
        print(json.dumps(report, indent=2, ensure_ascii=False))
        print(f"REPORT={REPORT_PATH}")
        return code

    except Exception as e:
        report["status"] = "PROGRESS_6_17_CORE_VISION_AUDIT_EXCEPTION"
        report["hard_failures"].append("unhandled_exception")
        report["error"] = repr(e)
        report["trace_tail"] = traceback.format_exc().splitlines()[-20:]
        safe_write_json(REPORT_PATH, report)
        print(json.dumps(report, indent=2, ensure_ascii=False))
        print(f"REPORT={REPORT_PATH}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
