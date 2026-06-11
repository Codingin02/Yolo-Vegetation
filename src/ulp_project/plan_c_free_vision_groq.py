"""Groq free-tier vision adapter for Plan C."""

from __future__ import annotations

import base64
import json
from pathlib import Path
import urllib.error
import urllib.request
from typing import Any

from .plan_c_free_vision_schema import normalize_detection_payload, parse_json_from_text


def detect_with_groq(image_path: Path, *, image_width: int, image_height: int, provider_config: dict[str, Any]) -> dict[str, Any]:
    api_key = provider_config.get("api_key")
    model = provider_config.get("model") or "meta-llama/llama-4-scout-17b-16e-instruct"
    if not api_key:
        return _disabled("FREE_VISION_KEY_MISSING")
    try:
        data_url = "data:image/jpeg;base64," + base64.b64encode(image_path.read_bytes()).decode("ascii")
        body = {
            "model": model,
            "temperature": 0,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": _prompt()},
                        {"type": "image_url", "image_url": {"url": data_url}},
                    ],
                }
            ],
        }
        request = urllib.request.Request(
            "https://api.groq.com/openai/v1/chat/completions",
            data=json.dumps(body).encode("utf-8"),
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        )
        with urllib.request.urlopen(request, timeout=20) as response:
            data = json.loads(response.read().decode("utf-8"))
        text = str(data.get("choices", [{}])[0].get("message", {}).get("content") or "")
        normalized = normalize_detection_payload(parse_json_from_text(text), image_width=image_width, image_height=image_height, source_internal="redacted_provider")
        return {**normalized, "role": provider_config.get("role", "secondary"), "configured": True, "raw_response_redacted": text[:2000]}
    except (OSError, urllib.error.URLError, urllib.error.HTTPError, json.JSONDecodeError) as exc:
        return _failed(exc)


def _prompt() -> str:
    return (
        "Return JSON only. Detect only struktur_penyangga, konduktor, pohon_sono. "
        "Use {'detections':[{'class_name':'...','bbox_xyxy':[x1,y1,x2,y2],'bbox_format':'0_1000','confidence':0.0}]}. "
        "Coordinates must be 0 to 1000. No markdown."
    )


def _disabled(status: str) -> dict[str, Any]:
    return {"status": status, "role": "secondary", "configured": False, "detections": [], "detection_count": 0, "source_internal": "redacted_provider"}


def _failed(exc: Exception) -> dict[str, Any]:
    return {
        "status": "VISION_PROVIDER_FAILED",
        "role": "secondary",
        "configured": True,
        "detections": [],
        "detection_count": 0,
        "error_redacted": f"{type(exc).__name__}: {str(exc)[:180]}",
        "source_internal": "redacted_provider",
    }
