"""Unified search and retrieval system for Pepperpy.

This module provides a comprehensive search framework that includes:
- Search result representation
- Query building
- Abstract search provider interface
- Base search provider implementation
- Memory-based search provider
- Search manager for coordinating providers
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Generic, TypeVar

from pepperpy.core.errors.unified import PepperpyError
from pepperpy.core.memory.unified import MemoryEntry, MemoryStore
from pepperpy.core.metrics import MetricsManager

logger = logging.getLogger(__name__)

T = TypeVar("T")


class SearchError(PepperpyError):
    """Base class for search-related errors."""

    def __init__(self, message: str, code: str = "SEARCH000", **kwargs):
        super().__init__(message, code=code, category="search", **kwargs)


@dataclass
class SearchResult(Generic[T]):
    """Represents a search result with metadata."""

    id: str
    score: float
    data: T
    metadata: dict[str, Any] | None = None
    timestamp: datetime = datetime.now()

    def to_dict(self) -> dict[str, Any]:
        """Convert the search result to a dictionary.

        Returns:
            Dictionary containing the result data.
        """
        return {
            "id": self.id,
            "score": self.score,
            "data": self.data,
            "metadata": self.metadata,
            "timestamp": self.timestamp,
        }


class SearchQuery:
    """Builder for search queries."""

    def __init__(
        self,
        query: str,
        filters: dict[str, Any] | None = None,
        sort: list[str] | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ):
        """Initialize a search query.

        Args:
            query: The search query string.
            filters: Optional filters to apply.
            sort: Optional sort fields.
            limit: Optional result limit.
            offset: Optional result offset.
        """
        self.query = query
        self.filters = filters or {}
        self.sort = sort or []
        self.limit = limit
        self.offset = offset

    def add_filter(self, field: str, value: Any) -> "SearchQuery":
        """Add a filter to the query.

        Args:
            field: The field to filter on.
            value: The filter value.

        Returns:
            Self for chaining.
        """
        self.filters[field] = value
        return self

    def add_sort(self, field: str) -> "SearchQuery":
        """Add a sort field to the query.

        Args:
            field: The field to sort by.

        Returns:
            Self for chaining.
        """
        self.sort.append(field)
        return self

    def set_limit(self, limit: int) -> "SearchQuery":
        """Set the result limit.

        Args:
            limit: Maximum number of results.

        Returns:
            Self for chaining.
        """
        self.limit = limit
        return self

    def set_offset(self, offset: int) -> "SearchQuery":
        """Set the result offset.

        Args:
            offset: Number of results to skip.

        Returns:
            Self for chaining.
        """
        self.offset = offset
        return self


class SearchProvider(ABC, Generic[T]):
    """Abstract base class for search providers."""

    @abstractmethod
    async def search(self, query: SearchQuery) -> AsyncIterator[SearchResult[T]]:
        """Execute search query and return results.

        Args:
            query: The search query to execute.

        Yields:
            Search results matching the query.
        """
        pass

    @abstractmethod
    async def get(self, id: str) -> T | None:
        """Get item by ID.

        Args:
            id: The item ID.

        Returns:
            The item if found, None otherwise.
        """
        pass

    @abstractmethod
    async def exists(self, id: str) -> bool:
        """Check if item exists.

        Args:
            id: The item ID.

        Returns:
            True if the item exists, False otherwise.
        """
        pass


class BaseSearchProvider(SearchProvider[T]):
    """Base implementation of search provider with common functionality."""

    def __init__(self):
        """Initialize the base search provider."""
        self._metrics = MetricsManager.get_instance()
        self._lock = asyncio.Lock()

    async def exists(self, id: str) -> bool:
        """Check if item exists."""
        result = await self.get(id)
        return result is not None

    async def _record_operation(
        self, operation: str, success: bool = True, **labels: str
    ) -> None:
        """Record a search operation metric.

        Args:
            operation: The operation name.
            success: Whether the operation succeeded.
            **labels: Additional metric labels.
        """
        self._metrics.counter(
            f"search_provider_{operation}", 1, success=str(success).lower(), **labels
        )

    def _calculate_score(self, item: T, query: str, **context: Any) -> float:
        """Calculate relevance score for item.

        Args:
            item: The item to score.
            query: The search query.
            **context: Additional scoring context.

        Returns:
            Relevance score between 0 and 1.
        """
        # Basic implementation - override for better scoring
        return 1.0


class MemorySearchProvider(BaseSearchProvider[T]):
    """Search provider implementation using memory store."""

    def __init__(self, store: MemoryStore[T]):
        """Initialize the memory search provider.

        Args:
            store: The memory store to search.
        """
        super().__init__()
        self._store = store

    async def search(self, query: SearchQuery) -> AsyncIterator[SearchResult[T]]:
        """Search the memory store."""
        async with self._lock:
            async for key in self._store.scan(query.query):
                entry = await self._store.get(key)
                if entry is None:
                    continue

                if not self._matches_filters(entry, query.filters):
                    continue

                score = self._calculate_score(entry.value, query.query)
                yield SearchResult(
                    id=key,
                    score=score,
                    data=entry.value,
                    metadata=entry.metadata,
                    timestamp=entry.created_at,
                )

    def _matches_filters(self, entry: MemoryEntry[T], filters: dict[str, Any]) -> bool:
        """Check if entry matches filters.

        Args:
            entry: The entry to check.
            filters: Filters to apply.

        Returns:
            True if entry matches all filters.
        """
        for key, value in filters.items():
            if key not in entry.metadata:
                return False
            if entry.metadata[key] != value:
                return False
        return True

    async def get(self, id: str) -> T | None:
        """Get item by ID."""
        entry = await self._store.get(id)
        if entry is None:
            await self._record_operation("get", False, reason="not_found")
            return None

        await self._record_operation("get", True)
        return entry.value


class SearchManager(Generic[T]):
    """Manager for coordinating multiple search providers."""

    def __init__(self):
        """Initialize the search manager."""
        self._providers: dict[str, SearchProvider[T]] = {}
        self._metrics = MetricsManager.get_instance()

    def register_provider(self, name: str, provider: SearchProvider[T]) -> None:
        """Register a search provider.

        Args:
            name: The provider's name.
            provider: The provider instance.
        """
        self._providers[name] = provider

    async def search(
        self, query: str | SearchQuery, provider: str | None = None, **kwargs: Any
    ) -> AsyncIterator[SearchResult[T]]:
        """Search using registered providers.

        Args:
            query: Search query string or SearchQuery instance.
            provider: Optional provider name to use.
            **kwargs: Additional query parameters.

        Yields:
            Search results from providers.

        Raises:
            SearchError: If provider is not found.
        """
        if isinstance(query, str):
            query = SearchQuery(query, **kwargs)

        if provider:
            if provider not in self._providers:
                raise SearchError(f"Provider not found: {provider}", code="SEARCH001")
            async for result in self._providers[provider].search(query):
                yield result
        else:
            # Search across all providers
            results: list[SearchResult[T]] = []
            for p in self._providers.values():
                async for result in p.search(query):
                    results.append(result)

            # Sort by score
            results.sort(key=lambda r: r.score, reverse=True)

            # Apply limit and offset
            start = query.offset or 0
            end = start + query.limit if query.limit else None
            for result in results[start:end]:
                yield result

    async def get(self, id: str, provider: str | None = None) -> T | None:
        """Get item from providers.

        Args:
            id: The item ID.
            provider: Optional provider name to use.

        Returns:
            The item if found, None otherwise.

        Raises:
            SearchError: If provider is not found.
        """
        if provider:
            if provider not in self._providers:
                raise SearchError(f"Provider not found: {provider}", code="SEARCH001")
            return await self._providers[provider].get(id)

        # Try all providers
        for p in self._providers.values():
            result = await p.get(id)
            if result is not None:
                return result

        return None
