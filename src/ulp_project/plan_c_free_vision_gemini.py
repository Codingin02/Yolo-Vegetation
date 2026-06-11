"""Gemini free-tier vision adapter for Plan C."""

from __future__ import annotations

import base64
import json
from pathlib import Path
import urllib.error
import urllib.request
from typing import Any

from .plan_c_free_vision_schema import normalize_detection_payload, parse_json_from_text


def detect_with_gemini(image_path: Path, *, image_width: int, image_height: int, provider_config: dict[str, Any]) -> dict[str, Any]:
    api_key = provider_config.get("api_key")
    model = provider_config.get("model") or "gemini-2.5-flash"
    if not api_key:
        return _disabled("FREE_VISION_KEY_MISSING")
    try:
        image_b64 = base64.b64encode(image_path.read_bytes()).decode("ascii")
        request_body = {
            "contents": [
                {
                    "parts": [
                        {"text": _prompt()},
                        {"inline_data": {"mime_type": "image/jpeg", "data": image_b64}},
                    ]
                }
            ],
            "generationConfig": {"temperature": 0.0, "response_mime_type": "application/json"},
        }
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
        request = urllib.request.Request(url, data=json.dumps(request_body).encode("utf-8"), headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(request, timeout=20) as response:
            data = json.loads(response.read().decode("utf-8"))
        text = _extract_text(data)
        normalized = normalize_detection_payload(parse_json_from_text(text), image_width=image_width, image_height=image_height, source_internal="redacted_provider")
        return {**normalized, "status": normalized["status"], "role": provider_config.get("role", "primary"), "configured": True, "raw_response_redacted": _truncate(text)}
    except (OSError, urllib.error.URLError, urllib.error.HTTPError, json.JSONDecodeError) as exc:
        return _failed(exc)


def _prompt() -> str:
    return (
        "Return JSON only. Detect only these classes: struktur_penyangga, konduktor, pohon_sono. "
        "Return {'detections':[{'class_name':'...','bbox_xyxy':[x1,y1,x2,y2],'bbox_format':'0_1000','confidence':0.0}]} "
        "using image coordinates normalized from 0 to 1000. No extra text."
    )


def _extract_text(data: dict[str, Any]) -> str:
    parts = data.get("candidates", [{}])[0].get("content", {}).get("parts", [])
    texts = [str(part.get("text") or "") for part in parts if isinstance(part, dict)]
    return "\n".join(texts)


def _disabled(status: str) -> dict[str, Any]:
    return {"status": status, "role": "primary", "configured": False, "detections": [], "detection_count": 0, "source_internal": "redacted_provider"}


def _failed(exc: Exception) -> dict[str, Any]:
    return {
        "status": "VISION_PROVIDER_FAILED",
        "role": "primary",
        "configured": True,
        "detections": [],
        "detection_count": 0,
        "error_redacted": f"{type(exc).__name__}: {str(exc)[:180]}",
        "source_internal": "redacted_provider",
    }


def _truncate(text: str) -> str:
    return str(text or "")[:2000]
