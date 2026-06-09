import base64
import json
import os
import re
import time
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Tuple

from flask import jsonify, request

ROOT = Path(__file__).resolve().parents[2]
VERSION = "progress6_22_vision_api_runtime"

ALLOWED_GROUPS = {
    "struktur_penyangga",
    "konduktor",
    "pohon_sono_candidate",
    "general_object",
}

PROMPT = """
Anda adalah modul vision-assisted detection untuk inspeksi jaringan distribusi listrik.

Deteksi objek kandidat:
1. struktur_penyangga: tiang listrik, pole, support structure, cross-arm, struktur penyangga jaringan.
2. konduktor: kabel listrik udara, overhead conductor, kabel distribusi PLN.
3. pohon_sono_candidate: pohon, tajuk, daun, batang, vegetasi yang relevan dengan ROW jaringan.
4. general_object: manusia, laptop, keyboard, botol, pintu, dinding, kasur, kursi, kabel charger, kabel USB, benda rumah.

Aturan keras:
- Jangan klasifikasikan laptop/keyboard/pintu/dinding/kasur/manusia sebagai pohon.
- Jangan klasifikasikan kabel charger/USB/kabel meja sebagai konduktor PLN.
- Jangan klasifikasikan dinding, lemari, pintu, atau laptop sebagai struktur penyangga.
- Jangan klaim clearance, jarak meter, atau ETA trimming.
- Bounding box wajib format [y_min, x_min, y_max, x_max] skala 0 sampai 1000.
- Jika objek PLN tidak tampak, tetap boleh isi general_object.
- Output hanya JSON valid, tanpa markdown.

Schema:
{
  "status": "VISION_ASSISTED_READY",
  "detections": [
    {
      "label": "string",
      "object_group": "struktur_penyangga|konduktor|pohon_sono_candidate|general_object",
      "box_2d": [0,0,0,0],
      "confidence": 0.0,
      "evidence_reason": "string"
    }
  ],
  "frame_summary": "string"
}
"""

def _strip_data_url(value: str) -> str:
    value = (value or "").strip()
    if value.lower().startswith("data:image") and "," in value:
        return value.split(",", 1)[1]
    return value

def _strip_json(text: str) -> str:
    text = (text or "").strip()
    text = re.sub(r"^```json\s*", "", text)
    text = re.sub(r"^```\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    match = re.search(r"(\{.*\}|\[.*\])", text, re.S)
    return match.group(1) if match else text

def _image_bytes_from_payload(payload: Dict[str, Any]) -> Tuple[bytes | None, str]:
    for key in ("frame_base64", "image_base64", "jpeg_base64", "snapshot_base64", "frame_image_base64"):
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            try:
                return base64.b64decode(_strip_data_url(value), validate=False), key
            except Exception:
                return None, f"{key}_DECODE_FAILED"

    image_path = payload.get("image_path")
    if isinstance(image_path, str) and image_path.strip():
        path = (ROOT / image_path).resolve()
        try:
            path.relative_to(ROOT)
        except Exception:
            return None, "IMAGE_PATH_OUTSIDE_ROOT"
        if path.exists() and path.is_file():
            return path.read_bytes(), "image_path"

    return None, "NO_IMAGE_INPUT"

def _compress_image(image_bytes: bytes, max_side: int = 1280, max_bytes: int = 1600000) -> bytes:
    try:
        import cv2
        import numpy as np

        arr = np.frombuffer(image_bytes, dtype=np.uint8)
        img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
        if img is None:
            return image_bytes

        h, w = img.shape[:2]
        side = max(h, w)
        if side > max_side:
            scale = max_side / float(side)
            img = cv2.resize(img, (max(1, int(w * scale)), max(1, int(h * scale))), interpolation=cv2.INTER_AREA)

        quality = 84
        while quality >= 50:
            ok, buf = cv2.imencode(".jpg", img, [int(cv2.IMWRITE_JPEG_QUALITY), quality])
            if ok:
                out = bytes(buf)
                if len(out) <= max_bytes:
                    return out
            quality -= 7
    except Exception:
        pass

    return image_bytes

def _normalize(provider: str, model: str, parsed: Any) -> Dict[str, Any]:
    if not isinstance(parsed, dict):
        parsed = {"status": "VISION_ASSISTED_READY", "detections": [], "frame_summary": str(parsed)}

    raw_detections = parsed.get("detections")
    if not isinstance(raw_detections, list):
        raw_detections = []

    detections: List[Dict[str, Any]] = []
    boxes: List[Dict[str, Any]] = []

    for item in raw_detections:
        if not isinstance(item, dict):
            continue

        label = str(item.get("label", "object")).strip()[:80]
        group = str(item.get("object_group", "general_object")).strip()
        if group not in ALLOWED_GROUPS:
            group = "general_object"

        box = item.get("box_2d", [0, 0, 0, 0])
        if not isinstance(box, list) or len(box) != 4:
            box = [0, 0, 0, 0]

        try:
            box = [max(0.0, min(1000.0, float(x))) for x in box]
        except Exception:
            box = [0.0, 0.0, 0.0, 0.0]

        try:
            confidence = max(0.0, min(1.0, float(item.get("confidence", 0.0))))
        except Exception:
            confidence = 0.0

        det = {
            "label": label,
            "object_group": group,
            "box_2d": box,
            "bbox_norm_yxyx_1000": box,
            "confidence": confidence,
            "evidence_reason": str(item.get("evidence_reason", ""))[:300],
            "provider": provider,
            "model": model,
        }

        detections.append(det)
        boxes.append(det.copy())

    return {
        "ok": True,
        "status": "VISION_ASSISTED_RUNTIME_PASS",
        "vision_status": "VISION_ASSISTED_READY",
        "provider": provider,
        "model": model,
        "selected_provider": provider,
        "selected_model": model,
        "detections": detections,
        "overlay_json": {
            "status": "VISION_OVERLAY_READY",
            "message": "VISION_ASSISTED_DETECTION_READY",
            "boxes": boxes,
            "draw_client_side": True,
        },
        "frame_summary": str(parsed.get("frame_summary", ""))[:600],
        "tree_detected": any(d["object_group"] == "pohon_sono_candidate" for d in detections),
        "pole_detected": any(d["object_group"] == "struktur_penyangga" for d in detections),
        "conductor_detected": any(d["object_group"] == "konduktor" for d in detections),
        "clearance_status": "CLEARANCE_NOT_FINAL_MONO_SCALING_NOT_STARTED",
        "eta_status": "ETA_NOT_FINAL_MONO_SCALING_NOT_STARTED",
        "no_fake_detection": True,
        "no_fake_coordinate": True,
        "no_fake_clearance": True,
        "runtime_source": VERSION,
    }

def _post_json(url: str, payload: Dict[str, Any], headers: Dict[str, str], timeout: int = 80) -> Tuple[int, str]:
    req = urllib.request.Request(
        url=url,
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return int(resp.status), resp.read().decode("utf-8", errors="replace")

def _call_gemini(image_bytes: bytes, model: str) -> Dict[str, Any]:
    key = os.environ.get("GEMINI_API_KEY", "").strip()
    if not key:
        return {"ok": False, "provider": "gemini", "model": model, "error": "GEMINI_API_KEY_EMPTY"}

    payload = {
        "contents": [
            {
                "parts": [
                    {"text": PROMPT},
                    {"inline_data": {"mime_type": "image/jpeg", "data": base64.b64encode(image_bytes).decode("utf-8")}},
                ]
            }
        ],
        "generationConfig": {
            "temperature": 0.1,
            "response_mime_type": "application/json",
        },
    }

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"

    try:
        status, raw = _post_json(url, payload, {"Content-Type": "application/json"}, timeout=80)
        data = json.loads(raw)
        text = data["candidates"][0]["content"]["parts"][0]["text"]
        parsed = json.loads(_strip_json(text))
        result = _normalize("gemini", model, parsed)
        result["http_status"] = status
        return result
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        return {"ok": False, "provider": "gemini", "model": model, "http_status": exc.code, "error_body": body[:1500]}
    except Exception as exc:
        return {"ok": False, "provider": "gemini", "model": model, "error": repr(exc)}

def _call_openrouter(image_bytes: bytes, model: str) -> Dict[str, Any]:
    key = os.environ.get("OPENROUTER_API_KEY", "").strip()
    if not key:
        return {"ok": False, "provider": "openrouter", "model": model, "error": "OPENROUTER_API_KEY_EMPTY"}

    image_url = "data:image/jpeg;base64," + base64.b64encode(image_bytes).decode("utf-8")

    payload = {
        "model": model,
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": PROMPT},
                    {"type": "image_url", "image_url": {"url": image_url}},
                ],
            }
        ],
        "temperature": 0.1,
        "max_tokens": 1400,
    }

    try:
        status, raw = _post_json(
            "https://openrouter.ai/api/v1/chat/completions",
            payload,
            {
                "Content-Type": "application/json",
                "Authorization": "Bearer " + key,
                "HTTP-Referer": "http://localhost",
                "X-Title": "ULP Progress 6.22 Vision Assisted Field Detection",
            },
            timeout=90,
        )
        data = json.loads(raw)
        text = data["choices"][0]["message"]["content"]
        parsed = json.loads(_strip_json(text))
        result = _normalize("openrouter", model, parsed)
        result["http_status"] = status
        return result
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        return {"ok": False, "provider": "openrouter", "model": model, "http_status": exc.code, "error_body": body[:1500]}
    except Exception as exc:
        return {"ok": False, "provider": "openrouter", "model": model, "error": repr(exc)}

def analyze_image_bytes(image_bytes: bytes) -> Dict[str, Any]:
    image_bytes = _compress_image(image_bytes)
    attempts: List[Dict[str, Any]] = []

    for model in ("gemini-2.5-flash", "gemini-2.5-flash-lite"):
        result = _call_gemini(image_bytes, model)
        attempts.append({k: v for k, v in result.items() if k not in ("detections", "overlay_json")})
        if result.get("ok"):
            result["attempts"] = attempts
            return result
        if result.get("http_status") in (429, 500, 502, 503, 504):
            time.sleep(0.7)

    for model in ("google/gemini-2.0-flash-exp:free", "qwen/qwen2.5-vl-72b-instruct:free"):
        result = _call_openrouter(image_bytes, model)
        attempts.append({k: v for k, v in result.items() if k not in ("detections", "overlay_json")})
        if result.get("ok"):
            result["attempts"] = attempts
            return result

    return {
        "ok": False,
        "status": "VISION_API_UNAVAILABLE",
        "attempts": attempts,
        "detections": [],
        "overlay_json": {
            "status": "VISION_API_UNAVAILABLE",
            "message": "VISION_API_UNAVAILABLE",
            "boxes": [],
            "draw_client_side": True,
        },
        "clearance_status": "CLEARANCE_NOT_FINAL_VISION_API_UNAVAILABLE",
        "eta_status": "ETA_NOT_FINAL_VISION_API_UNAVAILABLE",
        "no_fake_detection": True,
        "no_fake_coordinate": True,
        "no_fake_clearance": True,
        "runtime_source": VERSION,
    }

def install_progress6_22_vision_api_runtime(app):
    if app is None:
        return app

    if "progress6_22_vision_status" not in app.view_functions:
        @app.get("/api/runtime/progress6-22-vision-status", endpoint="progress6_22_vision_status")
        def progress6_22_vision_status():
            return jsonify({
                "status": "PROGRESS_6_22_VISION_API_RUNTIME_INSTALLED",
                "version": VERSION,
                "primary_provider": "gemini",
                "fallback_provider": "openrouter",
                "groq_runtime_enabled": False,
                "gemini_key_present": bool(os.environ.get("GEMINI_API_KEY")),
                "openrouter_key_present": bool(os.environ.get("OPENROUTER_API_KEY")),
                "no_label_touch": True,
                "no_raw_touch": True,
                "no_dataset_touch": True,
                "no_runs_touch": True,
                "no_weights_touch": True,
            })

    if "progress6_22_vision_analyze" not in app.view_functions:
        @app.post("/api/field/session/vision-analyze", endpoint="progress6_22_vision_analyze")
        def progress6_22_vision_analyze():
            payload = request.get_json(silent=True) or {}
            image_bytes, used_key = _image_bytes_from_payload(payload)

            if not image_bytes:
                return jsonify({
                    "ok": False,
                    "status": "VISION_IMAGE_NOT_PROVIDED",
                    "used_key": used_key,
                    "detections": [],
                    "overlay_json": {"boxes": [], "draw_client_side": True},
                    "no_fake_detection": True,
                }), 400

            result = analyze_image_bytes(image_bytes)
            result["session_id"] = payload.get("session_id")
            result["used_image_key"] = used_key
            result["timestamp"] = datetime.now().isoformat(timespec="seconds")
            return jsonify(result), 200 if result.get("ok") else 503

    return app
