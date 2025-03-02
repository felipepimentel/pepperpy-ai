"""Registry for vector database providers.

This module provides a registry for vector database providers that can be used
for retrieval in the RAG system.
"""

from typing import Dict, Optional, Type

from pepperpy.core.logging import get_logger
from pepperpy.rag.retrieval.providers.vector_db.base import VectorDBRetriever
from pepperpy.rag.retrieval.providers.vector_db.types import VectorDBType

logger = get_logger(__name__)


class VectorDBRegistry:
    """Registry for vector database providers."""

    _instance = None
    _providers: Dict[VectorDBType, Type[VectorDBRetriever]] = {}

    def __new__(cls):
        """Ensure singleton pattern."""
        if cls._instance is None:
            cls._instance = super(VectorDBRegistry, cls).__new__(cls)
        return cls._instance

    def register(
        self, db_type: VectorDBType, provider_class: Type[VectorDBRetriever]
    ) -> None:
        """Register a vector database provider.

        Args:
            db_type: The type of vector database
            provider_class: The provider class to register
        """
        self._providers[db_type] = provider_class
        logger.info(f"Registered vector database provider for {db_type.name}")

    def get(self, db_type: VectorDBType) -> Optional[Type[VectorDBRetriever]]:
        """Get a vector database provider by type.

        Args:
            db_type: The type of vector database

        Returns:
            The provider class if registered, None otherwise
        """
        return self._providers.get(db_type)

    def list_providers(self) -> Dict[VectorDBType, Type[VectorDBRetriever]]:
        """List all registered providers.

        Returns:
            A dictionary of registered providers
        """
        return self._providers.copy()


# Singleton instance
vector_db_registry = VectorDBRegistry()
