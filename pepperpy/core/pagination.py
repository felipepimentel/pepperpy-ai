"""Standardized pagination and iteration patterns.

This module provides standardized pagination and iteration patterns for the PepperPy
framework. It includes classes for paginated results, page iterators, and pagination
configuration.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import (
    Any,
    Dict,
    Generic,
    List,
    Optional,
    Protocol,
    Sequence,
    TypeVar,
    runtime_checkable,
)
from typing import (
    AsyncIterator as AsyncIteratorType,
)
from typing import (
    Iterator as IteratorType,
)

from pepperpy.interfaces.core import AsyncIterator, Iterator

T = TypeVar("T")
U = TypeVar("U")


class PaginationStrategy(Enum):
    """Pagination strategy.

    This enum defines the different strategies for pagination.
    """

    OFFSET = auto()  # Offset-based pagination (skip/limit)
    CURSOR = auto()  # Cursor-based pagination (next/previous tokens)
    PAGE = auto()  # Page-based pagination (page number/size)
    TIME = auto()  # Time-based pagination (before/after timestamps)


@dataclass
class PaginationConfig:
    """Pagination configuration.

    This class defines the configuration for pagination.
    """

    # Common parameters
    strategy: PaginationStrategy = PaginationStrategy.OFFSET
    page_size: int = 20
    max_page_size: int = 100

    # Offset-based pagination
    offset: int = 0
    limit: Optional[int] = None

    # Cursor-based pagination
    cursor: Optional[str] = None
    direction: str = "forward"

    # Page-based pagination
    page: int = 1

    # Time-based pagination
    before: Optional[float] = None
    after: Optional[float] = None

    # Sorting
    sort_by: Optional[str] = None
    sort_order: str = "desc"

    # Additional parameters
    params: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate and normalize configuration."""
        # Ensure page is at least 1
        self.page = max(1, self.page)

        # Ensure offset is at least 0
        self.offset = max(0, self.offset)

        # Ensure page_size is between 1 and max_page_size
        self.page_size = max(1, min(self.page_size, self.max_page_size))

        # Set limit to page_size if not specified
        if self.limit is None:
            self.limit = self.page_size

        # Ensure limit is between 1 and max_page_size
        if self.limit is not None:
            self.limit = max(1, min(self.limit, self.max_page_size))

        # Normalize sort order
        self.sort_order = self.sort_order.lower()
        if self.sort_order not in ("asc", "desc"):
            self.sort_order = "desc"

        # Normalize direction
        self.direction = self.direction.lower()
        if self.direction not in ("forward", "backward"):
            self.direction = "forward"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary.

        Returns:
            Dictionary representation of the configuration
        """
        result = {
            "strategy": self.strategy.name,
            "page_size": self.page_size,
        }

        # Add strategy-specific parameters
        if self.strategy == PaginationStrategy.OFFSET:
            result.update({"offset": self.offset, "limit": self.limit})
        elif self.strategy == PaginationStrategy.CURSOR:
            result.update({"cursor": self.cursor, "direction": self.direction})
        elif self.strategy == PaginationStrategy.PAGE:
            result.update({"page": self.page})
        elif self.strategy == PaginationStrategy.TIME:
            if self.before is not None:
                result["before"] = self.before
            if self.after is not None:
                result["after"] = self.after

        # Add sorting parameters
        if self.sort_by:
            result.update({"sort_by": self.sort_by, "sort_order": self.sort_order})

        # Add additional parameters
        result.update(self.params)

        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> PaginationConfig:
        """Create from dictionary.

        Args:
            data: Dictionary representation of the configuration

        Returns:
            PaginationConfig instance
        """
        # Extract strategy
        strategy_name = data.get("strategy", "OFFSET")
        try:
            strategy = PaginationStrategy[strategy_name]
        except KeyError:
            strategy = PaginationStrategy.OFFSET

        # Extract common parameters
        config = cls(
            strategy=strategy,
            page_size=data.get("page_size", 20),
            max_page_size=data.get("max_page_size", 100),
        )

        # Extract strategy-specific parameters
        if strategy == PaginationStrategy.OFFSET:
            config.offset = data.get("offset", 0)
            config.limit = data.get("limit", config.page_size)
        elif strategy == PaginationStrategy.CURSOR:
            config.cursor = data.get("cursor")
            config.direction = data.get("direction", "forward")
        elif strategy == PaginationStrategy.PAGE:
            config.page = data.get("page", 1)
        elif strategy == PaginationStrategy.TIME:
            config.before = data.get("before")
            config.after = data.get("after")

        # Extract sorting parameters
        config.sort_by = data.get("sort_by")
        config.sort_order = data.get("sort_order", "desc")

        # Extract additional parameters
        for key, value in data.items():
            if key not in {
                "strategy",
                "page_size",
                "max_page_size",
                "offset",
                "limit",
                "cursor",
                "direction",
                "page",
                "before",
                "after",
                "sort_by",
                "sort_order",
            }:
                config.params[key] = value

        return config

    def next_page(self) -> PaginationConfig:
        """Get configuration for the next page.

        Returns:
            Configuration for the next page
        """
        config = PaginationConfig(
            strategy=self.strategy,
            page_size=self.page_size,
            max_page_size=self.max_page_size,
            sort_by=self.sort_by,
            sort_order=self.sort_order,
            params=self.params.copy(),
        )

        if self.strategy == PaginationStrategy.OFFSET:
            config.offset = self.offset + (self.limit or self.page_size)
            config.limit = self.limit
        elif self.strategy == PaginationStrategy.CURSOR:
            # Cursor will be set by the paginated results
            config.direction = "forward"
        elif self.strategy == PaginationStrategy.PAGE:
            config.page = self.page + 1
        elif self.strategy == PaginationStrategy.TIME:
            # Timestamps will be set by the paginated results
            pass

        return config

    def previous_page(self) -> PaginationConfig:
        """Get configuration for the previous page.

        Returns:
            Configuration for the previous page
        """
        config = PaginationConfig(
            strategy=self.strategy,
            page_size=self.page_size,
            max_page_size=self.max_page_size,
            sort_by=self.sort_by,
            sort_order=self.sort_order,
            params=self.params.copy(),
        )

        if self.strategy == PaginationStrategy.OFFSET:
            config.offset = max(0, self.offset - (self.limit or self.page_size))
            config.limit = self.limit
        elif self.strategy == PaginationStrategy.CURSOR:
            # Cursor will be set by the paginated results
            config.direction = "backward"
        elif self.strategy == PaginationStrategy.PAGE:
            config.page = max(1, self.page - 1)
        elif self.strategy == PaginationStrategy.TIME:
            # Timestamps will be set by the paginated results
            pass

        return config


@dataclass
class Page(Generic[T]):
    """Page of results.

    This class represents a single page of results.
    """

    items: List[T]
    total: Optional[int] = None
    page_size: int = 0
    page_number: int = 0
    has_next: bool = False
    has_previous: bool = False
    next_cursor: Optional[str] = None
    previous_cursor: Optional[str] = None
    next_timestamp: Optional[float] = None
    previous_timestamp: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Initialize derived properties."""
        if self.page_size == 0:
            self.page_size = len(self.items)

    def __len__(self) -> int:
        """Get the number of items in the page.

        Returns:
            Number of items
        """
        return len(self.items)

    def __getitem__(self, index: int) -> T:
        """Get an item by index.

        Args:
            index: The index of the item

        Returns:
            The item
        """
        return self.items[index]

    def __iter__(self) -> IteratorType[T]:
        """Get an iterator over the items.

        Returns:
            Iterator over the items
        """
        return iter(self.items)

    @property
    def is_first_page(self) -> bool:
        """Check if this is the first page.

        Returns:
            True if this is the first page, False otherwise
        """
        return not self.has_previous

    @property
    def is_last_page(self) -> bool:
        """Check if this is the last page.

        Returns:
            True if this is the last page, False otherwise
        """
        return not self.has_next

    @property
    def total_pages(self) -> Optional[int]:
        """Get the total number of pages.

        Returns:
            Total number of pages, or None if unknown
        """
        if self.total is None or self.page_size == 0:
            return None
        return math.ceil(self.total / self.page_size)


class PaginatedResults(Generic[T]):
    """Paginated results.

    This class represents a collection of results that can be paginated.
    """

    def __init__(
        self,
        items: Sequence[T],
        config: PaginationConfig,
        total: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """Initialize paginated results.

        Args:
            items: The items in the collection
            config: The pagination configuration
            total: The total number of items (optional)
            metadata: Additional metadata (optional)
        """
        self.items = items
        self.config = config
        self.total = total
        self.metadata = metadata or {}

    def get_page(self) -> Page[T]:
        """Get the current page.

        Returns:
            The current page
        """
        # Calculate page parameters based on strategy
        if self.config.strategy == PaginationStrategy.OFFSET:
            offset = self.config.offset
            limit = self.config.limit or self.config.page_size
            page_number = (offset // limit) + 1 if limit > 0 else 1
            has_previous = offset > 0
            has_next = (
                self.total is not None
                and offset + len(self.items) < self.total
                or len(self.items) >= limit
            )
            return Page(
                items=list(self.items),
                total=self.total,
                page_size=limit,
                page_number=page_number,
                has_next=has_next,
                has_previous=has_previous,
                metadata=self.metadata.copy(),
            )
        elif self.config.strategy == PaginationStrategy.PAGE:
            page_number = self.config.page
            page_size = self.config.page_size
            has_previous = page_number > 1
            has_next = (
                self.total is not None
                and (page_number * page_size) < self.total
                or len(self.items) >= page_size
            )
            return Page(
                items=list(self.items),
                total=self.total,
                page_size=page_size,
                page_number=page_number,
                has_next=has_next,
                has_previous=has_previous,
                metadata=self.metadata.copy(),
            )
        elif self.config.strategy == PaginationStrategy.CURSOR:
            # For cursor-based pagination, we need to extract cursors from the items
            # This is a simplified implementation; in practice, you would need to
            # extract cursors from the items based on your data model
            next_cursor = None
            previous_cursor = None
            if self.items:
                if hasattr(self.items[-1], "id"):
                    next_cursor = getattr(self.items[-1], "id")
                if hasattr(self.items[0], "id"):
                    previous_cursor = getattr(self.items[0], "id")
            return Page(
                items=list(self.items),
                total=self.total,
                page_size=self.config.page_size,
                has_next=bool(next_cursor),
                has_previous=bool(previous_cursor),
                next_cursor=next_cursor,
                previous_cursor=previous_cursor,
                metadata=self.metadata.copy(),
            )
        elif self.config.strategy == PaginationStrategy.TIME:
            # For time-based pagination, we need to extract timestamps from the items
            # This is a simplified implementation; in practice, you would need to
            # extract timestamps from the items based on your data model
            next_timestamp = None
            previous_timestamp = None
            if self.items:
                if hasattr(self.items[-1], "timestamp"):
                    next_timestamp = getattr(self.items[-1], "timestamp")
                if hasattr(self.items[0], "timestamp"):
                    previous_timestamp = getattr(self.items[0], "timestamp")
            return Page(
                items=list(self.items),
                total=self.total,
                page_size=self.config.page_size,
                has_next=bool(next_timestamp),
                has_previous=bool(previous_timestamp),
                next_timestamp=next_timestamp,
                previous_timestamp=previous_timestamp,
                metadata=self.metadata.copy(),
            )
        else:
            # Default to simple pagination
            return Page(
                items=list(self.items),
                total=self.total,
                page_size=self.config.page_size,
                metadata=self.metadata.copy(),
            )

    def __iter__(self) -> IteratorType[T]:
        """Get an iterator over all items.

        Returns:
            Iterator over all items
        """
        return iter(self.items)

    def __len__(self) -> int:
        """Get the number of items in the current page.

        Returns:
            Number of items
        """
        return len(self.items)


@runtime_checkable
class Pageable(Protocol[T]):
    """Protocol for pageable objects.

    This protocol defines the interface for objects that can be paginated.
    """

    def get_page(self, config: PaginationConfig) -> Page[T]:
        """Get a page of results.

        Args:
            config: The pagination configuration

        Returns:
            A page of results
        """
        ...


@runtime_checkable
class AsyncPageable(Protocol[T]):
    """Protocol for asynchronously pageable objects.

    This protocol defines the interface for objects that can be paginated
    asynchronously.
    """

    async def get_page_async(self, config: PaginationConfig) -> Page[T]:
        """Get a page of results asynchronously.

        Args:
            config: The pagination configuration

        Returns:
            A page of results
        """
        ...


class PageIterator(Generic[T], Iterator[Page[T]]):
    """Iterator over pages.

    This class provides an iterator over pages of results.
    """

    def __init__(
        self,
        pageable: Pageable[T],
        config: Optional[PaginationConfig] = None,
        max_pages: Optional[int] = None,
    ):
        """Initialize page iterator.

        Args:
            pageable: The pageable object
            config: The initial pagination configuration (optional)
            max_pages: The maximum number of pages to iterate over (optional)
        """
        self.pageable = pageable
        self.config = config or PaginationConfig()
        self.max_pages = max_pages
        self.current_page: Optional[Page[T]] = None
        self.page_count = 0

    def __iter__(self) -> IteratorType[Page[T]]:
        """Get an iterator.

        Returns:
            The iterator
        """
        return self

    def __next__(self) -> Page[T]:
        """Get the next page.

        Returns:
            The next page

        Raises:
            StopIteration: If there are no more pages
        """
        # Check if we've reached the maximum number of pages
        if self.max_pages is not None and self.page_count >= self.max_pages:
            raise StopIteration

        # Get the current page
        if self.current_page is None:
            self.current_page = self.pageable.get_page(self.config)
            self.page_count += 1
            return self.current_page

        # Check if there are more pages
        if not self.current_page.has_next:
            raise StopIteration

        # Update configuration for the next page
        if self.config.strategy == PaginationStrategy.OFFSET:
            self.config.offset += len(self.current_page)
        elif self.config.strategy == PaginationStrategy.CURSOR:
            self.config.cursor = self.current_page.next_cursor
            self.config.direction = "forward"
        elif self.config.strategy == PaginationStrategy.PAGE:
            self.config.page += 1
        elif self.config.strategy == PaginationStrategy.TIME:
            if self.config.sort_order == "desc":
                self.config.before = self.current_page.next_timestamp
                self.config.after = None
            else:
                self.config.after = self.current_page.next_timestamp
                self.config.before = None

        # Get the next page
        self.current_page = self.pageable.get_page(self.config)
        self.page_count += 1
        return self.current_page


class AsyncPageIterator(Generic[T], AsyncIterator[Page[T]]):
    """Asynchronous iterator over pages.

    This class provides an asynchronous iterator over pages of results.
    """

    def __init__(
        self,
        pageable: AsyncPageable[T],
        config: Optional[PaginationConfig] = None,
        max_pages: Optional[int] = None,
    ):
        """Initialize asynchronous page iterator.

        Args:
            pageable: The pageable object
            config: The initial pagination configuration (optional)
            max_pages: The maximum number of pages to iterate over (optional)
        """
        self.pageable = pageable
        self.config = config or PaginationConfig()
        self.max_pages = max_pages
        self.current_page: Optional[Page[T]] = None
        self.page_count = 0

    def __aiter__(self) -> AsyncIteratorType[Page[T]]:
        """Get an asynchronous iterator.

        Returns:
            The asynchronous iterator
        """
        return self

    async def __anext__(self) -> Page[T]:
        """Get the next page asynchronously.

        Returns:
            The next page

        Raises:
            StopAsyncIteration: If there are no more pages
        """
        # Check if we've reached the maximum number of pages
        if self.max_pages is not None and self.page_count >= self.max_pages:
            raise StopAsyncIteration

        # Get the current page
        if self.current_page is None:
            self.current_page = await self.pageable.get_page_async(self.config)
            self.page_count += 1
            return self.current_page

        # Check if there are more pages
        if not self.current_page.has_next:
            raise StopAsyncIteration

        # Update configuration for the next page
        if self.config.strategy == PaginationStrategy.OFFSET:
            self.config.offset += len(self.current_page)
        elif self.config.strategy == PaginationStrategy.CURSOR:
            self.config.cursor = self.current_page.next_cursor
            self.config.direction = "forward"
        elif self.config.strategy == PaginationStrategy.PAGE:
            self.config.page += 1
        elif self.config.strategy == PaginationStrategy.TIME:
            if self.config.sort_order == "desc":
                self.config.before = self.current_page.next_timestamp
                self.config.after = None
            else:
                self.config.after = self.current_page.next_timestamp
                self.config.before = None

        # Get the next page
        self.current_page = await self.pageable.get_page_async(self.config)
        self.page_count += 1
        return self.current_page


class ItemIterator(Generic[T], Iterator[T]):
    """Iterator over items.

    This class provides an iterator over items across all pages.
    """

    def __init__(
        self,
        pageable: Pageable[T],
        config: Optional[PaginationConfig] = None,
        max_items: Optional[int] = None,
    ):
        """Initialize item iterator.

        Args:
            pageable: The pageable object
            config: The initial pagination configuration (optional)
            max_items: The maximum number of items to iterate over (optional)
        """
        self.page_iterator = PageIterator(pageable, config)
        self.max_items = max_items
        self.current_page: Optional[Page[T]] = None
        self.current_index = 0
        self.item_count = 0

    def __iter__(self) -> IteratorType[T]:
        """Get an iterator.

        Returns:
            The iterator
        """
        return self

    def __next__(self) -> T:
        """Get the next item.

        Returns:
            The next item

        Raises:
            StopIteration: If there are no more items
        """
        # Check if we've reached the maximum number of items
        if self.max_items is not None and self.item_count >= self.max_items:
            raise StopIteration

        # Get the current page if needed
        if self.current_page is None:
            self.current_page = next(self.page_iterator)
            self.current_index = 0

        # Check if we need to get the next page
        if self.current_index >= len(self.current_page):
            self.current_page = next(self.page_iterator)
            self.current_index = 0

        # Get the current item
        item = self.current_page[self.current_index]
        self.current_index += 1
        self.item_count += 1
        return item


class AsyncItemIterator(Generic[T], AsyncIterator[T]):
    """Asynchronous iterator over items.

    This class provides an asynchronous iterator over items across all pages.
    """

    def __init__(
        self,
        pageable: AsyncPageable[T],
        config: Optional[PaginationConfig] = None,
        max_items: Optional[int] = None,
    ):
        """Initialize asynchronous item iterator.

        Args:
            pageable: The pageable object
            config: The initial pagination configuration (optional)
            max_items: The maximum number of items to iterate over (optional)
        """
        self.page_iterator = AsyncPageIterator(pageable, config)
        self.max_items = max_items
        self.current_page: Optional[Page[T]] = None
        self.current_index = 0
        self.item_count = 0

    def __aiter__(self) -> AsyncIteratorType[T]:
        """Get an asynchronous iterator.

        Returns:
            The asynchronous iterator
        """
        return self

    async def __anext__(self) -> T:
        """Get the next item asynchronously.

        Returns:
            The next item

        Raises:
            StopAsyncIteration: If there are no more items
        """
        # Check if we've reached the maximum number of items
        if self.max_items is not None and self.item_count >= self.max_items:
            raise StopAsyncIteration

        # Get the current page if needed
        if self.current_page is None:
            self.current_page = await self.page_iterator.__anext__()
            self.current_index = 0

        # Check if we need to get the next page
        if self.current_index >= len(self.current_page):
            self.current_page = await self.page_iterator.__anext__()
            self.current_index = 0

        # Get the current item
        item = self.current_page[self.current_index]
        self.current_index += 1
        self.item_count += 1
        return item


def paginate(
    items: Sequence[T],
    config: Optional[PaginationConfig] = None,
    total: Optional[int] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> PaginatedResults[T]:
    """Create paginated results from a sequence of items.

    Args:
        items: The items to paginate
        config: The pagination configuration (optional)
        total: The total number of items (optional)
        metadata: Additional metadata (optional)

    Returns:
        Paginated results
    """
    return PaginatedResults(
        items=items,
        config=config or PaginationConfig(),
        total=total,
        metadata=metadata,
    )


def create_page_iterator(
    pageable: Pageable[T],
    config: Optional[PaginationConfig] = None,
    max_pages: Optional[int] = None,
) -> PageIterator[T]:
    """Create a page iterator.

    Args:
        pageable: The pageable object
        config: The initial pagination configuration (optional)
        max_pages: The maximum number of pages to iterate over (optional)

    Returns:
        Page iterator
    """
    return PageIterator(pageable, config, max_pages)


def create_async_page_iterator(
    pageable: AsyncPageable[T],
    config: Optional[PaginationConfig] = None,
    max_pages: Optional[int] = None,
) -> AsyncPageIterator[T]:
    """Create an asynchronous page iterator.

    Args:
        pageable: The pageable object
        config: The initial pagination configuration (optional)
        max_pages: The maximum number of pages to iterate over (optional)

    Returns:
        Asynchronous page iterator
    """
    return AsyncPageIterator(pageable, config, max_pages)


def create_item_iterator(
    pageable: Pageable[T],
    config: Optional[PaginationConfig] = None,
    max_items: Optional[int] = None,
) -> ItemIterator[T]:
    """Create an item iterator.

    Args:
        pageable: The pageable object
        config: The initial pagination configuration (optional)
        max_items: The maximum number of items to iterate over (optional)

    Returns:
        Item iterator
    """
    return ItemIterator(pageable, config, max_items)


def create_async_item_iterator(
    pageable: AsyncPageable[T],
    config: Optional[PaginationConfig] = None,
    max_items: Optional[int] = None,
) -> AsyncItemIterator[T]:
    """Create an asynchronous item iterator.

    Args:
        pageable: The pageable object
        config: The initial pagination configuration (optional)
        max_items: The maximum number of items to iterate over (optional)

    Returns:
        Asynchronous item iterator
    """
    return AsyncItemIterator(pageable, config, max_items)
