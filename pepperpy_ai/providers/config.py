"""Provider configuration module."""

from dataclasses import dataclass, field
from typing import Any, Dict, Optional

from ..config.base import BaseConfig
from ..types import JsonDict

@dataclass
class ProviderConfig(BaseConfig):
    """Provider configuration class.
    
    Attributes:
        api_key: The API key for the provider.
        model: The model name to use.
        provider: The provider name.
        api_base: Optional base URL for the provider's API.
        temperature: Sampling temperature between 0 and 1.
        max_tokens: Maximum number of tokens to generate.
    """

    # Required provider fields
    api_key: str = field(init=False)
    model: str = field(init=False)
    provider: str = field(init=False)
    
    # Optional provider fields
    api_base: Optional[str] = None
    temperature: float = 0.7
    max_tokens: int = 1024

    def __init__(
        self,
        api_key: str,
        model: str,
        provider: str,
        name: str = "provider",
        version: str = "1.0.0",
        enabled: bool = True,
        api_base: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1024,
        metadata: Optional[JsonDict] = None,
        settings: Optional[JsonDict] = None,
    ) -> None:
        """Initialize provider configuration.
        
        Args:
            api_key: The API key for the provider.
            model: The model name to use.
            provider: The provider name.
            name: The configuration name.
            version: The configuration version.
            enabled: Whether the provider is enabled.
            api_base: Optional base URL for the provider's API.
            temperature: Sampling temperature between 0 and 1.
            max_tokens: Maximum number of tokens to generate.
            metadata: Optional metadata dictionary.
            settings: Optional settings dictionary.
        """
        super().__init__(
            name=name,
            version=version,
            enabled=enabled,
            metadata=metadata or {},
            settings=settings or {},
        )
        self.api_key = api_key
        self.model = model
        self.provider = provider
        self.api_base = api_base
        self.temperature = temperature
        self.max_tokens = max_tokens

    def __post_init__(self) -> None:
        """Validate configuration."""
        super().__post_init__()

        if not self.api_key:
            raise ValueError("API key cannot be empty")

        if not self.model:
            raise ValueError("Model name cannot be empty")

        if not self.provider:
            raise ValueError("Provider name cannot be empty")

        if not isinstance(self.temperature, float):
            raise ValueError("Temperature must be a float")

        if not isinstance(self.max_tokens, int):
            raise ValueError("Max tokens must be an integer")
