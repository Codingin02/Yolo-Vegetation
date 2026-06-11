"""Append-only operator feedback learning store for Plan C."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .plan_c_storage import PLAN_C_RUNTIME_ROOT, read_json, relative_to_project, session_file, write_json

FEEDBACK_ROOT = PLAN_C_RUNTIME_ROOT / "feedback"
ACCEPTED_JSONL = FEEDBACK_ROOT / "accepted_records.jsonl"
REJECTED_JSONL = FEEDBACK_ROOT / "rejected_records.jsonl"
LABEL_DIR = FEEDBACK_ROOT / "yolo_compatible_labels"


def save_operator_feedback(payload: dict[str, Any]) -> dict[str, Any]:
    session_id = str(payload.get("session_id") or "").strip()
    verdict = str(payload.get("verdict") or payload.get("feedback") or "").strip().lower()
    note = str(payload.get("note") or "").strip()[:500]
    if not session_id:
        return {"ok": False, "status": "PLAN_C_SESSION_ID_REQUIRED"}
    if verdict in {"accept", "accepted", "benar", "true", "ok"}:
        return accept_reference(session_id, note=note)
    if verdict in {"reject", "rejected", "salah", "false", "hapus", "delete"}:
        return reject_reference(session_id, note=note)
    return {"ok": False, "status": "OPERATOR_FEEDBACK_VERDICT_INVALID", "session_id": session_id}


def accept_reference(session_id: str, *, note: str = "") -> dict[str, Any]:
    result = _load_result(session_id)
    record = _feedback_record(session_id, result, "accepted", note)
    _append_jsonl(ACCEPTED_JSONL, record)
    label_status = _write_yolo_compatible_label(session_id, result)
    result["operator_feedback_status"] = "accepted"
    result["active_result_status"] = "accepted"
    write_json(session_file(session_id, "result.json"), result)
    _sync_developer_feedback(session_id, "accepted")
    return {
        "ok": True,
        "status": "OPERATOR_ACCEPTED_REFERENCE_SAVED",
        "session_id": session_id,
        "label_status": label_status,
    }


def reject_reference(session_id: str, *, note: str = "") -> dict[str, Any]:
    result = _load_result(session_id)
    record = _feedback_record(session_id, result, "rejected", note)
    _append_jsonl(REJECTED_JSONL, record)
    result["operator_feedback_status"] = "rejected"
    result["active_result_status"] = "rejected"
    result["manual_review_required"] = True
    write_json(session_file(session_id, "result.json"), result)
    _sync_developer_feedback(session_id, "rejected")
    return {
        "ok": True,
        "status": "REJECTED_REMOVED_FROM_ACTIVE_RESULTS",
        "session_id": session_id,
    }


def rejected_session_ids() -> set[str]:
    ids: set[str] = set()
    if not REJECTED_JSONL.exists():
        return ids
    for line in REJECTED_JSONL.read_text(encoding="utf-8", errors="ignore").splitlines():
        if not line.strip():
            continue
        try:
            item = json.loads(line)
        except json.JSONDecodeError:
            continue
        session_id = str(item.get("session_id") or "")
        if session_id:
            ids.add(session_id)
    return ids


def _load_result(session_id: str) -> dict[str, Any]:
    result = read_json(session_file(session_id, "result.json"), default={}) or {}
    if not isinstance(result, dict):
        return {}
    return result


def _feedback_record(session_id: str, result: dict[str, Any], verdict: str, note: str) -> dict[str, Any]:
    files = result.get("files") if isinstance(result.get("files"), dict) else {}
    return {
        "session_id": session_id,
        "verdict": verdict,
        "note": note,
        "original_image": files.get("original"),
        "annotated_image": files.get("annotated"),
        "detections": result.get("detections", []),
        "species_status": result.get("tree_species_status", "unknown"),
        "zone_status": result.get("zone_status", "unavailable"),
        "risk_status": result.get("risk_status"),
        "prediction_window": result.get("prediction_window"),
        "operator_output_format": result.get("operator_output_format", "YOLO-compatible"),
    }


def _write_yolo_compatible_label(session_id: str, result: dict[str, Any]) -> dict[str, Any]:
    detections = result.get("detections") or []
    if not detections:
        return {"status": "NO_BBOX_TO_SAVE", "path": ""}
    width = _to_float(result.get("detection_image_width")) or _image_width(session_id) or 1.0
    height = _to_float(result.get("detection_image_height")) or _image_height(session_id) or 1.0
    lines = []
    for detection in detections:
        bbox = detection.get("bbox_xyxy")
        if not isinstance(bbox, list) or len(bbox) != 4:
            continue
        class_id = int(detection.get("class_id"))
        x1, y1, x2, y2 = [float(value) for value in bbox]
        cx = ((x1 + x2) / 2.0) / width
        cy = ((y1 + y2) / 2.0) / height
        bw = max(x2 - x1, 0.0) / width
        bh = max(y2 - y1, 0.0) / height
        lines.append(f"{class_id} {cx:.6f} {cy:.6f} {bw:.6f} {bh:.6f}")
    LABEL_DIR.mkdir(parents=True, exist_ok=True)
    path = LABEL_DIR / f"{session_id}.txt"
    path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")
    return {"status": "YOLO_COMPATIBLE_LABEL_SAVED", "path": relative_to_project(path), "line_count": len(lines)}


def _sync_developer_feedback(session_id: str, verdict: str) -> None:
    developer = read_json(session_file(session_id, "developer.json"), default={}) or {}
    if isinstance(developer, dict):
        developer["operator_feedback_status"] = verdict
        write_json(session_file(session_id, "developer.json"), developer)


def _append_jsonl(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False, default=str) + "\n")


def _image_width(session_id: str) -> float | None:
    size = _image_size(session_id)
    return float(size[0]) if size else None


def _image_height(session_id: str) -> float | None:
    size = _image_size(session_id)
    return float(size[1]) if size else None


def _image_size(session_id: str) -> tuple[int, int] | None:
    try:
        from PIL import Image

        with Image.open(session_file(session_id, "original.jpg")) as image:
            return int(image.width), int(image.height)
    except Exception:
        return None


def _to_float(value: Any) -> float | None:
    if value in {None, ""}:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
