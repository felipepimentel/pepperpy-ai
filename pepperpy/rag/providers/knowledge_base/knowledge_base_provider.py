"""Knowledge base provider implementation.

This module implements the knowledge base provider for RAG capabilities.
"""

from typing import Any, Dict

from pepperpy.rag.providers.base.base import RagProvider
from pepperpy.rag.providers.base.types import ProviderType


class KnowledgeBaseProvider(RagProvider):
    """Knowledge base provider implementation.

    This provider integrates with structured knowledge repositories
    for information retrieval.
    """

    async def initialize(self) -> None:
        """Initialize the knowledge base provider."""
        pass

    async def cleanup(self) -> None:
        """Clean up the knowledge base provider."""
        pass

    @property
    def provider_info(self) -> Dict[str, Any]:
        """Get information about the provider.

        Returns:
            A dictionary containing information about the provider
        """
        return {
            "provider_type": ProviderType.KNOWLEDGE_BASE,
            "provider_id": "knowledge_base",
            "description": "Knowledge base provider for RAG",
        }
