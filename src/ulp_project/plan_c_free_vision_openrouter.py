"""OpenRouter free-model vision adapter for Plan C."""

from __future__ import annotations

import base64
import json
from pathlib import Path
import urllib.error
import urllib.request
from typing import Any

from .plan_c_free_vision_schema import normalize_detection_payload, parse_json_from_text


def detect_with_openrouter(image_path: Path, *, image_width: int, image_height: int, provider_config: dict[str, Any], free_only: bool = True) -> dict[str, Any]:
    api_key = provider_config.get("api_key")
    model = provider_config.get("model")
    if not api_key:
        return _disabled("FREE_VISION_KEY_MISSING")
    if not model:
        return _disabled("FREE_VISION_NOT_CONFIGURED")
    if free_only and not check_openrouter_free_model(model, api_key=api_key):
        return _disabled("FREE_VISION_NOT_CONFIGURED")
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
            "https://openrouter.ai/api/v1/chat/completions",
            data=json.dumps(body).encode("utf-8"),
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        )
        with urllib.request.urlopen(request, timeout=20) as response:
            data = json.loads(response.read().decode("utf-8"))
        text = str(data.get("choices", [{}])[0].get("message", {}).get("content") or "")
        normalized = normalize_detection_payload(parse_json_from_text(text), image_width=image_width, image_height=image_height, source_internal="redacted_provider")
        return {**normalized, "role": provider_config.get("role", "tertiary"), "configured": True, "raw_response_redacted": text[:2000]}
    except (OSError, urllib.error.URLError, urllib.error.HTTPError, json.JSONDecodeError) as exc:
        return _failed(exc)


def check_openrouter_free_model(model_id: str, *, api_key: str) -> bool:
    if not model_id:
        return False
    try:
        request = urllib.request.Request("https://openrouter.ai/api/v1/models", headers={"Authorization": f"Bearer {api_key}"})
        with urllib.request.urlopen(request, timeout=20) as response:
            data = json.loads(response.read().decode("utf-8"))
    except Exception:
        return False
    for model in data.get("data", []):
        if model.get("id") != model_id:
            continue
        modalities = set(model.get("architecture", {}).get("input_modalities") or model.get("input_modalities") or [])
        pricing = model.get("pricing") or {}
        prompt = str(pricing.get("prompt", "")).strip()
        completion = str(pricing.get("completion", "")).strip()
        image = str(pricing.get("image", "")).strip()
        is_free = prompt in {"0", "0.0", ""} and completion in {"0", "0.0", ""} and image in {"0", "0.0", ""}
        return is_free and "image" in modalities
    return False


def _prompt() -> str:
    return (
        "Return JSON only. Detect only struktur_penyangga, konduktor, pohon_sono. "
        "Use normalized 0-1000 bbox_xyxy."
    )


def _disabled(status: str) -> dict[str, Any]:
    return {"status": status, "role": "tertiary", "configured": False, "detections": [], "detection_count": 0, "source_internal": "redacted_provider"}


def _failed(exc: Exception) -> dict[str, Any]:
    return {
        "status": "VISION_PROVIDER_FAILED",
        "role": "tertiary",
        "configured": True,
        "detections": [],
        "detection_count": 0,
        "error_redacted": f"{type(exc).__name__}: {str(exc)[:180]}",
        "source_internal": "redacted_provider",
    }
