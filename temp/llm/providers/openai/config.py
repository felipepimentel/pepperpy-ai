"""Configuration for the OpenAI provider.

This module defines configuration classes and constants for the OpenAI provider.
"""

from dataclasses import dataclass, field
from typing import Dict, Optional

from pepperpy.config import ConfigModel


@dataclass
class OpenAIModelConfig:
    """Configuration for an OpenAI model.

    Attributes:
        name: The name of the model
        max_tokens: The maximum number of tokens the model can process
        supports_functions: Whether the model supports function calling
        supports_vision: Whether the model supports vision inputs
        default_temperature: The default temperature to use with this model
    """

    name: str
    max_tokens: int
    supports_functions: bool = False
    supports_vision: bool = False
    default_temperature: float = 0.7


@dataclass
class OpenAIConfig(ConfigModel):
    """Configuration for the OpenAI provider.

    Attributes:
        api_key: The OpenAI API key
        organization_id: The OpenAI organization ID
        base_url: The base URL for the OpenAI API
        timeout: The timeout for API requests in seconds
        default_model: The default model to use
        models: A dictionary of model configurations
        retry_count: The number of times to retry failed requests
        retry_base_delay: The base delay between retries in seconds
        retry_max_delay: The maximum delay between retries in seconds
    """

    api_key: str
    organization_id: Optional[str] = None
    base_url: str = "https://api.openai.com/v1"
    timeout: float = 60.0
    default_model: str = "gpt-3.5-turbo"
    models: Dict[str, OpenAIModelConfig] = field(default_factory=dict)
    retry_count: int = 3
    retry_base_delay: float = 1.0
    retry_max_delay: float = 60.0

    def __post_init__(self):
        """Initialize default models if none are provided."""
        if not self.models:
            self.models = {
                "gpt-3.5-turbo": OpenAIModelConfig(
                    name="gpt-3.5-turbo",
                    max_tokens=4096,
                    supports_functions=True,
                ),
                "gpt-3.5-turbo-16k": OpenAIModelConfig(
                    name="gpt-3.5-turbo-16k",
                    max_tokens=16384,
                    supports_functions=True,
                ),
                "gpt-4": OpenAIModelConfig(
                    name="gpt-4",
                    max_tokens=8192,
                    supports_functions=True,
                ),
                "gpt-4-32k": OpenAIModelConfig(
                    name="gpt-4-32k",
                    max_tokens=32768,
                    supports_functions=True,
                ),
                "gpt-4-vision-preview": OpenAIModelConfig(
                    name="gpt-4-vision-preview",
                    max_tokens=128000,
                    supports_functions=True,
                    supports_vision=True,
                ),
                "gpt-4-turbo-preview": OpenAIModelConfig(
                    name="gpt-4-turbo-preview",
                    max_tokens=128000,
                    supports_functions=True,
                ),
                "text-embedding-ada-002": OpenAIModelConfig(
                    name="text-embedding-ada-002",
                    max_tokens=8191,
                ),
            }


# Default configuration
DEFAULT_CONFIG = OpenAIConfig(api_key="")


def get_config() -> OpenAIConfig:
    """Get the OpenAI configuration.

    Returns:
        The OpenAI configuration
    """
    from pepperpy.config import get_config as get_global_config

    config = get_global_config()
    openai_config = config.get("llm.providers.openai", DEFAULT_CONFIG)

    if isinstance(openai_config, dict):
        return OpenAIConfig(**openai_config)

    return openai_config
