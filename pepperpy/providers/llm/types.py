"""Type definitions for LLM providers."""

from dataclasses import dataclass
from typing import Dict, Any, Optional

@dataclass
class LLMConfig:
    """Configuration for LLM providers."""
    
    api_key: str
    model: str
    base_url: Optional[str] = None
    min_request_interval: float = 2.0
    temperature: float = 0.7
    max_tokens: Optional[int] = None
    is_fallback: bool = False
    priority: int = 1
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary.
        
        Returns:
            Dictionary representation of config.
        """
        return {
            "api_key": self.api_key,
            "model": self.model,
            "base_url": self.base_url,
            "min_request_interval": self.min_request_interval,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "is_fallback": self.is_fallback,
            "priority": self.priority
        } 