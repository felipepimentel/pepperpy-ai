"""Type definitions for vector database providers.

This module defines the types used by vector database providers for the RAG system.
"""

from enum import Enum, auto
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class VectorDBType(Enum):
    """Types of vector databases supported by the system."""

    CUSTOM = auto()
    QDRANT = auto()
    PINECONE = auto()
    MILVUS = auto()
    WEAVIATE = auto()
    CHROMA = auto()
    FAISS = auto()


class VectorDBConfig(BaseModel):
    """Configuration for a vector database connection."""

    db_type: VectorDBType
    connection_string: Optional[str] = None
    api_key: Optional[str] = None
    collection_name: str
    dimension: int = 1536
    metadata: Dict[str, Any] = Field(default_factory=dict)
