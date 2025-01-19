"""Type definitions for LLM module."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class LLMResponse:
    """Response from LLM generation."""
    
    text: str
    tokens_used: int
    cost: float
    model_name: str
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ProviderStats:
    """Statistics for a provider."""
    
    total_tokens: int = 0
    total_cost: float = 0
    total_requests: int = 0
    failed_requests: int = 0
    avg_latency: float = 0.0
    last_failure: Optional[datetime] = None
    last_success: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ProviderConfig:
    """Configuration for a provider."""
    
    type: str
    model_name: str
    api_key: str
    temperature: float = 0.7
    max_tokens: int = 1000
    stop_sequences: List[str] = field(default_factory=list)
    model_kwargs: Dict[str, Any] = field(default_factory=dict)
    is_fallback: bool = False
    priority: int = 0 