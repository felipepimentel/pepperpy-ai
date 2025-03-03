"""Base classes for RAG providers.

This module defines the base classes that all RAG providers must implement.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict

from pepperpy.rag.base import RagComponent


class RagProvider(RagComponent, ABC):
    """Base class for all RAG providers.

    A RAG provider is a component that integrates with external services
    or APIs to provide specific RAG capabilities.
    """

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the provider.

        This method should establish any necessary connections and
        prepare the provider for use.
        """

    @abstractmethod
    async def cleanup(self) -> None:
        """Clean up the provider.

        This method should release any resources held by the provider.
        """

    @property
    @abstractmethod
    def provider_info(self) -> Dict[str, Any]:
        """Get information about the provider.

        Returns:
            A dictionary containing information about the provider

        """
