"""Memory store protocols and base classes.

This module defines the core protocols and base classes for memory stores,
ensuring proper type safety and variance handling.
"""

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from typing import Any, Generic, Protocol, TypeVar, runtime_checkable

from .types import MemoryEntry, MemoryQuery, MemoryResult, MemoryScope

# Type variables for memory stores
T_Content = TypeVar("T_Content", bound=dict[str, Any])


@runtime_checkable
class MemoryStore(Protocol[T_Content]):
    """Protocol for memory stores.

    Type Parameters:
        T_Content: Type of content stored in memory entries
    """

    @abstractmethod
    async def store(
        self,
        key: str,
        content: T_Content,
        scope: MemoryScope = MemoryScope.SESSION,
        metadata: dict[str, str] | None = None,
    ) -> MemoryEntry[T_Content]:
        """Store content in memory.

        Args:
            key: Unique key for the content
            content: Content to store
            scope: Storage scope
            metadata: Optional metadata

        Returns:
            Created memory entry

        Raises:
            ValueError: If key or content is invalid
            RuntimeError: If storage fails
        """
        ...

    @abstractmethod
    def retrieve(
        self,
        query: MemoryQuery,
    ) -> AsyncIterator[MemoryResult[T_Content]]:
        """Retrieve entries from memory.

        Args:
            query: Query parameters

        Returns:
            Iterator of memory results

        Raises:
            ValueError: If query is invalid
            RuntimeError: If retrieval fails
        """
        ...

    @abstractmethod
    async def delete(self, key: str) -> bool:
        """Delete an entry from memory.

        Args:
            key: Key to delete

        Returns:
            True if deleted, False if not found

        Raises:
            ValueError: If key is invalid
            RuntimeError: If deletion fails
        """
        ...

    @abstractmethod
    async def exists(self, key: str) -> bool:
        """Check if key exists in memory.

        Args:
            key: Key to check

        Returns:
            True if exists, False otherwise

        Raises:
            ValueError: If key is invalid
            RuntimeError: If check fails
        """
        ...

    @abstractmethod
    async def clear(self, scope: MemoryScope | None = None) -> int:
        """Clear entries from memory.

        Args:
            scope: Optional scope to clear

        Returns:
            Number of entries cleared

        Raises:
            RuntimeError: If clearing fails
        """
        ...


class BaseMemoryStore(ABC, Generic[T_Content]):
    """Base class for memory stores.

    Type Parameters:
        T_Content: Type of content stored in memory entries
    """

    @abstractmethod
    async def _store_impl(
        self,
        key: str,
        content: T_Content,
        scope: MemoryScope,
        metadata: dict[str, str] | None,
    ) -> MemoryEntry[T_Content]:
        """Store content in memory.

        Args:
            key: Key to store under
            content: Content to store
            scope: Storage scope
            metadata: Optional metadata

        Returns:
            Created memory entry

        Raises:
            RuntimeError: If storage fails
        """
        ...

    @abstractmethod
    def _retrieve_impl(
        self,
        query: MemoryQuery,
    ) -> AsyncIterator[MemoryResult[T_Content]]:
        """Retrieve entries from memory.

        Args:
            query: Query parameters

        Returns:
            Iterator of memory results

        Raises:
            RuntimeError: If retrieval fails
        """
        ...

    @abstractmethod
    async def _delete_impl(self, key: str) -> bool:
        """Delete an entry from memory.

        Args:
            key: Key to delete

        Returns:
            True if deleted, False if not found

        Raises:
            RuntimeError: If deletion fails
        """
        ...

    @abstractmethod
    async def _exists_impl(self, key: str) -> bool:
        """Check if key exists in memory.

        Args:
            key: Key to check

        Returns:
            True if exists, False otherwise

        Raises:
            RuntimeError: If check fails
        """
        ...

    @abstractmethod
    async def _clear_impl(self, scope: MemoryScope | None = None) -> int:
        """Clear entries from memory.

        Args:
            scope: Optional scope to clear

        Returns:
            Number of entries cleared

        Raises:
            RuntimeError: If clearing fails
        """
        ...

    async def store(
        self,
        key: str,
        content: T_Content,
        scope: MemoryScope = MemoryScope.SESSION,
        metadata: dict[str, str] | None = None,
    ) -> MemoryEntry[T_Content]:
        """Store content in memory.

        Args:
            key: Key to store under
            content: Content to store
            scope: Storage scope
            metadata: Optional metadata

        Returns:
            Created memory entry

        Raises:
            ValueError: If key or content is invalid
            RuntimeError: If storage fails
        """
        if not key:
            raise ValueError("Key cannot be empty")
        if not content:
            raise ValueError("Content cannot be empty")

        return await self._store_impl(key, content, scope, metadata)

    def retrieve(
        self,
        query: MemoryQuery,
    ) -> AsyncIterator[MemoryResult[T_Content]]:
        """Retrieve entries from memory.

        Args:
            query: Query parameters

        Returns:
            Iterator of memory results

        Raises:
            ValueError: If query is invalid
            RuntimeError: If retrieval fails
        """
        if not query:
            raise ValueError("Query cannot be empty")

        return self._retrieve_impl(query)

    async def delete(self, key: str) -> bool:
        """Delete an entry from memory.

        Args:
            key: Key to delete

        Returns:
            True if deleted, False if not found

        Raises:
            ValueError: If key is invalid
            RuntimeError: If deletion fails
        """
        if not key:
            raise ValueError("Key cannot be empty")

        return await self._delete_impl(key)

    async def exists(self, key: str) -> bool:
        """Check if key exists in memory.

        Args:
            key: Key to check

        Returns:
            True if exists, False otherwise

        Raises:
            ValueError: If key is invalid
            RuntimeError: If check fails
        """
        if not key:
            raise ValueError("Key cannot be empty")

        return await self._exists_impl(key)

    async def clear(self, scope: MemoryScope | None = None) -> int:
        """Clear entries from memory.

        Args:
            scope: Optional scope to clear

        Returns:
            Number of entries cleared

        Raises:
            RuntimeError: If clearing fails
        """
        return await self._clear_impl(scope)
