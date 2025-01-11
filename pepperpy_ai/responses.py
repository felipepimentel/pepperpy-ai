"""AI response types."""

from dataclasses import dataclass
from typing import Any, Dict, Optional, cast

from pepperpy_ai.types import JsonDict, Serializable


@dataclass
class AIResponse(Serializable):
    """Response from an AI provider.
    
    Attributes:
        content: The response content
        metadata: Optional metadata associated with the response
    """

    content: str
    metadata: Optional[Dict[str, Any]] = None

    def to_dict(self) -> JsonDict:
        """Convert response to dictionary.
        
        Returns:
            Dictionary representation of the response
        """
        return cast(JsonDict, {
            "content": self.content,
            "metadata": self.metadata or {},
        }) 