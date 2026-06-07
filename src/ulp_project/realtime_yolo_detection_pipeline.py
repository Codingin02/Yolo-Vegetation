"""Realtime YOLO readiness and candidate geometry pipeline.

The pipeline is automatic-first: it consumes camera frames and model outputs.
Manual operator input is not a primary measurement path.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .geometry_reference_scaling import compute_reference_geometry
from .paths import PROJECT_ROOT
from .tree_detection_runtime import infer_tree_candidate, tree_model_status

REQUIRED_MULTICLASS_NAMES = {"struktur_penyangga", "konduktor", "pohon_sono"}


def model_readiness_status() -> dict[str, Any]:
    multiclass = _find_multiclass_candidate()
    tree = tree_model_status()
    if multiclass:
        return {
            "status": "MULTICLASS_MODEL_READY_CANDIDATE",
            "model_status": "MULTICLASS_MODEL_READY_CANDIDATE",
            "multiclass_model_path": str(multiclass),
            "required_classes": sorted(REQUIRED_MULTICLASS_NAMES),
            "tree_model_status": tree.get("tree_model_status"),
            "pole_model_status": "POLE_MODEL_READY_CANDIDATE",
            "conductor_model_status": "CONDUCTOR_MODEL_READY_CANDIDATE",
            "production_status": "NOT_FINAL_CANDIDATE_DETECTION",
            "no_fake_detection": True,
        }
    if tree.get("tree_model_status") == "TREE_MODEL_READY_CANDIDATE":
        return {
            "status": "TREE_MODEL_READY_CANDIDATE",
            "model_status": "TREE_MODEL_READY_CANDIDATE",
            "tree_model_status": "TREE_MODEL_READY_CANDIDATE",
            "tree_model_path": tree.get("model_path"),
            "pole_model_status": "POLE_MODEL_NOT_READY",
            "conductor_model_status": "CONDUCTOR_MODEL_NOT_READY",
            "geometry_readiness": "AUTO_GEOMETRY_BLOCKED_WAITING_FOR_POLE_CONDUCTOR_MODEL",
            "production_status": "NOT_FINAL_CANDIDATE_DETECTION",
            "no_fake_pole_conductor_detection": True,
            "no_fake_detection": True,
        }
    return {
        "status": "MODEL_NOT_READY_NO_FAKE_DETECTION",
        "model_status": "MODEL_NOT_READY",
        "tree_model_status": tree.get("tree_model_status", "TREE_MODEL_NOT_READY"),
        "pole_model_status": "POLE_MODEL_NOT_READY",
        "conductor_model_status": "CONDUCTOR_MODEL_NOT_READY",
        "geometry_readiness": "AUTO_GEOMETRY_BLOCKED_WAITING_FOR_MODEL",
        "no_fake_detection": True,
    }


def process_realtime_yolo_frame(payload: dict[str, Any]) -> dict[str, Any]:
    readiness = model_readiness_status()
    if payload.get("mock_multiclass_detections") or payload.get("mock_detections"):
        detections = list(payload.get("mock_multiclass_detections") or payload.get("mock_detections") or [])
        geometry = compute_reference_geometry(
            detections,
            frame_width=_number_or_none(payload.get("camera_width") or payload.get("frame_width")),
            frame_height=_number_or_none(payload.get("camera_height") or payload.get("frame_height")),
            reference_pole_height_m=_number_or_none(payload.get("reference_pole_height_m")),
        )
        return {
            "status": "REALTIME_YOLO_PIPELINE_OK",
            "detections": detections,
            "detected_classes": sorted({str(item.get("class_name") or item.get("label")) for item in detections if item.get("class_name") or item.get("label")}),
            "tree": _presence_payload(detections, "pohon_sono"),
            "pole": _presence_payload(detections, "struktur_penyangga"),
            "conductor": _presence_payload(detections, "konduktor"),
            "tree_detected": _presence_payload(detections, "pohon_sono")["detected"],
            "pole_detected": _presence_payload(detections, "struktur_penyangga")["detected"],
            "conductor_detected": _presence_payload(detections, "konduktor")["detected"],
            "model_readiness": {**readiness, "status": "MULTICLASS_MODEL_READY_CANDIDATE"},
            "model_status": "MULTICLASS_MODEL_READY_CANDIDATE",
            "geometry_readiness": geometry.get("geometry_status"),
            "geometry": geometry,
            "no_fake_detection": True,
        }

    tree = infer_tree_candidate(payload)
    geometry = compute_reference_geometry(tree.get("detections", []))
    return {
        "status": "REALTIME_YOLO_PIPELINE_OK",
        "detections": tree.get("detections", []),
        "detected_classes": tree.get("detected_classes", []),
        "tree": {
            "detected": bool(tree.get("tree_detected")),
            "confidence": tree.get("tree_confidence", 0.0),
            "bbox": tree.get("tree_bbox_xyxy"),
            "status": tree.get("tree_model_status"),
        },
        "pole": {"detected": False, "status": "POLE_MODEL_NOT_READY"},
        "conductor": {"detected": False, "status": "CONDUCTOR_MODEL_NOT_READY"},
        "tree_detected": bool(tree.get("tree_detected")),
        "pole_detected": False,
        "conductor_detected": False,
        "tree_confidence": tree.get("tree_confidence", 0.0),
        "tree_bbox_xyxy": tree.get("tree_bbox_xyxy"),
        "model_readiness": readiness,
        "model_status": readiness.get("model_status", "MODEL_NOT_READY"),
        "tree_model_status": readiness.get("tree_model_status"),
        "pole_model_status": "POLE_MODEL_NOT_READY",
        "conductor_model_status": "CONDUCTOR_MODEL_NOT_READY",
        "geometry_readiness": "AUTO_GEOMETRY_BLOCKED_WAITING_FOR_POLE_CONDUCTOR_MODEL",
        "geometry": geometry,
        "decode_status": tree.get("decode_status"),
        "production_status": "NOT_FINAL_CANDIDATE_DETECTION" if readiness.get("status") == "TREE_MODEL_READY_CANDIDATE" else "NOT_FINAL",
        "no_fake_pole_conductor_detection": True,
        "no_fake_detection": True,
    }


def _find_multiclass_candidate() -> Path | None:
    candidates = [PROJECT_ROOT / "models" / "best.pt"]
    candidates.extend(PROJECT_ROOT.glob("runs/detect*/weights/best.pt"))
    candidates.extend(PROJECT_ROOT.glob("runs/detect/*/weights/best.pt"))
    for path in candidates:
        if not path.exists():
            continue
        text = str(path).replace("\\", "/").lower()
        if "v001_pohon_sono_only" in text:
            continue
        names_file = path.with_name("classes.txt")
        if names_file.exists():
            names = {line.strip() for line in names_file.read_text(encoding="utf-8").splitlines() if line.strip()}
            if REQUIRED_MULTICLASS_NAMES.issubset(names):
                return path
    return None


def _presence_payload(detections: list[dict[str, Any]], class_name: str) -> dict[str, Any]:
    matches = [item for item in detections if str(item.get("class_name") or item.get("label")) == class_name]
    best = max(matches, key=lambda item: float(item.get("confidence") or 0.0), default={})
    return {
        "detected": bool(matches),
        "confidence": best.get("confidence", 0.0),
        "bbox": best.get("bbox_xyxy") or best.get("bbox"),
        "status": "DETECTED_BY_MULTICLASS_CANDIDATE" if matches else "NOT_DETECTED",
    }


def _number_or_none(value: Any) -> float | None:
    try:
        if value in {None, ""}:
            return None
        return float(value)
    except (TypeError, ValueError):
        return None
