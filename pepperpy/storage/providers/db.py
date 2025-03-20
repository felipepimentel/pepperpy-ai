"""Database storage providers for PepperPy.

This module provides database storage implementations for both SQL and NoSQL
databases, with a unified interface for data persistence.

Example:
    >>> from pepperpy.storage import DBProvider
    >>> provider = DBProvider.from_config({
    ...     "type": "sql",  # or "nosql"
    ...     "url": "postgresql://user:pass@localhost/db"
    ... })
    >>> await provider.store("users", {"id": 1, "name": "Alice"})
    >>> data = await provider.retrieve("users", {"id": 1})
"""

from abc import abstractmethod
from typing import Any, Dict, List, Optional, Union

from pepperpy.core.errors import ValidationError
from pepperpy.storage.base import StorageProvider


class DBProvider(StorageProvider):
    """Base class for database storage providers."""

    name = "db"

    def __init__(
        self,
        config: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize database provider.

        Args:
            config: Optional configuration dictionary with:
                - type: "sql" or "nosql"
                - url: Database connection URL
                - options: Additional database options
        """
        config = config or {}
        super().__init__(base_url=config.get("url", ""))
        self.db_type = config.get("type", "sql")
        self.url = config.get("url", "")
        self.options = config.get("options", {})

    @abstractmethod
    async def store(
        self,
        collection: str,
        data: Union[Dict[str, Any], List[Dict[str, Any]]],
        **kwargs: Any,
    ) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
        """Store data in the database.

        Args:
            collection: Name of the collection/table
            data: Data to store (dict or list of dicts)
            **kwargs: Additional storage options

        Returns:
            Stored data with any generated fields

        Raises:
            ValidationError: If data is invalid
        """
        if not collection or not isinstance(collection, str):
            raise ValidationError("Collection name must be a non-empty string")
        if not data:
            raise ValidationError("Data cannot be empty")
        return await self._store_impl(collection, data, **kwargs)

    @abstractmethod
    async def retrieve(
        self,
        collection: str,
        query: Dict[str, Any],
        **kwargs: Any,
    ) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
        """Retrieve data from the database.

        Args:
            collection: Name of the collection/table
            query: Query parameters
            **kwargs: Additional retrieval options

        Returns:
            Retrieved data matching the query

        Raises:
            NotFoundError: If no data matches the query
        """
        if not collection or not isinstance(collection, str):
            raise ValidationError("Collection name must be a non-empty string")
        if not query:
            raise ValidationError("Query cannot be empty")
        return await self._retrieve_impl(collection, query, **kwargs)

    @abstractmethod
    async def update(
        self,
        collection: str,
        query: Dict[str, Any],
        data: Dict[str, Any],
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Update data in the database.

        Args:
            collection: Name of the collection/table
            query: Query to identify data to update
            data: New data to apply
            **kwargs: Additional update options

        Returns:
            Updated data

        Raises:
            NotFoundError: If no data matches the query
            ValidationError: If data is invalid
        """
        if not collection or not isinstance(collection, str):
            raise ValidationError("Collection name must be a non-empty string")
        if not query:
            raise ValidationError("Query cannot be empty")
        if not data:
            raise ValidationError("Update data cannot be empty")
        return await self._update_impl(collection, query, data, **kwargs)

    @abstractmethod
    async def delete(
        self,
        collection: str,
        query: Dict[str, Any],
        **kwargs: Any,
    ) -> None:
        """Delete data from the database.

        Args:
            collection: Name of the collection/table
            query: Query to identify data to delete
            **kwargs: Additional deletion options

        Raises:
            NotFoundError: If no data matches the query
        """
        if not collection or not isinstance(collection, str):
            raise ValidationError("Collection name must be a non-empty string")
        if not query:
            raise ValidationError("Query cannot be empty")
        await self._delete_impl(collection, query, **kwargs)

    @abstractmethod
    async def _store_impl(
        self,
        collection: str,
        data: Union[Dict[str, Any], List[Dict[str, Any]]],
        **kwargs: Any,
    ) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
        """Implementation for storing data."""
        raise NotImplementedError

    @abstractmethod
    async def _retrieve_impl(
        self,
        collection: str,
        query: Dict[str, Any],
        **kwargs: Any,
    ) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
        """Implementation for retrieving data."""
        raise NotImplementedError

    @abstractmethod
    async def _update_impl(
        self,
        collection: str,
        query: Dict[str, Any],
        data: Dict[str, Any],
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Implementation for updating data."""
        raise NotImplementedError

    @abstractmethod
    async def _delete_impl(
        self,
        collection: str,
        query: Dict[str, Any],
        **kwargs: Any,
    ) -> None:
        """Implementation for deleting data."""
        raise NotImplementedError


class SQLProvider(DBProvider):
    """SQL database provider implementation."""

    name = "sql"

    async def _store_impl(
        self,
        collection: str,
        data: Union[Dict[str, Any], List[Dict[str, Any]]],
        **kwargs: Any,
    ) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
        """Store data in SQL database."""
        # TODO[v1.0]: Implement SQL storage with SQLAlchemy
        # Issue: #236 - Database Provider Implementation
        raise NotImplementedError

    async def _retrieve_impl(
        self,
        collection: str,
        query: Dict[str, Any],
        **kwargs: Any,
    ) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
        """Retrieve data from SQL database."""
        # TODO[v1.0]: Implement SQL retrieval with SQLAlchemy
        # Issue: #236 - Database Provider Implementation
        raise NotImplementedError

    async def _update_impl(
        self,
        collection: str,
        query: Dict[str, Any],
        data: Dict[str, Any],
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Update data in SQL database."""
        # TODO[v1.0]: Implement SQL update with SQLAlchemy
        # Issue: #236 - Database Provider Implementation
        raise NotImplementedError

    async def _delete_impl(
        self,
        collection: str,
        query: Dict[str, Any],
        **kwargs: Any,
    ) -> None:
        """Delete data from SQL database."""
        # TODO[v1.0]: Implement SQL deletion with SQLAlchemy
        # Issue: #236 - Database Provider Implementation
        raise NotImplementedError


class NoSQLProvider(DBProvider):
    """NoSQL database provider implementation."""

    name = "nosql"

    async def _store_impl(
        self,
        collection: str,
        data: Union[Dict[str, Any], List[Dict[str, Any]]],
        **kwargs: Any,
    ) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
        """Store data in NoSQL database."""
        # TODO[v1.0]: Implement NoSQL storage with MongoDB
        # Issue: #236 - Database Provider Implementation
        raise NotImplementedError

    async def _retrieve_impl(
        self,
        collection: str,
        query: Dict[str, Any],
        **kwargs: Any,
    ) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
        """Retrieve data from NoSQL database."""
        # TODO[v1.0]: Implement NoSQL retrieval with MongoDB
        # Issue: #236 - Database Provider Implementation
        raise NotImplementedError

    async def _update_impl(
        self,
        collection: str,
        query: Dict[str, Any],
        data: Dict[str, Any],
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Update data in NoSQL database."""
        # TODO[v1.0]: Implement NoSQL update with MongoDB
        # Issue: #236 - Database Provider Implementation
        raise NotImplementedError

    async def _delete_impl(
        self,
        collection: str,
        query: Dict[str, Any],
        **kwargs: Any,
    ) -> None:
        """Delete data from NoSQL database."""
        # TODO[v1.0]: Implement NoSQL deletion with MongoDB
        # Issue: #236 - Database Provider Implementation
        raise NotImplementedError
