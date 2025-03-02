"""Base classes for retrieval providers.

This module defines the base classes that all retrieval providers must implement.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict

from pepperpy.rag.base import RagComponent


class RetrievalProvider(RagComponent, ABC):
    """Base class for all retrieval providers.

    A retrieval provider is a component that integrates with external services
    or APIs to provide specific retrieval capabilities.
    """

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the provider.

        This method should establish any necessary connections and
        prepare the provider for use.
        """
        pass

    @abstractmethod
    async def cleanup(self) -> None:
        """Clean up the provider.

        This method should release any resources held by the provider.
        """
        pass

    @property
    @abstractmethod
    def provider_info(self) -> Dict[str, Any]:
        """Get information about the provider.

        Returns:
            A dictionary containing information about the provider
        """
        pass
