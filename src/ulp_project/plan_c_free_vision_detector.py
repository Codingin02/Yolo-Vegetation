"""Aggregator for local YOLO and optional free vision Plan C detection."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .plan_c_free_vision_config import load_free_vision_config, redact_config
from .plan_c_free_vision_consensus import build_detection_consensus
from .plan_c_free_vision_gemini import detect_with_gemini
from .plan_c_free_vision_groq import detect_with_groq
from .plan_c_free_vision_openrouter import detect_with_openrouter
from .plan_c_free_vision_schema import empty_detection_result, normalize_yolo_detections


def detect_yolo_compatible_from_snapshot(
    image_path: Path,
    image_width: int,
    image_height: int,
    config: dict[str, Any] | None = None,
    *,
    yolo_result: dict[str, Any] | None = None,
) -> dict[str, Any]:
    config = config or load_free_vision_config()
    provider_status: list[dict[str, Any]] = []
    yolo_candidate = normalize_yolo_detections(
        list((yolo_result or {}).get("detections") or []),
        image_width=image_width,
        image_height=image_height,
        source_internal="local_yolo",
    )
    if yolo_candidate.get("detections"):
        return {
            **yolo_candidate,
            "pipeline_status": "YOLO_LOCAL_USED",
            "provider_status_redacted": _status_from_config(config),
            "provider_order": ["local_yolo"],
            "provider_errors_redacted": [],
            "raw_response_redacted": [],
        }

    provider_status.append({"role": "local_yolo", "status": "YOLO_LOCAL_EMPTY_FALLBACK_USED", "configured": bool(yolo_result)})
    if config.get("mode") != "free_only":
        return _disabled(image_width, image_height, provider_status, "FREE_VISION_NOT_CONFIGURED")

    candidates: list[dict[str, Any]] = []
    provider_errors: list[dict[str, Any]] = []
    raw_responses: list[dict[str, Any]] = []
    for role in config.get("provider_order", ["primary", "secondary", "tertiary"]):
        provider = dict((config.get("providers") or {}).get(role) or {})
        provider["role"] = role
        if not provider.get("configured"):
            provider_status.append({"role": role, "status": provider.get("status", "FREE_VISION_KEY_MISSING"), "configured": False, "source_internal": "redacted_provider"})
            continue
        result = _run_provider(image_path, image_width=image_width, image_height=image_height, provider=provider, free_only=bool(config.get("openrouter_free_only", True)))
        result["role"] = role
        candidates.append(result)
        provider_status.append({"role": role, "status": _used_status(role, result), "configured": True, "detection_count": len(result.get("detections", []) or []), "source_internal": "redacted_provider"})
        if result.get("error_redacted"):
            provider_errors.append({"role": role, "error_redacted": result.get("error_redacted")})
        if result.get("raw_response_redacted"):
            raw_responses.append({"role": role, "raw_response_redacted": result.get("raw_response_redacted")})
        if result.get("detections") and not _needs_fallback(result):
            break

    if not candidates and not any(item.get("configured") for item in provider_status if item.get("role") != "local_yolo"):
        return _disabled(image_width, image_height, provider_status, "FREE_VISION_ALL_DISABLED")
    consensus = build_detection_consensus(candidates, image_width=image_width, image_height=image_height)
    pipeline_status = "DATA_TIDAK_CUKUP" if not consensus.get("detections") else "FREE_VISION_PRIMARY_USED"
    for item in provider_status:
        if item.get("status") in {"FREE_VISION_SECONDARY_USED", "FREE_VISION_TERTIARY_USED"} and item.get("detection_count", 0) > 0:
            pipeline_status = str(item["status"])
    return {
        **consensus,
        "pipeline_status": pipeline_status,
        "provider_status_redacted": provider_status,
        "provider_order": list(config.get("provider_order", [])),
        "provider_errors_redacted": provider_errors,
        "raw_response_redacted": raw_responses,
    }


def build_free_vision_status_payload(config: dict[str, Any] | None = None) -> dict[str, Any]:
    config = config or load_free_vision_config()
    redacted = redact_config(config)
    providers = {}
    for role, provider in (redacted.get("providers") or {}).items():
        providers[role] = {
            "name": "redacted",
            "configured": bool(provider.get("configured")),
            "free_only": True,
        }
    return {
        "ok": True,
        "status": "PLAN_C_FREE_VISION_STATUS_READY",
        "mode": redacted.get("mode", "free_only"),
        "operator_hide_provider": True,
        "providers": providers,
    }


def _run_provider(image_path: Path, *, image_width: int, image_height: int, provider: dict[str, Any], free_only: bool) -> dict[str, Any]:
    name = provider.get("name")
    if name == "gemini":
        return detect_with_gemini(image_path, image_width=image_width, image_height=image_height, provider_config=provider)
    if name == "groq":
        return detect_with_groq(image_path, image_width=image_width, image_height=image_height, provider_config=provider)
    if name == "openrouter":
        return detect_with_openrouter(image_path, image_width=image_width, image_height=image_height, provider_config=provider, free_only=free_only)
    return empty_detection_result(status="FREE_VISION_NOT_CONFIGURED", image_width=image_width, image_height=image_height, consensus_status="disabled")


def _needs_fallback(result: dict[str, Any]) -> bool:
    detections = result.get("detections") or []
    if not detections:
        return True
    return any(float(item.get("confidence") or 0) < 0.45 for item in detections)


def _used_status(role: str, result: dict[str, Any]) -> str:
    if not result.get("detections"):
        return str(result.get("status") or "DATA_TIDAK_CUKUP")
    return {"primary": "FREE_VISION_PRIMARY_USED", "secondary": "FREE_VISION_SECONDARY_USED", "tertiary": "FREE_VISION_TERTIARY_USED"}.get(role, "FREE_VISION_PRIMARY_USED")


def _disabled(image_width: int, image_height: int, provider_status: list[dict[str, Any]], status: str) -> dict[str, Any]:
    return {
        **empty_detection_result(status="DATA_TIDAK_CUKUP", image_width=image_width, image_height=image_height, provider_status_redacted=provider_status),
        "pipeline_status": status,
        "provider_order": [],
        "provider_errors_redacted": [],
        "raw_response_redacted": [],
    }


def _status_from_config(config: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {"role": role, "status": provider.get("status"), "configured": bool(provider.get("configured")), "source_internal": "redacted_provider"}
        for role, provider in (config.get("providers") or {}).items()
    ]
