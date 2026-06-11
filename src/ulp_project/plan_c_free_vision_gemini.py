"""Gemini free-tier vision adapter for Plan C."""

from __future__ import annotations

import base64
import json
from pathlib import Path
from typing import Any
from urllib import request as urlrequest
from urllib.error import HTTPError, URLError

from .plan_c_detection_prompt_rules import build_plan_c_detection_prompt
from .plan_c_free_vision_schema import normalize_detection_payload, parse_json_from_text


def detect_with_gemini(
    image_path: Path,
    *,
    image_width: int,
    image_height: int,
    provider_config: dict[str, Any] | None = None,
    **_: Any,
) -> dict[str, Any]:
    provider_config = provider_config or {}
    api_key = str(provider_config.get("api_key") or "").strip()
    model = str(provider_config.get("model") or "gemini-2.5-flash").strip()
    role = str(provider_config.get("role") or "primary")
    if not api_key:
        return _disabled("FREE_VISION_KEY_MISSING", role=role)
    if not model:
        return _disabled("FREE_VISION_NOT_CONFIGURED", role=role)

    try:
        image_b64 = base64.b64encode(Path(image_path).read_bytes()).decode("ascii")
        body = {
            "contents": [
                {
                    "parts": [
                        {"text": build_plan_c_detection_prompt()},
                        {"inline_data": {"mime_type": "image/jpeg", "data": image_b64}},
                    ]
                }
            ],
            "generationConfig": {
                "temperature": 0,
                "response_mime_type": "application/json",
            },
        }
        request = urlrequest.Request(
            f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
            data=json.dumps(body).encode("utf-8"),
            headers={"Content-Type": "application/json", "x-goog-api-key": api_key},
            method="POST",
        )
        with urlrequest.urlopen(request, timeout=20) as response:
            response_data = json.loads(response.read().decode("utf-8"))
        text = _extract_text(response_data)
        payload = parse_json_from_text(text)
        normalized = normalize_detection_payload(payload, image_width=image_width, image_height=image_height, source_internal="redacted_provider")
        return {
            **normalized,
            "role": role,
            "configured": True,
            "provider_status": "FREE_VISION_PRIMARY_USED",
            "raw_response_redacted": _truncate(text),
        }
    except HTTPError as exc:
        return _failed(f"VISION_PROVIDER_HTTP_{exc.code}", role=role, error=f"HTTPError: {exc.code}")
    except (URLError, OSError, json.JSONDecodeError) as exc:
        return _failed("VISION_PROVIDER_FAILED", role=role, error=f"{type(exc).__name__}: {str(exc)[:180]}")


def _extract_text(data: dict[str, Any]) -> str:
    parts = data.get("candidates", [{}])[0].get("content", {}).get("parts", [])
    texts = [str(part.get("text") or "") for part in parts if isinstance(part, dict)]
    if texts:
        return "\n".join(texts)
    return json.dumps(data, ensure_ascii=False)


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
