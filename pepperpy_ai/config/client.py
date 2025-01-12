"""Client configuration."""

from dataclasses import dataclass, field
from typing import Any, Dict, Optional

@dataclass
class ClientConfig:
    """Client configuration."""

    # Required fields
    provider: str
    model: str
    api_key: str

    # Optional fields with defaults
    name: str = "client"
    version: str = "1.0.0"
    enabled: bool = True
    description: str = ""
    api_base: Optional[str] = None
    temperature: float = 0.7
    max_tokens: int = 1000
    metadata: Dict[str, Any] = field(default_factory=dict)
    settings: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate configuration."""
        if not self.provider:
            raise ValueError("Provider type must be specified")
        if not self.model:
            raise ValueError("Model must be specified")
        if not self.api_key:
            raise ValueError("API key must be specified")
        if not 0.0 <= self.temperature <= 1.0:
            raise ValueError("Temperature must be between 0.0 and 1.0")
        if self.max_tokens <= 0:
            raise ValueError("Max tokens must be positive")
