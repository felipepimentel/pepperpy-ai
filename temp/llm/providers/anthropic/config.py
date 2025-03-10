"""Configuration for the Anthropic provider.

This module defines configuration classes and constants for the Anthropic provider.
"""

from dataclasses import dataclass, field
from typing import Dict

from pepperpy.config import ConfigModel


@dataclass
class AnthropicModelConfig:
    """Configuration for an Anthropic model.

    Attributes:
        name: The name of the model
        max_tokens: The maximum number of tokens the model can process
        supports_vision: Whether the model supports vision inputs
        default_temperature: The default temperature to use with this model
    """

    name: str
    max_tokens: int
    supports_vision: bool = False
    default_temperature: float = 0.7


@dataclass
class AnthropicConfig(ConfigModel):
    """Configuration for the Anthropic provider.

    Attributes:
        api_key: The Anthropic API key
        base_url: The base URL for the Anthropic API
        timeout: The timeout for API requests in seconds
        default_model: The default model to use
        models: A dictionary of model configurations
        retry_count: The number of times to retry failed requests
        retry_base_delay: The base delay between retries in seconds
        retry_max_delay: The maximum delay between retries in seconds
    """

    api_key: str
    base_url: str = "https://api.anthropic.com"
    timeout: float = 60.0
    default_model: str = "claude-3-opus-20240229"
    models: Dict[str, AnthropicModelConfig] = field(default_factory=dict)
    retry_count: int = 3
    retry_base_delay: float = 1.0
    retry_max_delay: float = 60.0

    def __post_init__(self):
        """Initialize default models if none are provided."""
        if not self.models:
            self.models = {
                "claude-3-opus-20240229": AnthropicModelConfig(
                    name="claude-3-opus-20240229",
                    max_tokens=200000,
                    supports_vision=True,
                ),
                "claude-3-sonnet-20240229": AnthropicModelConfig(
                    name="claude-3-sonnet-20240229",
                    max_tokens=200000,
                    supports_vision=True,
                ),
                "claude-3-haiku-20240307": AnthropicModelConfig(
                    name="claude-3-haiku-20240307",
                    max_tokens=200000,
                    supports_vision=True,
                ),
                "claude-2.1": AnthropicModelConfig(
                    name="claude-2.1",
                    max_tokens=200000,
                ),
                "claude-2.0": AnthropicModelConfig(
                    name="claude-2.0",
                    max_tokens=100000,
                ),
                "claude-instant-1.2": AnthropicModelConfig(
                    name="claude-instant-1.2",
                    max_tokens=100000,
                ),
            }


# Default configuration
DEFAULT_CONFIG = AnthropicConfig(api_key="")


def get_config() -> AnthropicConfig:
    """Get the Anthropic configuration.

    Returns:
        The Anthropic configuration
    """
    from pepperpy.config import get_config as get_global_config

    config = get_global_config()
    anthropic_config = config.get("llm.providers.anthropic", DEFAULT_CONFIG)

    if isinstance(anthropic_config, dict):
        return AnthropicConfig(**anthropic_config)

    return anthropic_config
