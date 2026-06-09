from __future__ import annotations

import base64
import json
import sys
import tempfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ulp_project.flask_app import create_app  # noqa: E402


IMAGE_ROOTS = [
    ROOT / "data" / "raw" / "00_inbox_hp" / "images",
    ROOT / "data" / "raw" / "01_field_points",
]


def _candidate_images() -> list[Path]:
    out: list[Path] = []
    for root in IMAGE_ROOTS:
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if path.suffix.lower() not in {".jpg", ".jpeg", ".png", ".webp"}:
                continue
            low = str(path).lower()
            if "dataset_botol" in low:
                continue
            if "v001" in low or "pohon_sono" in low or "sono" in low:
                out.append(path)
    return sorted(dict.fromkeys(out), key=lambda p: (0 if "v001" in str(p).lower() else 1, len(str(p))))[:12]


def _image_b64(path: Path) -> str:
    return base64.b64encode(path.read_bytes()).decode("ascii")


def _post_frame_for_first_detected(client: Any, session_id: str) -> tuple[Path | None, dict[str, Any], int]:
    last_payload: dict[str, Any] = {}
    last_status = 0
    for image in _candidate_images():
        response = client.post(
            "/api/field/session/frame",
            json={
                "session_id": session_id,
                "frame_base64": _image_b64(image),
                "source": "PROGRESS_6_21_CANONICAL_OUTPUT_SMOKE_READ_ONLY_LOCAL_IMAGE",
                "no_fake_detection": True,
                "no_fake_gps": True,
            },
        )
        payload = response.get_json() or {}
        last_payload = payload
        last_status = response.status_code
        if payload.get("progress6_20_gps_yolo", {}).get("yolo_detection", {}).get("tree_detected"):
            return image, payload, response.status_code
    return None, last_payload, last_status


def run_smoke() -> dict[str, Any]:
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        app = create_app(runtime_root=Path(tmp))
        client = app.test_client()
        start = client.post(
            "/api/field/session/start",
            json={"point_id": "V001_pohon_sono", "source_mode": "SMOKE_TEST", "idempotency_key": "P621_CANONICAL_START"},
        )
        start_payload = start.get_json() or {}
        session_id = str(start_payload.get("session_id") or "")
        image, frame, frame_status = _post_frame_for_first_detected(client, session_id)

    measurement = frame.get("measurement_result") if isinstance(frame.get("measurement_result"), dict) else {}
    overlay = frame.get("overlay_json") if isinstance(frame.get("overlay_json"), dict) else {}
    p620 = frame.get("progress6_20_gps_yolo") if isinstance(frame.get("progress6_20_gps_yolo"), dict) else {}
    yolo = p620.get("yolo_detection") if isinstance(p620.get("yolo_detection"), dict) else {}
    boxes = overlay.get("boxes") if isinstance(overlay.get("boxes"), list) else []

    checks = {
        "frame_route_ok": 200 <= frame_status < 300,
        "progress6_20_tree_detected": yolo.get("tree_detected") is True,
        "overlay_boxes_not_empty": len(boxes) > 0,
        "measurement_tree_detected_true": measurement.get("tree_detected") is True,
        "top_level_tree_detected_true": frame.get("tree_detected") is True,
        "yolo_detection_status": frame.get("yolo_detection_status") == "YOLO_TREE_DETECTED",
        "tracking_status": frame.get("tracking_status") == "YOLO_TREE_DETECTED",
        "overlay_message": overlay.get("message") == "YOLO_TREE_DETECTED",
        "no_tree_not_detected_reason": "TREE_NOT_DETECTED_BY_CANDIDATE_MODEL" not in (measurement.get("reason_codes") or []),
    }

    return {
        "status": "PROGRESS_6_21_CANONICAL_OUTPUT_PASS" if all(checks.values()) else "PROGRESS_6_21_CANONICAL_OUTPUT_FAIL",
        "checks": checks,
        "session_id": session_id,
        "selected_image": str(image.relative_to(ROOT)) if image else None,
        "overlay_box_count": len(boxes),
        "measurement_result": {
            "tree_detected": measurement.get("tree_detected"),
            "tree_confidence": measurement.get("tree_confidence"),
            "tree_bbox": measurement.get("tree_bbox"),
            "clearance_m": measurement.get("clearance_m"),
            "zone_status": measurement.get("zone_status"),
        },
        "yolo_detection_status": frame.get("yolo_detection_status"),
        "tracking_status": frame.get("tracking_status"),
        "pole_detected": frame.get("pole_detected"),
        "conductor_detected": frame.get("conductor_detected"),
        "pole_model_status": frame.get("pole_model_status"),
        "conductor_model_status": frame.get("conductor_model_status"),
        "no_fake_pole_conductor_detection": frame.get("no_fake_pole_conductor_detection"),
        "no_label_touch": True,
        "no_raw_touch": True,
        "no_runs_touch": True,
        "no_weights_touch": True,
    }


def main() -> int:
    result = run_smoke()
    print(json.dumps(result, indent=2, ensure_ascii=False))
    print(result["status"])
    return 0 if result["status"].endswith("_PASS") else 1


if __name__ == "__main__":
    raise SystemExit(main())
