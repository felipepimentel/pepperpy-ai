"""LLM factory module."""

from typing import cast

from ..providers.anthropic import AnthropicProvider
from ..providers.base import BaseProvider
from ..providers.config import ProviderConfig
from ..providers.openai import OpenAIProvider
from ..providers.openrouter import OpenRouterProvider
from ..providers.stackspot import StackSpotProvider
from .config import LLMConfig


class LLMFactory:
    """LLM factory class."""

    @staticmethod
    def create_provider(config: LLMConfig) -> BaseProvider:
        """Create LLM provider.

        Args:
            config: LLM configuration.

        Returns:
            LLM provider.

        Raises:
            ValueError: If provider type is not supported.
        """
        provider_type = config.get("provider_type", "openai")
        provider_config = {
            "name": provider_type,
            "version": "latest",
            "model": config.get("model", "gpt-4"),
            "api_key": config.get("api_key", ""),
            "api_base": config.get("api_base", ""),
            "api_version": config.get("api_version"),
            "organization": config.get("organization"),
            "temperature": config.get("temperature", 0.0),
            "max_tokens": config.get("max_tokens", 100),
            "top_p": config.get("top_p", 1.0),
            "frequency_penalty": config.get("frequency_penalty", 0.0),
            "presence_penalty": config.get("presence_penalty", 0.0),
            "timeout": config.get("timeout", 30.0),
            "enabled": config.get("enabled", True),
        }

        if provider_type == "openai":
            return OpenAIProvider(cast(ProviderConfig, provider_config))
        elif provider_type == "anthropic":
            return AnthropicProvider(cast(ProviderConfig, provider_config))
        elif provider_type == "openrouter":
            return OpenRouterProvider(cast(ProviderConfig, provider_config))
        elif provider_type == "stackspot":
            return StackSpotProvider(cast(ProviderConfig, provider_config))
        else:
            raise ValueError(f"Unsupported provider type: {provider_type}")
