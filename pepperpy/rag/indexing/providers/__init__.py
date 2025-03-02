"""Provider implementations for indexing components.

This module provides concrete implementations of indexing components using various
third-party libraries and services.
"""

from pepperpy.core.logging import get_logger
from pepperpy.rag.indexing.providers.base import (
    IndexingProvider,
    IndexingProviderType,
    IndexingRequest,
    IndexingResponse,
    get_indexing_provider,
    list_indexing_providers,
    register_indexing_provider,
)
from pepperpy.rag.indexing.providers.chroma import ChromaProvider
from pepperpy.rag.indexing.providers.faiss import FAISSProvider

logger = get_logger(__name__)

__all__ = [
    "ChromaProvider",
    "FAISSProvider",
    "IndexingProvider",
    "register_indexing_provider",
    "get_indexing_provider",
    "list_indexing_providers",
    "IndexingProviderType",
    "IndexingRequest",
    "IndexingResponse",
]
