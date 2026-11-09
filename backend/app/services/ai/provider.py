"""Optional AI provider abstraction (OpenAI-compatible APIs)."""
from __future__ import annotations

import logging
from dataclasses import dataclass

import httpx

from app.core.config import settings

logger = logging.getLogger("codeguard.ai")


class AIError(Exception):
    """Raised when an AI request fails or is not configured."""


@dataclass
class ProviderConfig:
    provider: str
    base_url: str
    api_key: str
    model: str

    @property
    def name(self) -> str:
        return self.provider or "openai-compatible"


def resolve_config(settings_row=None) -> ProviderConfig | None:
    """Resolve the AI configuration from user settings, falling back to env vars.

    API keys are only ever read from the backend environment, never from the
    frontend or the database.
    """
    if settings_row is not None and settings_row.ai_enabled:
        if settings.ai_api_key and settings_row.ai_base_url and settings_row.ai_model:
            return ProviderConfig(
                provider=settings_row.ai_provider or settings.ai_provider or "openai-compatible",
                base_url=settings_row.ai_base_url,
                api_key=settings.ai_api_key,  # key always comes from the backend env
                model=settings_row.ai_model,
            )
    if settings.ai_configured:
        return ProviderConfig(
            provider=settings.ai_provider or "openai-compatible",
            base_url=settings.ai_base_url,
            api_key=settings.ai_api_key,
            model=settings.ai_model,
        )
    return None


def is_available(settings_row=None) -> bool:
    return resolve_config(settings_row) is not None


def chat(messages: list[dict], config: ProviderConfig, temperature: float = 0.2, max_tokens: int = 900) -> str:
    """Send a chat-completion request to an OpenAI-compatible endpoint."""
    url = config.base_url.rstrip("/") + "/chat/completions"
    payload = {
        "model": config.model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "stream": False,
    }
    headers = {
        "Authorization": f"Bearer {config.api_key}",
        "Content-Type": "application/json",
    }
    try:
        with httpx.Client(timeout=60.0) as client:
            resp = client.post(url, json=payload, headers=headers)
    except httpx.HTTPError as exc:
        raise AIError(f"Could not reach AI provider: {exc}") from exc

    if resp.status_code == 429:
        raise AIError("AI provider rate limit reached. Try again later or use offline mode.")
    if resp.status_code in (401, 403):
        raise AIError("AI provider rejected the API key (check backend configuration).")
    if resp.status_code >= 400:
        raise AIError(f"AI provider error {resp.status_code}: {resp.text[:200]}")

    try:
        data = resp.json()
        return data["choices"][0]["message"]["content"].strip()
    except (KeyError, IndexError, ValueError) as exc:
        raise AIError("Unexpected response format from AI provider.") from exc


def test_provider(config: ProviderConfig) -> str:
    return chat(
        [
            {"role": "system", "content": "You are a concise assistant."},
            {"role": "user", "content": "Reply with exactly: CodeGuard AI connection OK"},
        ],
        config,
        max_tokens=256,
    )
