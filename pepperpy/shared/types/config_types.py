"""Configuration type definitions."""

from dataclasses import dataclass, field
from typing import Any, Dict, Optional

from pepperpy.capabilities import RAGCapability, RAGStrategy


@dataclass
class ModelConfig:
    """Configuration for language models."""

    type: str
    model_name: str
    api_key: str
    temperature: float = 0.7
    max_tokens: Optional[int] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RAGConfig:
    """Configuration for RAG functionality."""

    capabilities: list[RAGCapability] = field(default_factory=list)
    strategy: RAGStrategy = RAGStrategy.BASIC
    chunk_size: int = 1000
    chunk_overlap: int = 200
    max_chunks: Optional[int] = None
    metadata: Dict[str, Any] = field(default_factory=dict) 