"""LLM client factory."""

from ..exceptions import ConfigError
from .base import LLMClient
from .config import LLMConfig

# Import providers conditionally to handle optional dependencies
PROVIDERS: dict[str, type[LLMClient]] = {}

# Optional Anthropic provider
try:
    from ..providers.anthropic import AnthropicProvider

    PROVIDERS["anthropic"] = AnthropicProvider
except ImportError:
    pass

# Optional OpenAI provider
try:
    from ..providers.openai import OpenAIProvider

    PROVIDERS["openai"] = OpenAIProvider
except ImportError:
    pass


def create_llm_client(config: LLMConfig) -> LLMClient:
    """Create LLM client from config."""
    provider_class = PROVIDERS.get(config.provider)
    if provider_class is None:
        raise ConfigError(
            f"Unsupported LLM provider: {config.provider}. "
            f"Supported providers: {', '.join(PROVIDERS.keys())}"
        )

    return provider_class(config)
