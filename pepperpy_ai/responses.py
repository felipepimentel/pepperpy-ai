"""AI response types."""

from dataclasses import dataclass
from typing import Optional, Dict, Any

from pepperpy_ai.types import JsonDict, Serializable


@dataclass
class AIResponse(Serializable):
    """Response from an AI provider.
    
    Attributes:
        content: The response content
        model: Optional model associated with the response
        provider: Optional provider associated with the response
        metadata: Optional metadata associated with the response
    """

    content: str
    model: Optional[str] = None
    provider: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

    def to_dict(self) -> JsonDict:
        """Convert response to dictionary.
        
        Returns:
            Dictionary representation of the response
        """
        return {
            "content": self.content,
            "model": self.model,
            "provider": self.provider,
            "metadata": self.metadata or {},
        }
