"""Base interfaces for memory management."""

import logging
from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from datetime import UTC, datetime
from enum import Enum
from typing import Any, Dict, Generic, Optional, TypeVar

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=Dict[str, Any])


class MemoryType(str, Enum):
    """Types of memory storage."""

    SHORT_TERM = "short_term"  # Volatile, fast access
    MEDIUM_TERM = "medium_term"  # Semi-persistent
    LONG_TERM = "long_term"  # Persistent, indexed


class MemoryEntry(BaseModel, Generic[T]):
    """Memory entry.

    Attributes:
        key: Entry key
        value: Entry value
        type: Memory type
        created_at: Creation timestamp
        expires_at: Expiration timestamp
        metadata: Additional metadata

    """

    key: str
    value: T
    type: MemoryType = Field(default=MemoryType.SHORT_TERM)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    expires_at: Optional[datetime] = Field(default=None)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class MemoryQuery(BaseModel):
    """Memory query parameters.

    Attributes:
        query: Search query
        filters: Query filters
        limit: Maximum results
        offset: Result offset
        metadata: Metadata filters

    """

    query: str = Field(..., min_length=1)
    filters: Dict[str, Any] = Field(default_factory=dict)
    limit: int = Field(default=10, ge=1)
    offset: int = Field(default=0, ge=0)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class MemorySearchResult(BaseModel, Generic[T]):
    """Memory search result.

    Attributes:
        entry: Memory entry
        score: Similarity score
        metadata: Additional result metadata

    """

    entry: MemoryEntry[T]
    score: float = Field(ge=0.0, le=1.0)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class BaseMemory(ABC, Generic[T]):
    """Base interface for memory implementations."""

    @abstractmethod
    async def store(
        self,
        key: str,
        value: T,
        type: MemoryType = MemoryType.SHORT_TERM,
        metadata: Optional[Dict[str, Any]] = None,
        expires_at: Optional[datetime] = None,
    ) -> MemoryEntry[T]:
        """Store data in memory.

        Args:
            key: Memory key
            value: Value to store
            type: Type of memory storage
            metadata: Optional metadata
            expires_at: Optional expiration time

        Returns:
            Created memory entry

        Raises:
            ValueError: If key is invalid
            TypeError: If value type is not supported
            MemoryError: If storage fails

        """
        pass

    @abstractmethod
    async def retrieve(
        self,
        key: str,
        type: Optional[MemoryType] = None,
    ) -> MemoryEntry[T]:
        """Retrieve data from memory.

        Args:
            key: Memory key
            type: Optional memory type filter

        Returns:
            Memory entry

        Raises:
            KeyError: If key not found
            ValueError: If key is invalid
            MemoryError: If retrieval fails

        """
        pass

    @abstractmethod
    async def search(
        self,
        query: MemoryQuery,
    ) -> AsyncIterator[MemorySearchResult[T]]:
        """Search memory entries.

        Args:
            query: Search parameters

        Yields:
            Search results ordered by relevance

        Raises:
            ValueError: If query is invalid
            MemoryError: If search fails

        """
        pass
