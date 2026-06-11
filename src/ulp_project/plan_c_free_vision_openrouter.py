"""OpenRouter free-model vision verifier/fallback adapter for Plan C."""

from __future__ import annotations

import base64
import json
from pathlib import Path
from typing import Any
from urllib import request as urlrequest
from urllib.error import HTTPError, URLError

from .plan_c_detection_prompt_rules import build_plan_c_detection_prompt
from .plan_c_free_vision_schema import normalize_detection_payload, parse_json_from_text


def detect_with_openrouter(
    image_path: Path,
    *,
    image_width: int,
    image_height: int,
    provider_config: dict[str, Any] | None = None,
    free_only: bool = True,
    **_: Any,
) -> dict[str, Any]:
    provider_config = provider_config or {}
    api_key = str(provider_config.get("api_key") or "").strip()
    model = str(provider_config.get("model") or "").strip()
    role = str(provider_config.get("role") or "tertiary")
    if not api_key:
        return _disabled("FREE_VISION_KEY_MISSING", role=role)
    if not model:
        return _disabled("OPENROUTER_MODEL_NOT_CONFIGURED", role=role)
    if free_only and not _model_is_free_enough(model, api_key=api_key):
        return _disabled("OPENROUTER_MODEL_NOT_CONFIGURED", role=role)

    try:
        image_b64 = base64.b64encode(Path(image_path).read_bytes()).decode("ascii")
        body = {
            "model": model,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": build_plan_c_detection_prompt()},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_b64}"}},
                    ],
                }
            ],
            "temperature": 0,
            "max_tokens": 1200,
        }
        request = urlrequest.Request(
            "https://openrouter.ai/api/v1/chat/completions",
            data=json.dumps(body).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}",
                "HTTP-Referer": "http://127.0.0.1:5000",
                "X-Title": "ULP Plan C Field Trial",
            },
            method="POST",
        )
        with urlrequest.urlopen(request, timeout=20) as response:
            response_data = json.loads(response.read().decode("utf-8"))
        text = str(response_data.get("choices", [{}])[0].get("message", {}).get("content") or "")
        payload = parse_json_from_text(text)
        normalized = normalize_detection_payload(payload, image_width=image_width, image_height=image_height, source_internal="redacted_provider")
        return {
            **normalized,
            "role": role,
            "configured": True,
            "provider_status": "FREE_VISION_TERTIARY_USED",
            "raw_response_redacted": _truncate(text),
        }
    except HTTPError as exc:
        return _failed(f"VISION_PROVIDER_HTTP_{exc.code}", role=role, error=f"HTTPError: {exc.code}")
    except (URLError, OSError, json.JSONDecodeError) as exc:
        return _failed("VISION_PROVIDER_FAILED", role=role, error=f"{type(exc).__name__}: {str(exc)[:180]}")


def check_openrouter_free_model(model_id: str, *, api_key: str) -> bool:
    if not model_id:
        return False
    if ":free" in model_id:
        return True
    try:
        request = urlrequest.Request("https://openrouter.ai/api/v1/models", headers={"Authorization": f"Bearer {api_key}"})
        with urlrequest.urlopen(request, timeout=20) as response:
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


def _model_is_free_enough(model: str, *, api_key: str) -> bool:
    return check_openrouter_free_model(model, api_key=api_key)


def _disabled(status: str, *, role: str) -> dict[str, Any]:
    return {"status": status, "role": role, "configured": False, "detections": [], "detection_count": 0, "source_internal": "redacted_provider"}


def _failed(status: str, *, role: str, error: str) -> dict[str, Any]:
    return {
        "status": status,
        "role": role,
        "configured": True,
        "detections": [],
        "detection_count": 0,
        "error_redacted": error,
        "source_internal": "redacted_provider",
    }


def _truncate(text: str) -> str:
    return str(text or "")[:2000]
