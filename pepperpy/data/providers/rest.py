"""
REST-based Data providers for PepperPy.

This module implements Data providers that use REST APIs for data storage and retrieval.
"""

from typing import Any, Dict, List, Optional, TypeVar

from pepperpy.providers.rest_base import RESTProvider
from pepperpy.types.common import Result
from pepperpy.utils.logging import get_logger

logger = get_logger(__name__)

T = TypeVar("T")


class RESTDataProvider(RESTProvider):
    """Base class for REST-based data providers.

    This class extends RESTProvider to provide a foundation for data providers
    that use REST APIs for storage and retrieval.
    """

    def __init__(
        self,
        name: str,
        api_key: str,
        base_url: Optional[str] = None,
        timeout: int = 30,
        max_retries: int = 3,
        **kwargs: Any,
    ) -> None:
        """Initialize a new REST data provider.

        Args:
            name: Provider name
            api_key: Authentication key
            base_url: Base URL for the API
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
            **kwargs: Additional provider-specific configuration
        """
        super().__init__(
            name=name,
            api_key=api_key,
            base_url=base_url,
            timeout=timeout,
            max_retries=max_retries,
            **kwargs,
        )

    async def create(
        self,
        collection: str,
        data: Dict[str, Any],
        **kwargs: Any,
    ) -> Result[str]:
        """Create a new document in the collection.

        Args:
            collection: Collection name
            data: Document data
            **kwargs: Additional creation parameters

        Returns:
            Result with the document ID

        Raises:
            DataError: If creation fails
        """
        raise NotImplementedError("Subclasses must implement create")

    async def read(
        self,
        collection: str,
        document_id: str,
        **kwargs: Any,
    ) -> Result[Dict[str, Any]]:
        """Read a document from the collection.

        Args:
            collection: Collection name
            document_id: Document ID
            **kwargs: Additional read parameters

        Returns:
            Result with the document data

        Raises:
            DataError: If read fails
        """
        raise NotImplementedError("Subclasses must implement read")

    async def update(
        self,
        collection: str,
        document_id: str,
        data: Dict[str, Any],
        **kwargs: Any,
    ) -> Result[bool]:
        """Update a document in the collection.

        Args:
            collection: Collection name
            document_id: Document ID
            data: Updated document data
            **kwargs: Additional update parameters

        Returns:
            Result with success status

        Raises:
            DataError: If update fails
        """
        raise NotImplementedError("Subclasses must implement update")

    async def delete(
        self,
        collection: str,
        document_id: str,
        **kwargs: Any,
    ) -> Result[bool]:
        """Delete a document from the collection.

        Args:
            collection: Collection name
            document_id: Document ID
            **kwargs: Additional delete parameters

        Returns:
            Result with success status

        Raises:
            DataError: If deletion fails
        """
        raise NotImplementedError("Subclasses must implement delete")

    async def query(
        self,
        collection: str,
        query: Dict[str, Any],
        **kwargs: Any,
    ) -> Result[List[Dict[str, Any]]]:
        """Query documents in the collection.

        Args:
            collection: Collection name
            query: Query parameters
            **kwargs: Additional query parameters

        Returns:
            Result with list of matching documents

        Raises:
            DataError: If query fails
        """
        raise NotImplementedError("Subclasses must implement query")

    def get_capabilities(self) -> Dict[str, Any]:
        """Get the provider capabilities.

        Returns:
            Dict with provider capabilities
        """
        capabilities = super().get_capabilities()
        capabilities.update({
            "supports_create": True,
            "supports_read": True,
            "supports_update": True,
            "supports_delete": True,
            "supports_query": True,
        })
        return capabilities
