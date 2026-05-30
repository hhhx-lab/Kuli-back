from __future__ import annotations

import httpx

from app.core.config import get_settings


def remote_llm_enabled() -> bool:
    settings = get_settings()
    return bool(settings.effective_llm_api_key and settings.effective_llm_model != "local-rules")


def complete_chat(system: str, messages: list[dict[str, str]]) -> str | None:
    settings = get_settings()
    if not remote_llm_enabled():
        return None
    try:
        url = settings.effective_llm_base_url.rstrip("/") + "/chat/completions"
        payload = {
            "model": settings.effective_llm_model,
            "messages": [{"role": "system", "content": system}, *messages],
            "temperature": 0.3,
        }
        headers = {"Authorization": f"Bearer {settings.effective_llm_api_key}", "Content-Type": "application/json"}
        response = httpx.post(url, headers=headers, json=payload, timeout=settings.llm_timeout_seconds)
        response.raise_for_status()
        body = response.json()
        return body["choices"][0]["message"]["content"]
    except (httpx.HTTPError, KeyError, IndexError, TypeError):
        return None
