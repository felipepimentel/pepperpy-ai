"""Base module for indexing providers.

This module provides the base classes and interfaces for indexing providers.
"""

from pepperpy.rag.indexing.providers.base.base import IndexingProvider
from pepperpy.rag.indexing.providers.base.registry import (
    get_indexing_provider,
    list_indexing_providers,
    register_indexing_provider,
)
from pepperpy.rag.indexing.providers.base.types import (
    IndexingProviderType,
    IndexingRequest,
    IndexingResponse,
)

__all__ = [
    "IndexingProvider",
    "register_indexing_provider",
    "get_indexing_provider",
    "list_indexing_providers",
    "IndexingProviderType",
    "IndexingRequest",
    "IndexingResponse",
]
