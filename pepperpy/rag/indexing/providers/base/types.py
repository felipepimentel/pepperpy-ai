"""Types for indexing providers.

This module provides type definitions for indexing providers.
"""

from enum import Enum, auto
from typing import Any, Dict, List, Optional

from pepperpy.rag.types import Chunk, Document


class IndexingProviderType(Enum):
    """Types of indexing providers."""

    CHROMA = auto()
    FAISS = auto()
    CUSTOM = auto()


class IndexingRequest:
    """Request for indexing."""

    def __init__(
        self,
        documents: Optional[List[Document]] = None,
        chunks: Optional[List[Chunk]] = None,
        collection_name: str = "default",
        options: Optional[Dict[str, Any]] = None,
    ):
        """Initialize the indexing request.

        Args:
            documents: Documents to index
            chunks: Chunks to index
            collection_name: Name of the collection to index into
            options: Additional provider-specific options
        """
        self.documents = documents or []
        self.chunks = chunks or []
        self.collection_name = collection_name
        self.options = options or {}


class IndexingResponse:
    """Response from indexing."""

    def __init__(
        self,
        success: bool,
        document_ids: Optional[List[str]] = None,
        chunk_ids: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """Initialize the indexing response.

        Args:
            success: Whether the indexing was successful
            document_ids: IDs of the indexed documents
            chunk_ids: IDs of the indexed chunks
            metadata: Additional metadata about the indexing
        """
        self.success = success
        self.document_ids = document_ids or []
        self.chunk_ids = chunk_ids or []
        self.metadata = metadata or {}
