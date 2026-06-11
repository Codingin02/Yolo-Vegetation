"""Free-only vision adapter configuration for Plan C."""

from __future__ import annotations

import os
from typing import Any

PROVIDER_ENV = {
    "gemini": ("GEMINI_API_KEY", "GEMINI_VISION_MODEL", "gemini-2.5-flash"),
    "groq": ("GROQ_API_KEY", "GROQ_VISION_MODEL", "meta-llama/llama-4-scout-17b-16e-instruct"),
    "openrouter": ("OPENROUTER_API_KEY", "OPENROUTER_VISION_MODEL", ""),
}

PROVIDER_ROLE_ENV = {
    "primary": "PLAN_C_FREE_VISION_PRIMARY",
    "secondary": "PLAN_C_FREE_VISION_SECONDARY",
    "tertiary": "PLAN_C_FREE_VISION_TERTIARY",
}


def load_free_vision_config() -> dict[str, Any]:
    mode = os.environ.get("PLAN_C_VISION_MODE", "free_only").strip() or "free_only"
    operator_hide_provider = _to_bool(os.environ.get("PLAN_C_OPERATOR_HIDE_PROVIDER", "true"), default=True)
    providers: dict[str, dict[str, Any]] = {}
    order: list[str] = []
    for role, env_name in PROVIDER_ROLE_ENV.items():
        provider_name = _normalize_provider(os.environ.get(env_name, _default_provider_for_role(role)))
        provider = _provider_config(provider_name, role)
        providers[role] = provider
        order.append(role)
    return {
        "status": "PLAN_C_FREE_VISION_CONFIG_READY",
        "mode": mode,
        "free_only": mode == "free_only",
        "operator_hide_provider": operator_hide_provider,
        "provider_order": order,
        "providers": providers,
        "openrouter_free_only": _to_bool(os.environ.get("OPENROUTER_FREE_ONLY", "true"), default=True),
    }


def redact_secret(value: Any) -> Any:
    if value in {None, ""}:
        return ""
    text = str(value)
    if len(text) <= 4:
        return "[REDACTED]"
    return f"{text[:2]}...[REDACTED]...{text[-2:]}"


def redact_config(config: dict[str, Any]) -> dict[str, Any]:
    redacted = dict(config)
    providers: dict[str, Any] = {}
    for role, provider in (config.get("providers") or {}).items():
        provider_dict = dict(provider or {})
        provider_dict["name"] = "redacted" if provider_dict.get("name") else ""
        provider_dict["api_key"] = redact_secret(provider_dict.get("api_key"))
        provider_dict["configured"] = bool(provider_dict.get("configured"))
        providers[role] = provider_dict
    redacted["providers"] = providers
    return redacted


def is_free_only_mode() -> bool:
    return load_free_vision_config().get("mode") == "free_only"


def _provider_config(provider_name: str, role: str) -> dict[str, Any]:
    env = PROVIDER_ENV.get(provider_name)
    if not env:
        return {
            "role": role,
            "name": provider_name,
            "model": "",
            "api_key": "",
            "configured": False,
            "status": "FREE_VISION_NOT_CONFIGURED",
            "free_only": True,
        }
    key_env, model_env, default_model = env
    api_key = os.environ.get(key_env, "")
    model = os.environ.get(model_env, default_model).strip()
    configured = bool(api_key and model)
    status = "FREE_VISION_CONFIGURED" if configured else "FREE_VISION_KEY_MISSING"
    if api_key and not model:
        status = "FREE_VISION_NOT_CONFIGURED"
    return {
        "role": role,
        "name": provider_name,
        "model": model,
        "api_key": api_key,
        "configured": configured,
        "status": status,
        "free_only": True,
    }


def _default_provider_for_role(role: str) -> str:
    return {"primary": "gemini", "secondary": "groq", "tertiary": "openrouter"}.get(role, "")


def _normalize_provider(value: str | None) -> str:
    text = str(value or "").strip().lower()
    if text in {"gemini", "groq", "openrouter"}:
        return text
    return ""


def _to_bool(value: Any, *, default: bool) -> bool:
    if value is None:
        return default
    text = str(value).strip().lower()
    if text in {"1", "true", "yes", "on"}:
        return True
    if text in {"0", "false", "no", "off"}:
        return False
    return default
