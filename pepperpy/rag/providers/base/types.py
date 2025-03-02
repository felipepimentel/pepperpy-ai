"""Type definitions for RAG providers.

This module defines the types used by RAG providers.
"""

from enum import Enum, auto
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class ProviderType(Enum):
    """Types of RAG providers supported by the system."""

    VECTOR_DB = auto()
    DOCUMENT_PROCESSOR = auto()
    EMBEDDING_MODEL = auto()
    KNOWLEDGE_BASE = auto()
    SEARCH_ENGINE = auto()
    CUSTOM = auto()


class ProviderConfig(BaseModel):
    """Base configuration for a RAG provider."""

    provider_type: ProviderType
    provider_id: str
    api_key: Optional[str] = None
    connection_string: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
