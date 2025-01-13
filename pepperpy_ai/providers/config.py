"""Provider configuration module."""

import os
from dataclasses import dataclass
from typing import Any, TypedDict

from .exceptions import ProviderError


class ProviderConfig(TypedDict):
    """Base provider configuration."""

    model: str


@dataclass
class ProviderSettings:
    """Provider settings."""

    name: str
    api_key: str
    config: dict[str, Any]

    @classmethod
    def from_env(cls, prefix: str = "") -> "ProviderSettings":
        """Create provider settings from environment variables.

        The following environment variables are used:
        - {prefix}PROVIDER: Provider name (default: openrouter)
        - {prefix}API_KEY: API key
        - {prefix}MODEL: Model name (default: depends on provider)
        - {prefix}TEMPERATURE: Temperature (default: 0.7)
        - {prefix}MAX_TOKENS: Max tokens (default: 1000)
        - {prefix}TIMEOUT: Timeout in seconds (default: 30.0)

        Args:
            prefix: Environment variable prefix (e.g., "PEPPERPY_")

        Returns:
            Provider settings

        Raises:
            ProviderError: If required environment variables are missing
        """
        # Get provider name (default to openrouter)
        provider = os.getenv(f"{prefix}PROVIDER", "openrouter").lower()

        # Get API key
        api_key = os.getenv(f"{prefix}API_KEY", "").strip()
        if not api_key:
            raise ProviderError(
                f"Missing {prefix}API_KEY environment variable",
                provider=provider,
                operation="config",
            )

        # Get model name
        model = os.getenv(f"{prefix}MODEL", "")
        if not model:
            # Default models per provider
            model = {
                "openai": "gpt-3.5-turbo",
                "anthropic": "claude-2.1",
                "openrouter": "anthropic/claude-2",
                "mock": "mock",
            }.get(provider, "")

        # Build config
        config = {
            "model": model,
            "temperature": float(os.getenv(f"{prefix}TEMPERATURE", "0.7")),
            "max_tokens": int(os.getenv(f"{prefix}MAX_TOKENS", "1000")),
            "timeout": float(os.getenv(f"{prefix}TIMEOUT", "30.0")),
        }

        return cls(
            name=provider,
            api_key=api_key,
            config=config,
        )

    def get_env_help(self, prefix: str = "") -> str:
        """Get help text for environment variables.

        Args:
            prefix: Environment variable prefix

        Returns:
            Help text
        """
        return f"""
Required environment variables:
    {prefix}API_KEY: API key for the provider

Optional environment variables:
    {prefix}PROVIDER: Provider name (default: openrouter)
        Supported providers: openai, anthropic, openrouter, mock
    {prefix}MODEL: Model name (provider-specific defaults)
        OpenAI: gpt-3.5-turbo
        Anthropic: claude-2.1
        OpenRouter: anthropic/claude-2
    {prefix}TEMPERATURE: Temperature (default: 0.7)
    {prefix}MAX_TOKENS: Max tokens (default: 1000)
    {prefix}TIMEOUT: Timeout in seconds (default: 30.0)
"""
