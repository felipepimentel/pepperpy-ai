"""AI provider factory."""

from ..exceptions import PepperpyError
from ..llm.config import LLMConfig
from .base import BaseProvider

# Import providers conditionally to handle optional dependencies
_PROVIDERS: dict[str, type[BaseProvider[LLMConfig]]] = {}

# Optional Anthropic provider
try:
    from .anthropic import AnthropicProvider

    _PROVIDERS["anthropic"] = AnthropicProvider
except ImportError:
    pass

# Optional OpenAI provider
try:
    from .openai import OpenAIProvider

    _PROVIDERS["openai"] = OpenAIProvider
except ImportError:
    pass


class AIProviderFactory:
    """Factory for creating AI providers."""

    _provider_map: dict[str, type[BaseProvider[LLMConfig]]] = _PROVIDERS

    @classmethod
    def create_provider(cls, config: LLMConfig) -> BaseProvider[LLMConfig]:
        """Create provider instance.

        Args:
            config: Provider configuration

        Returns:
            Provider instance

        Raises:
            PepperpyError: If provider creation fails
        """
        try:
            if config.provider not in cls._provider_map:
                raise PepperpyError(f"Unsupported provider type: {config.provider}")

            provider_class = cls._provider_map[config.provider]
            return provider_class(config)

        except Exception as e:
            raise PepperpyError(f"Failed to create provider: {e}", cause=e)

    @classmethod
    def get_supported_providers(cls) -> list[str]:
        """Get list of supported provider types."""
        return list(cls._provider_map.keys())
