"""AI module. One port (base.Provider), one adapter per API shape, picked by env.

    AI_PROVIDER=ollama     -> local, default (OpenAI-compatible API)
    AI_PROVIDER=openai     -> production
    AI_PROVIDER=anthropic  -> Claude

Adding a provider means adding one adapter and one line in PROVIDERS. Nothing
else in the app knows which model is running.
"""

import os
from functools import lru_cache

from .base import AIError, Attachment, Message, parse_upload
from .anthropic_provider import AnthropicProvider
from .openai_provider import OpenAICompatProvider

__all__ = ["AIError", "Attachment", "Message", "parse_upload", "run_chat", "provider_name"]


def _flag(name: str, default: bool) -> bool:
    return os.environ.get(name, "1" if default else "0").strip().lower() in ("1", "true", "yes")


PROVIDERS = {
    "ollama": lambda: OpenAICompatProvider(
        name="ollama",
        model=os.environ.get("OLLAMA_MODEL", "glm-4.7-flash:latest"),
        api_key="ollama",  # Ollama ignores it, the SDK requires a non-empty value
        base_url=os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434/v1"),
        # Most local text models cannot read images. Set AI_VISION=1 for one that can.
        supports_images=_flag("AI_VISION", False),
    ),
    "openai": lambda: OpenAICompatProvider(
        name="openai",
        model=os.environ.get("OPENAI_MODEL", ""),
        api_key=os.environ.get("OPENAI_API_KEY", ""),
        base_url=os.environ.get("OPENAI_BASE_URL") or None,
        supports_images=_flag("AI_VISION", True),
    ),
    "anthropic": lambda: AnthropicProvider(
        name="anthropic",
        model=os.environ.get("ANTHROPIC_MODEL", "claude-opus-5"),
        api_key=os.environ.get("ANTHROPIC_API_KEY", ""),
    ),
}


def provider_name() -> str:
    return os.environ.get("AI_PROVIDER", "ollama").strip().lower()


@lru_cache(maxsize=len(PROVIDERS))
def _provider(name: str):
    build = PROVIDERS.get(name)
    if build is None:
        raise AIError(f"Unknown AI_PROVIDER '{name}'. Use one of: {', '.join(PROVIDERS)}")
    return build()


def run_chat(history: list[Message], message: str, attachments: list[Attachment]) -> str:
    """Run one assistant turn on the configured provider."""
    return _provider(provider_name()).run(history, message, attachments)
