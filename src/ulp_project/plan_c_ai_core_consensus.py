"""Three-provider visual consensus for Plan C System C runtime.

Cloud AI providers are inference validators, not trained locally by our label
dataset. The trained label dataset is reflected in the local YOLOv8 System C
detector and reference examples. The AI consensus refines/reviews visual
interpretation and zone decision without replacing YOLOv8 bounding boxes or
Python geometry.
"""

from __future__ import annotations

import base64
import json
import os
from pathlib import Path
import socket
from typing import Any
from urllib import error, request

DEFAULT_TIMEOUT_SECONDS = 75
PROMPT_VERSION = "plan_c_system_c_gemini_groq_openrouter_v2"


def load_provider_config() -> dict[str, Any]:
    gemini_key = os.getenv("GEMINI_API_KEY", "").strip()
    groq_key = os.getenv("GROQ_API_KEY", "").strip()
    openrouter_key = os.getenv("OPENROUTER_API_KEY", "").strip()
    return {
        "provider_priority": ["gemini", "groq", "openrouter"],
        "gemini": {
            "configured": bool(gemini_key),
            "model": os.getenv("GEMINI_VISION_MODEL", "").strip()
            or os.getenv("GEMINI_MODEL", "gemini-2.5-flash").strip()
            or "gemini-2.5-flash",
        },
        "groq": {
            "configured": bool(groq_key),
            "model": os.getenv("GROQ_VISION_MODEL", "").strip()
            or os.getenv("GROQ_MODEL", "").strip()
            or "meta-llama/llama-4-scout-17b-16e-instruct",
            "endpoint": "https://api.groq.com/openai/v1/chat/completions",
        },
        "openrouter": {
            "configured": bool(openrouter_key),
            "model": os.getenv("OPENROUTER_VISION_MODEL", "").strip()
            or os.getenv("OPENROUTER_MODEL", "qwen/qwen2.5-vl-72b-instruct:free").strip()
            or "qwen/qwen2.5-vl-72b-instruct:free",
        },
        "openai_ignored_for_plan_c": bool(os.getenv("OPENAI_API_KEY", "").strip()),
        "ignored_optional_legacy_key": {"XAI_API_KEY": bool(os.getenv("XAI_API_KEY", "").strip())},
        "no_secret_logged": True,
    }


def encode_image_base64(path: Path | str) -> str:
    return base64.b64encode(Path(path).read_bytes()).decode("ascii")


def call_gemini_vision(image_path: Path | str, context: dict[str, Any]) -> dict[str, Any]:
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    model = os.getenv("GEMINI_VISION_MODEL", "").strip() or os.getenv("GEMINI_MODEL", "gemini-2.5-flash").strip() or "gemini-2.5-flash"
    if not api_key:
        return _provider_result("gemini", "SKIPPED_NO_KEY")
    prompt = _build_prompt(context)
    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [
                    {"text": prompt},
                    {"inline_data": {"mime_type": "image/jpeg", "data": encode_image_base64(image_path)}},
                ],
            }
        ],
        "generationConfig": {"response_mime_type": "application/json", "temperature": 0.1},
    }
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    raw = _post_json(url, payload, headers={"Content-Type": "application/json"})
    if raw.get("status") != "OK":
        return _provider_result("gemini", raw.get("status", "HTTP_ERROR"), reason=raw.get("error", ""), raw=raw)
    text = ""
    try:
        parts = raw["json"]["candidates"][0]["content"]["parts"]
        text = " ".join(str(part.get("text", "")) for part in parts if isinstance(part, dict))
    except (KeyError, IndexError, TypeError):
        return _provider_result("gemini", "PARSE_ERROR", reason="Gemini response did not contain JSON text.", raw=raw)
    return normalize_provider_response("gemini", text)


def call_groq_vision(image_path: Path | str, context: dict[str, Any]) -> dict[str, Any]:
    api_key = os.getenv("GROQ_API_KEY", "").strip()
    model = os.getenv("GROQ_VISION_MODEL", "").strip() or os.getenv("GROQ_MODEL", "").strip() or "meta-llama/llama-4-scout-17b-16e-instruct"
    if not api_key:
        return _provider_result("groq", "SKIPPED_NO_KEY")
    payload = _chat_vision_payload(model, image_path, context)
    raw = _post_json(
        "https://api.groq.com/openai/v1/chat/completions",
        payload,
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"},
    )
    if raw.get("status") != "OK":
        return _provider_result("groq", raw.get("status", "HTTP_ERROR"), reason=raw.get("error", ""), raw=raw)
    return normalize_provider_response("groq", _chat_text(raw))


def call_grok_vision(image_path: Path | str, context: dict[str, Any]) -> dict[str, Any]:
    """Compatibility alias for older code; uses Groq Console, not xAI."""

    return call_groq_vision(image_path, context)


def call_openrouter_vision(image_path: Path | str, context: dict[str, Any]) -> dict[str, Any]:
    api_key = os.getenv("OPENROUTER_API_KEY", "").strip()
    model = os.getenv("OPENROUTER_VISION_MODEL", "").strip() or os.getenv("OPENROUTER_MODEL", "qwen/qwen2.5-vl-72b-instruct:free").strip()
    if not api_key:
        return _provider_result("openrouter", "SKIPPED_NO_KEY")
    if ":free" not in model and "free" not in model.lower():
        return _provider_result("openrouter", "SKIPPED_MODEL_NOT_FREE", reason="OpenRouter model is not marked free.")
    payload = _chat_vision_payload(model, image_path, context)
    raw = _post_json(
        "https://openrouter.ai/api/v1/chat/completions",
        payload,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
            "HTTP-Referer": "http://localhost/plan-c",
            "X-Title": "ULP Plan C Field Trial",
        },
    )
    if raw.get("status") != "OK":
        return _provider_result("openrouter", raw.get("status", "HTTP_ERROR"), reason=raw.get("error", ""), raw=raw)
    return normalize_provider_response("openrouter", _chat_text(raw))


def run_ai_consensus(
    image_path: Path | str,
    yolo_detections: list[dict[str, Any]],
    growth_summary: dict[str, Any],
    metadata: dict[str, Any],
) -> dict[str, Any]:
    image_width, image_height = _read_image_size(image_path)
    context = {
        "runtime_mode": "PLAN_C_SYSTEM_C",
        "detector": "YOLOv8",
        "yolo_detections": _redact_detection_list(yolo_detections),
        "growth_summary": {
            "growth_profile_status": growth_summary.get("growth_profile_status"),
            "growth_rate_m_per_quarter": growth_summary.get("growth_rate_m_per_quarter"),
            "data_source_type": growth_summary.get("data_source_type"),
        },
        "metadata": {
            "session_id": metadata.get("session_id"),
            "source": metadata.get("capture_source"),
            "gps_status": metadata.get("gps_status"),
        },
        "image_width": image_width,
        "image_height": image_height,
    }
    provider_results = [
        call_gemini_vision(image_path, context),
        call_groq_vision(image_path, context),
        call_openrouter_vision(image_path, context),
    ]
    summary = build_ai_consensus_summary(provider_results)
    candidates = [item for item in provider_results if item.get("bbox_xyxy")]
    chosen = choose_best_tree_bbox(_best_yolo_bbox(yolo_detections), candidates, image_width=image_width, image_height=image_height)
    return {
        "status": "AI_CONSENSUS_COMPLETE",
        "ai_core_mode": "THREE_PROVIDER_CONSENSUS",
        "prompt_version": PROMPT_VERSION,
        "providers_enabled": summary.get("providers_enabled", []),
        "provider_statuses": summary.get("provider_statuses", []),
        "provider_results": provider_results,
        "summary": summary,
        "chosen_bbox": chosen.get("bbox_xyxy"),
        "chosen_bbox_source": chosen.get("source"),
        "risk_zone_guess": summary.get("risk_zone_guess", "REVIEW_REQUIRED"),
        "retake_recommendation": summary.get("retake_recommendation", ""),
        "tree_visible_consensus": summary.get("tree_visible_consensus"),
        "no_secret_logged": True,
    }


def normalize_provider_response(provider_name: str, raw_response: Any) -> dict[str, Any]:
    if isinstance(raw_response, dict):
        payload = raw_response
    else:
        try:
            payload = _extract_json_object(str(raw_response or ""))
        except ValueError as exc:
            return _provider_result(provider_name, "PARSE_ERROR", reason=str(exc), raw={"text_preview": str(raw_response)[:500]})
    candidate = {
        "provider": provider_name,
        "status": "OK",
        "tree_visible": _to_optional_bool(payload.get("tree_visible")),
        "tree_species_guess": str(payload.get("tree_species_guess") or payload.get("species_guess") or "unknown"),
        "risk_zone_guess": _normalize_zone(payload.get("risk_zone_guess") or payload.get("zone") or "REVIEW_REQUIRED"),
        "bbox_xyxy": _normalize_bbox(payload.get("bbox_xyxy") or payload.get("bbox")),
        "confidence": _clamp_confidence(payload.get("confidence")),
        "reason": str(payload.get("reason") or "")[:500],
        "retake_recommendation": str(payload.get("retake_recommendation") or "")[:500],
        "false_positive_likelihood": _clamp_confidence(payload.get("false_positive_likelihood")),
        "false_negative_likelihood": _clamp_confidence(payload.get("false_negative_likelihood")),
        "confidence_adjustment": _clamp_adjustment(payload.get("confidence_adjustment")),
        "image_quality_flags": _normalize_string_list(payload.get("image_quality_flags")),
        "bbox_sanity": str(payload.get("bbox_sanity") or "REVIEW_REQUIRED")[:120],
        "raw_redacted": _redact_raw(payload),
    }
    return candidate


def validate_ai_bbox(candidate: dict[str, Any], image_width: int, image_height: int) -> dict[str, Any]:
    bbox = candidate.get("bbox_xyxy")
    if not isinstance(bbox, list) or len(bbox) != 4:
        return {"valid": False, "reason": "BBOX_MISSING"}
    try:
        x1, y1, x2, y2 = [float(value) for value in bbox]
    except (TypeError, ValueError):
        return {"valid": False, "reason": "BBOX_NOT_NUMERIC"}
    if x1 >= x2 or y1 >= y2:
        return {"valid": False, "reason": "BBOX_INVALID_ORDER"}
    if image_width <= 0 or image_height <= 0:
        return {"valid": False, "reason": "IMAGE_SIZE_INVALID"}
    if x1 < 0 or y1 < 0 or x2 > image_width or y2 > image_height:
        return {"valid": False, "reason": "BBOX_OUT_OF_BOUNDS"}
    area = (x2 - x1) * (y2 - y1)
    frame_area = image_width * image_height
    if area < frame_area * 0.002:
        return {"valid": False, "reason": "BBOX_TOO_SMALL"}
    if area > frame_area * 0.92:
        return {"valid": False, "reason": "BBOX_TOO_LARGE_FULL_FRAME"}
    return {"valid": True, "bbox_xyxy": [round(x1, 2), round(y1, 2), round(x2, 2), round(y2, 2)]}


def choose_best_tree_bbox(
    yolo_bbox: list[float] | None,
    ai_candidates: list[dict[str, Any]],
    *,
    image_width: int,
    image_height: int,
) -> dict[str, Any]:
    if yolo_bbox:
        yolo_candidate = {"bbox_xyxy": yolo_bbox, "provider": "yolo"}
        validity = validate_ai_bbox(yolo_candidate, image_width, image_height)
        if validity.get("valid"):
            return {"source": "YOLOV8_LOCAL", "bbox_xyxy": validity["bbox_xyxy"]}
    valid_ai: list[tuple[float, dict[str, Any], list[float]]] = []
    for candidate in ai_candidates:
        validity = validate_ai_bbox(candidate, image_width, image_height)
        if not validity.get("valid"):
            continue
        conf = float(candidate.get("confidence") or 0.0)
        if candidate.get("tree_visible") is False:
            conf -= 0.3
        valid_ai.append((conf, candidate, validity["bbox_xyxy"]))
    if valid_ai:
        valid_ai.sort(key=lambda item: item[0], reverse=True)
        return {"source": "AI_CONSENSUS", "bbox_xyxy": valid_ai[0][2], "provider": valid_ai[0][1].get("provider")}
    return {"source": "NONE", "bbox_xyxy": None}


def build_ai_consensus_summary(provider_results: list[dict[str, Any]]) -> dict[str, Any]:
    enabled = [item.get("provider") for item in provider_results if item.get("status") != "SKIPPED_NO_KEY"]
    statuses = [{"provider": item.get("provider"), "status": item.get("status")} for item in provider_results]
    ok_results = [item for item in provider_results if item.get("status") == "OK"]
    zone_votes = [str(item.get("risk_zone_guess") or "REVIEW_REQUIRED") for item in ok_results]
    risk_zone = _majority(zone_votes) if zone_votes else "REVIEW_REQUIRED"
    tree_votes = [item.get("tree_visible") for item in ok_results if item.get("tree_visible") is not None]
    retake = next((str(item.get("retake_recommendation") or "") for item in ok_results if item.get("retake_recommendation")), "")
    return {
        "providers_enabled": enabled,
        "provider_statuses": statuses,
        "ok_count": len(ok_results),
        "risk_zone_guess": _normalize_zone(risk_zone),
        "tree_visible_consensus": _majority_bool(tree_votes),
        "retake_recommendation": retake,
        "false_positive_likelihood_mean": _mean_conf(ok_results, "false_positive_likelihood"),
        "false_negative_likelihood_mean": _mean_conf(ok_results, "false_negative_likelihood"),
        "confidence_adjustment_mean": _mean_adjustment(ok_results),
        "image_quality_flags": sorted(
            {
                flag
                for item in ok_results
                for flag in (item.get("image_quality_flags") or [])
                if isinstance(flag, str) and flag
            }
        ),
    }


def _build_prompt(context: dict[str, Any]) -> str:
    return (
        "Return strict JSON only. No prose outside JSON. "
        "Plan C uses a local YOLOv8 System C detector for pohon_sono, conductor, and support structure. "
        "You are a visual validator and second opinion, not the final bounding-box detector. "
        "Identify whether the main tree appears pohon_sono/angsana-like and whether YOLO detections look plausible. "
        "Do not create final conductor or pole bounding boxes. If you provide bbox, provide the main tree bbox only. "
        "Estimate whether canopy intersects the upper electrical-risk area and flag possible false positives or false negatives. "
        "Use pixel bbox [x1,y1,x2,y2] if confident; otherwise bbox_xyxy must be null. "
        "If unsure return REVIEW_REQUIRED. "
        f"Image size: {context.get('image_width')}x{context.get('image_height')}. "
        "Schema: {\"tree_visible\":true|false|null,\"tree_species_guess\":\"pohon_sono|unknown\","
        "\"risk_zone_guess\":\"ZONA_TEBANG|ZONA_PANTAU|ZONA_AMAN|REVIEW_REQUIRED\","
        "\"bbox_xyxy\":[x1,y1,x2,y2]|null,\"confidence\":0.0,\"reason\":\"short\","
        "\"false_positive_likelihood\":0.0,\"false_negative_likelihood\":0.0,"
        "\"confidence_adjustment\":-0.2,\"bbox_sanity\":\"OK|SUSPICIOUS|REVIEW_REQUIRED\","
        "\"image_quality_flags\":[\"blur|dark|low_contrast|backlight|rain|fog|low_resolution\"],"
        "\"retake_recommendation\":\"short\"}"
    )


def _chat_vision_payload(model: str, image_path: Path | str, context: dict[str, Any]) -> dict[str, Any]:
    data_url = f"data:image/jpeg;base64,{encode_image_base64(image_path)}"
    return {
        "model": model,
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": _build_prompt(context)},
                    {"type": "image_url", "image_url": {"url": data_url}},
                ],
            }
        ],
        "temperature": 0.1,
        "response_format": {"type": "json_object"},
    }


def _post_json(url: str, payload: dict[str, Any], *, headers: dict[str, str]) -> dict[str, Any]:
    data = json.dumps(payload).encode("utf-8")
    req = request.Request(url, data=data, headers=headers, method="POST")
    try:
        with request.urlopen(req, timeout=DEFAULT_TIMEOUT_SECONDS) as response:
            body = response.read().decode("utf-8", errors="replace")
            return {"status": "OK", "json": json.loads(body)}
    except error.HTTPError as exc:
        if exc.code == 429:
            status = "RATE_LIMIT"
        elif exc.code in {401, 403}:
            status = "AUTH_ERROR"
        elif exc.code == 400:
            status = "MODEL_UNSUPPORTED_OR_BAD_REQUEST"
        else:
            status = "HTTP_ERROR"
        preview = ""
        try:
            preview = exc.read().decode("utf-8", errors="replace")[:500]
        except Exception:
            preview = ""
        return {"status": status, "http_status": exc.code, "error": str(exc), "body_preview": preview}
    except (TimeoutError, socket.timeout):
        return {"status": "TIMEOUT", "error": "provider timeout"}
    except Exception as exc:
        return {"status": "HTTP_ERROR", "error": f"{type(exc).__name__}: {exc}"}


def _chat_text(raw: dict[str, Any]) -> str:
    try:
        return str(raw["json"]["choices"][0]["message"]["content"])
    except (KeyError, IndexError, TypeError):
        return ""


def _provider_result(provider: str, status: str, *, reason: str = "", raw: dict[str, Any] | None = None) -> dict[str, Any]:
    return {
        "provider": provider,
        "status": status,
        "tree_visible": None,
        "tree_species_guess": "unknown",
        "risk_zone_guess": "REVIEW_REQUIRED",
        "bbox_xyxy": None,
        "confidence": 0.0,
        "reason": reason,
        "retake_recommendation": "",
        "false_positive_likelihood": 0.0,
        "false_negative_likelihood": 0.0,
        "confidence_adjustment": 0.0,
        "image_quality_flags": [],
        "bbox_sanity": "REVIEW_REQUIRED",
        "raw_redacted": _redact_raw(raw or {}),
    }


def _extract_json_object(text: str) -> dict[str, Any]:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        if cleaned.lower().startswith("json"):
            cleaned = cleaned[4:].strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start >= 0 and end > start:
            return json.loads(cleaned[start : end + 1])
    raise ValueError("provider response is not valid JSON")


def _normalize_bbox(value: Any) -> list[float] | None:
    if not isinstance(value, list) or len(value) != 4:
        return None
    try:
        return [float(item) for item in value]
    except (TypeError, ValueError):
        return None


def _normalize_zone(value: Any) -> str:
    text = str(value or "").strip().upper()
    if text in {"ZONA_TEBANG", "ZONA_PANTAU", "ZONA_AMAN", "REVIEW_REQUIRED"}:
        return text
    if text in {"TEBANG", "DANGER"}:
        return "ZONA_TEBANG"
    if text in {"PANTAU", "WATCH"}:
        return "ZONA_PANTAU"
    if text in {"AMAN", "SAFE"}:
        return "ZONA_AMAN"
    return "REVIEW_REQUIRED"


def _clamp_confidence(value: Any) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return 0.0
    return round(max(0.0, min(1.0, number)), 4)


def _clamp_adjustment(value: Any) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return 0.0
    return round(max(-0.25, min(0.25, number)), 4)


def _normalize_string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    output = []
    for item in value:
        text = str(item or "").strip().lower()
        if text:
            output.append(text[:60])
    return output[:12]


def _mean_conf(items: list[dict[str, Any]], key: str) -> float:
    values = [float(item.get(key) or 0.0) for item in items if isinstance(item, dict)]
    if not values:
        return 0.0
    return round(sum(values) / len(values), 4)


def _mean_adjustment(items: list[dict[str, Any]]) -> float:
    values = [float(item.get("confidence_adjustment") or 0.0) for item in items if isinstance(item, dict)]
    if not values:
        return 0.0
    return round(sum(values) / len(values), 4)


def _to_optional_bool(value: Any) -> bool | None:
    if isinstance(value, bool):
        return value
    text = str(value or "").strip().lower()
    if text in {"true", "1", "yes"}:
        return True
    if text in {"false", "0", "no"}:
        return False
    return None


def _redact_raw(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        return {"preview": str(value)[:200]}
    redacted: dict[str, Any] = {}
    for key, item in value.items():
        lowered = str(key).lower()
        if any(token in lowered for token in ("key", "token", "authorization", "base64", "image")):
            redacted[key] = "[REDACTED]"
        elif isinstance(item, (str, int, float, bool)) or item is None:
            redacted[key] = item if not isinstance(item, str) or len(item) <= 240 else item[:240]
        elif isinstance(item, list):
            redacted[key] = f"[list:{len(item)}]"
        elif isinstance(item, dict):
            redacted[key] = "[object]"
        else:
            redacted[key] = str(type(item).__name__)
    return redacted


def _redact_detection_list(detections: list[dict[str, Any]]) -> list[dict[str, Any]]:
    safe = []
    for item in detections:
        if not isinstance(item, dict):
            continue
        safe.append(
            {
                "class_name": item.get("class_name"),
                "confidence": item.get("confidence"),
                "bbox_xyxy": item.get("bbox_xyxy"),
                "source": item.get("source"),
            }
        )
    return safe[:10]


def _best_yolo_bbox(detections: list[dict[str, Any]]) -> list[float] | None:
    candidates = [item for item in detections if item.get("class_name") == "pohon_sono" and isinstance(item.get("bbox_xyxy"), list)]
    if not candidates:
        return None
    best = max(candidates, key=lambda item: float(item.get("confidence") or 0.0))
    bbox = best.get("bbox_xyxy")
    return [float(value) for value in bbox] if isinstance(bbox, list) and len(bbox) == 4 else None


def _majority(values: list[str]) -> str:
    if not values:
        return "REVIEW_REQUIRED"
    counts: dict[str, int] = {}
    for value in values:
        counts[value] = counts.get(value, 0) + 1
    return sorted(counts.items(), key=lambda item: (-item[1], item[0]))[0][0]


def _majority_bool(values: list[bool]) -> bool | None:
    if not values:
        return None
    return values.count(True) >= values.count(False)


def _read_image_size(path: Path | str) -> tuple[int, int]:
    try:
        from PIL import Image

        with Image.open(path) as image:
            return int(image.width), int(image.height)
    except Exception:
        return 0, 0
