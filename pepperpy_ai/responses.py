"""AI response types."""

from dataclasses import dataclass
from typing import Dict, Optional


@dataclass
class AIResponse:
    """AI response class."""
    content: str
    metadata: Optional[Dict[str, str]] = None 