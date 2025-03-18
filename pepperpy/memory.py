"""PepperPy Memory Module.

This module provides memory management functionality for the PepperPy framework, including:
- Memory storage and retrieval
- Different types of memory items (messages, facts, documents, interactions)
- Memory filtering and searching

The memory module is designed to be used by AI applications to store and retrieve
information across interactions, enabling context-aware and stateful applications.
"""

import time
from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Generic, List, Optional, TypeVar, Union

from pepperpy.core.errors import PepperPyError
from pepperpy.core.logging import get_logger

# Logger for this module
logger = get_logger(__name__)

# Type variable for memory item types
T = TypeVar("T")


class MemoryError(PepperPyError):
    """Error raised when a memory operation fails."""

    pass


class MemoryItemType(str, Enum):
    """Types of memory items."""

    MESSAGE = "message"
    FACT = "fact"
    DOCUMENT = "document"
    INTERACTION = "interaction"
    CUSTOM = "custom"


class MemoryItem:
    """Base class for memory items."""

    def __init__(
        self,
        content: str,
        item_type: Union[str, MemoryItemType] = MemoryItemType.CUSTOM,
        metadata: Optional[Dict[str, Any]] = None,
        timestamp: Optional[float] = None,
        item_id: Optional[str] = None,
    ):
        """Initialize a memory item.

        Args:
            content: The content of the memory item
            item_type: The type of the memory item
            metadata: Optional metadata for the memory item
            timestamp: Optional timestamp for the memory item (defaults to current time)
            item_id: Optional ID for the memory item (defaults to a generated ID)
        """
        self.content = content
        self.item_type = (
            item_type
            if isinstance(item_type, MemoryItemType)
            else MemoryItemType(item_type)
        )
        self.metadata = metadata or {}
        self.timestamp = timestamp or time.time()
        self.item_id = item_id or f"{self.item_type.value}_{int(self.timestamp * 1000)}"

    @property
    def datetime(self) -> datetime:
        """Get the datetime representation of the timestamp.

        Returns:
            The datetime representation of the timestamp
        """
        return datetime.fromtimestamp(self.timestamp)

    def to_dict(self) -> Dict[str, Any]:
        """Convert the memory item to a dictionary.

        Returns:
            A dictionary representation of the memory item
        """
        return {
            "item_id": self.item_id,
            "content": self.content,
            "item_type": self.item_type.value,
            "metadata": self.metadata,
            "timestamp": self.timestamp,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MemoryItem":
        """Create a memory item from a dictionary.

        Args:
            data: The dictionary to create the memory item from

        Returns:
            The created memory item
        """
        return cls(
            content=data["content"],
            item_type=data["item_type"],
            metadata=data.get("metadata", {}),
            timestamp=data.get("timestamp"),
            item_id=data.get("item_id"),
        )

    def __str__(self) -> str:
        """Get a string representation of the memory item.

        Returns:
            A string representation of the memory item
        """
        return f"{self.item_type.value}: {self.content}"


class Message(MemoryItem):
    """A message memory item."""

    def __init__(
        self,
        content: str,
        role: str,
        metadata: Optional[Dict[str, Any]] = None,
        timestamp: Optional[float] = None,
        item_id: Optional[str] = None,
    ):
        """Initialize a message memory item.

        Args:
            content: The content of the message
            role: The role of the message sender
            metadata: Optional metadata for the message
            timestamp: Optional timestamp for the message (defaults to current time)
            item_id: Optional ID for the message (defaults to a generated ID)
        """
        metadata = metadata or {}
        metadata["role"] = role
        super().__init__(
            content=content,
            item_type=MemoryItemType.MESSAGE,
            metadata=metadata,
            timestamp=timestamp,
            item_id=item_id,
        )

    @property
    def role(self) -> str:
        """Get the role of the message sender.

        Returns:
            The role of the message sender
        """
        return self.metadata.get("role", "")


class Fact(MemoryItem):
    """A fact memory item."""

    def __init__(
        self,
        content: str,
        source: Optional[str] = None,
        confidence: float = 1.0,
        metadata: Optional[Dict[str, Any]] = None,
        timestamp: Optional[float] = None,
        item_id: Optional[str] = None,
    ):
        """Initialize a fact memory item.

        Args:
            content: The content of the fact
            source: Optional source of the fact
            confidence: Optional confidence level of the fact (0.0 to 1.0)
            metadata: Optional metadata for the fact
            timestamp: Optional timestamp for the fact (defaults to current time)
            item_id: Optional ID for the fact (defaults to a generated ID)
        """
        metadata = metadata or {}
        if source is not None:
            metadata["source"] = source
        metadata["confidence"] = confidence
        super().__init__(
            content=content,
            item_type=MemoryItemType.FACT,
            metadata=metadata,
            timestamp=timestamp,
            item_id=item_id,
        )

    @property
    def source(self) -> Optional[str]:
        """Get the source of the fact.

        Returns:
            The source of the fact, or None if not set
        """
        return self.metadata.get("source")

    @property
    def confidence(self) -> float:
        """Get the confidence level of the fact.

        Returns:
            The confidence level of the fact (0.0 to 1.0)
        """
        return self.metadata.get("confidence", 1.0)


class Document(MemoryItem):
    """A document memory item."""

    def __init__(
        self,
        content: str,
        title: Optional[str] = None,
        source: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        timestamp: Optional[float] = None,
        item_id: Optional[str] = None,
    ):
        """Initialize a document memory item.

        Args:
            content: The content of the document
            title: Optional title of the document
            source: Optional source of the document
            metadata: Optional metadata for the document
            timestamp: Optional timestamp for the document (defaults to current time)
            item_id: Optional ID for the document (defaults to a generated ID)
        """
        metadata = metadata or {}
        if title is not None:
            metadata["title"] = title
        if source is not None:
            metadata["source"] = source
        super().__init__(
            content=content,
            item_type=MemoryItemType.DOCUMENT,
            metadata=metadata,
            timestamp=timestamp,
            item_id=item_id,
        )

    @property
    def title(self) -> Optional[str]:
        """Get the title of the document.

        Returns:
            The title of the document, or None if not set
        """
        return self.metadata.get("title")

    @property
    def source(self) -> Optional[str]:
        """Get the source of the document.

        Returns:
            The source of the document, or None if not set
        """
        return self.metadata.get("source")


class Interaction(MemoryItem):
    """An interaction memory item."""

    def __init__(
        self,
        content: str,
        interaction_type: str,
        metadata: Optional[Dict[str, Any]] = None,
        timestamp: Optional[float] = None,
        item_id: Optional[str] = None,
    ):
        """Initialize an interaction memory item.

        Args:
            content: The content of the interaction
            interaction_type: The type of the interaction
            metadata: Optional metadata for the interaction
            timestamp: Optional timestamp for the interaction (defaults to current time)
            item_id: Optional ID for the interaction (defaults to a generated ID)
        """
        metadata = metadata or {}
        metadata["interaction_type"] = interaction_type
        super().__init__(
            content=content,
            item_type=MemoryItemType.INTERACTION,
            metadata=metadata,
            timestamp=timestamp,
            item_id=item_id,
        )

    @property
    def interaction_type(self) -> str:
        """Get the type of the interaction.

        Returns:
            The type of the interaction
        """
        return self.metadata.get("interaction_type", "")


class MemoryFilter:
    """Filter for memory items."""

    def __init__(
        self,
        item_type: Optional[Union[str, MemoryItemType]] = None,
        start_time: Optional[float] = None,
        end_time: Optional[float] = None,
        metadata_filters: Optional[Dict[str, Any]] = None,
        content_filter: Optional[str] = None,
        limit: Optional[int] = None,
        offset: int = 0,
        sort_by: str = "timestamp",
        sort_order: str = "desc",
    ):
        """Initialize a memory filter.

        Args:
            item_type: Optional type of memory items to filter for
            start_time: Optional start time for filtering (inclusive)
            end_time: Optional end time for filtering (inclusive)
            metadata_filters: Optional metadata filters
            content_filter: Optional content filter (substring match)
            limit: Optional maximum number of items to return
            offset: Optional offset for pagination
            sort_by: Optional field to sort by (default: timestamp)
            sort_order: Optional sort order (asc or desc, default: desc)
        """
        self.item_type = (
            item_type
            if item_type is None or isinstance(item_type, MemoryItemType)
            else MemoryItemType(item_type)
        )
        self.start_time = start_time
        self.end_time = end_time
        self.metadata_filters = metadata_filters or {}
        self.content_filter = content_filter
        self.limit = limit
        self.offset = offset
        self.sort_by = sort_by
        self.sort_order = sort_order

    def to_dict(self) -> Dict[str, Any]:
        """Convert the filter to a dictionary.

        Returns:
            A dictionary representation of the filter
        """
        return {
            "item_type": self.item_type.value if self.item_type else None,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "metadata_filters": self.metadata_filters,
            "content_filter": self.content_filter,
            "limit": self.limit,
            "offset": self.offset,
            "sort_by": self.sort_by,
            "sort_order": self.sort_order,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MemoryFilter":
        """Create a filter from a dictionary.

        Args:
            data: The dictionary to create the filter from

        Returns:
            The created filter
        """
        return cls(
            item_type=data.get("item_type"),
            start_time=data.get("start_time"),
            end_time=data.get("end_time"),
            metadata_filters=data.get("metadata_filters"),
            content_filter=data.get("content_filter"),
            limit=data.get("limit"),
            offset=data.get("offset", 0),
            sort_by=data.get("sort_by", "timestamp"),
            sort_order=data.get("sort_order", "desc"),
        )


class MemoryStorageBase(Generic[T], ABC):
    """Base class for memory storage providers."""

    @abstractmethod
    async def add(self, item: T) -> T:
        """Add an item to storage.

        Args:
            item: The item to add

        Returns:
            The added item (with any modifications made by the storage)

        Raises:
            MemoryError: If the operation fails
        """
        pass

    @abstractmethod
    async def get(self, item_id: str) -> Optional[T]:
        """Get an item from storage.

        Args:
            item_id: The ID of the item to get

        Returns:
            The item, or None if not found

        Raises:
            MemoryError: If the operation fails
        """
        pass

    @abstractmethod
    async def update(self, item: T) -> T:
        """Update an item in storage.

        Args:
            item: The item to update

        Returns:
            The updated item

        Raises:
            MemoryError: If the operation fails or the item does not exist
        """
        pass

    @abstractmethod
    async def delete(self, item_id: str) -> bool:
        """Delete an item from storage.

        Args:
            item_id: The ID of the item to delete

        Returns:
            True if the item was deleted, False if it did not exist

        Raises:
            MemoryError: If the operation fails
        """
        pass

    @abstractmethod
    async def search(self, filter: MemoryFilter) -> List[T]:
        """Search for items in storage.

        Args:
            filter: The filter to apply

        Returns:
            A list of matching items

        Raises:
            MemoryError: If the operation fails
        """
        pass

    @abstractmethod
    async def clear(self) -> None:
        """Clear all items from storage.

        Raises:
            MemoryError: If the operation fails
        """
        pass


class InMemoryStorage(MemoryStorageBase[MemoryItem]):
    """In-memory storage for memory items."""

    def __init__(self):
        """Initialize in-memory storage."""
        self._items: Dict[str, MemoryItem] = {}

    async def add(self, item: MemoryItem) -> MemoryItem:
        """Add an item to storage.

        Args:
            item: The item to add

        Returns:
            The added item

        Raises:
            MemoryError: If an item with the same ID already exists
        """
        if item.item_id in self._items:
            raise MemoryError(f"Item with ID {item.item_id} already exists")

        self._items[item.item_id] = item
        return item

    async def get(self, item_id: str) -> Optional[MemoryItem]:
        """Get an item from storage.

        Args:
            item_id: The ID of the item to get

        Returns:
            The item, or None if not found
        """
        return self._items.get(item_id)

    async def update(self, item: MemoryItem) -> MemoryItem:
        """Update an item in storage.

        Args:
            item: The item to update

        Returns:
            The updated item

        Raises:
            MemoryError: If the item does not exist
        """
        if item.item_id not in self._items:
            raise MemoryError(f"Item with ID {item.item_id} does not exist")

        self._items[item.item_id] = item
        return item

    async def delete(self, item_id: str) -> bool:
        """Delete an item from storage.

        Args:
            item_id: The ID of the item to delete

        Returns:
            True if the item was deleted, False if it did not exist
        """
        if item_id not in self._items:
            return False

        del self._items[item_id]
        return True

    async def search(self, filter: MemoryFilter) -> List[MemoryItem]:
        """Search for items in storage.

        Args:
            filter: The filter to apply

        Returns:
            A list of matching items
        """
        results = []

        for item in self._items.values():
            # Filter by item type
            if filter.item_type and item.item_type != filter.item_type:
                continue

            # Filter by time range
            if filter.start_time and item.timestamp < filter.start_time:
                continue
            if filter.end_time and item.timestamp > filter.end_time:
                continue

            # Filter by content
            if (
                filter.content_filter
                and filter.content_filter.lower() not in item.content.lower()
            ):
                continue

            # Filter by metadata
            if filter.metadata_filters:
                match = True
                for key, value in filter.metadata_filters.items():
                    if key not in item.metadata or item.metadata[key] != value:
                        match = False
                        break
                if not match:
                    continue

            results.append(item)

        # Sort results
        if filter.sort_by == "timestamp":
            results.sort(
                key=lambda x: x.timestamp, reverse=(filter.sort_order == "desc")
            )
        elif filter.sort_by in ["item_id", "content", "item_type"]:
            results.sort(
                key=lambda x: getattr(x, filter.sort_by),
                reverse=(filter.sort_order == "desc"),
            )

        # Apply pagination
        if filter.offset > 0:
            results = results[filter.offset :]
        if filter.limit is not None:
            results = results[: filter.limit]

        return results

    async def clear(self) -> None:
        """Clear all items from storage."""
        self._items.clear()


class Memory:
    """Memory manager for storing and retrieving memory items."""

    def __init__(self, storage: Optional[MemoryStorageBase[MemoryItem]] = None):
        """Initialize a memory manager.

        Args:
            storage: Optional storage provider (defaults to InMemoryStorage)
        """
        self.storage = storage or InMemoryStorage()

    async def add_item(self, item: MemoryItem) -> MemoryItem:
        """Add an item to memory.

        Args:
            item: The item to add

        Returns:
            The added item

        Raises:
            MemoryError: If the operation fails
        """
        return await self.storage.add(item)

    async def add_message(
        self,
        content: str,
        role: str,
        metadata: Optional[Dict[str, Any]] = None,
        timestamp: Optional[float] = None,
    ) -> Message:
        """Add a message to memory.

        Args:
            content: The content of the message
            role: The role of the message sender
            metadata: Optional metadata for the message
            timestamp: Optional timestamp for the message

        Returns:
            The added message

        Raises:
            MemoryError: If the operation fails
        """
        message = Message(
            content=content,
            role=role,
            metadata=metadata,
            timestamp=timestamp,
        )
        await self.add_item(message)
        return message

    async def add_fact(
        self,
        content: str,
        source: Optional[str] = None,
        confidence: float = 1.0,
        metadata: Optional[Dict[str, Any]] = None,
        timestamp: Optional[float] = None,
    ) -> Fact:
        """Add a fact to memory.

        Args:
            content: The content of the fact
            source: Optional source of the fact
            confidence: Optional confidence level of the fact
            metadata: Optional metadata for the fact
            timestamp: Optional timestamp for the fact

        Returns:
            The added fact

        Raises:
            MemoryError: If the operation fails
        """
        fact = Fact(
            content=content,
            source=source,
            confidence=confidence,
            metadata=metadata,
            timestamp=timestamp,
        )
        await self.add_item(fact)
        return fact

    async def add_document(
        self,
        content: str,
        title: Optional[str] = None,
        source: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        timestamp: Optional[float] = None,
    ) -> Document:
        """Add a document to memory.

        Args:
            content: The content of the document
            title: Optional title of the document
            source: Optional source of the document
            metadata: Optional metadata for the document
            timestamp: Optional timestamp for the document

        Returns:
            The added document

        Raises:
            MemoryError: If the operation fails
        """
        document = Document(
            content=content,
            title=title,
            source=source,
            metadata=metadata,
            timestamp=timestamp,
        )
        await self.add_item(document)
        return document

    async def add_interaction(
        self,
        content: str,
        interaction_type: str,
        metadata: Optional[Dict[str, Any]] = None,
        timestamp: Optional[float] = None,
    ) -> Interaction:
        """Add an interaction to memory.

        Args:
            content: The content of the interaction
            interaction_type: The type of the interaction
            metadata: Optional metadata for the interaction
            timestamp: Optional timestamp for the interaction

        Returns:
            The added interaction

        Raises:
            MemoryError: If the operation fails
        """
        interaction = Interaction(
            content=content,
            interaction_type=interaction_type,
            metadata=metadata,
            timestamp=timestamp,
        )
        await self.add_item(interaction)
        return interaction

    async def get_item(self, item_id: str) -> Optional[MemoryItem]:
        """Get an item from memory.

        Args:
            item_id: The ID of the item to get

        Returns:
            The item, or None if not found

        Raises:
            MemoryError: If the operation fails
        """
        return await self.storage.get(item_id)

    async def update_item(self, item: MemoryItem) -> MemoryItem:
        """Update an item in memory.

        Args:
            item: The item to update

        Returns:
            The updated item

        Raises:
            MemoryError: If the operation fails or the item does not exist
        """
        return await self.storage.update(item)

    async def delete_item(self, item_id: str) -> bool:
        """Delete an item from memory.

        Args:
            item_id: The ID of the item to delete

        Returns:
            True if the item was deleted, False if it did not exist

        Raises:
            MemoryError: If the operation fails
        """
        return await self.storage.delete(item_id)

    async def search(self, filter: Optional[MemoryFilter] = None) -> List[MemoryItem]:
        """Search for items in memory.

        Args:
            filter: Optional filter to apply (defaults to an empty filter)

        Returns:
            A list of matching items

        Raises:
            MemoryError: If the operation fails
        """
        return await self.storage.search(filter or MemoryFilter())

    async def get_messages(
        self,
        role: Optional[str] = None,
        limit: Optional[int] = None,
        offset: int = 0,
    ) -> List[Message]:
        """Get messages from memory.

        Args:
            role: Optional role to filter by
            limit: Optional maximum number of messages to return
            offset: Optional offset for pagination

        Returns:
            A list of matching messages

        Raises:
            MemoryError: If the operation fails
        """
        metadata_filters = {}
        if role is not None:
            metadata_filters["role"] = role

        filter = MemoryFilter(
            item_type=MemoryItemType.MESSAGE,
            metadata_filters=metadata_filters,
            limit=limit,
            offset=offset,
            sort_by="timestamp",
            sort_order="desc",
        )

        items = await self.search(filter)
        return [item for item in items if isinstance(item, Message)]

    async def get_facts(
        self,
        source: Optional[str] = None,
        min_confidence: float = 0.0,
        limit: Optional[int] = None,
        offset: int = 0,
    ) -> List[Fact]:
        """Get facts from memory.

        Args:
            source: Optional source to filter by
            min_confidence: Optional minimum confidence level
            limit: Optional maximum number of facts to return
            offset: Optional offset for pagination

        Returns:
            A list of matching facts

        Raises:
            MemoryError: If the operation fails
        """
        metadata_filters = {}
        if source is not None:
            metadata_filters["source"] = source

        filter = MemoryFilter(
            item_type=MemoryItemType.FACT,
            metadata_filters=metadata_filters,
            limit=limit,
            offset=offset,
            sort_by="timestamp",
            sort_order="desc",
        )

        items = await self.search(filter)
        return [
            item
            for item in items
            if isinstance(item, Fact) and item.confidence >= min_confidence
        ]

    async def get_documents(
        self,
        title: Optional[str] = None,
        source: Optional[str] = None,
        limit: Optional[int] = None,
        offset: int = 0,
    ) -> List[Document]:
        """Get documents from memory.

        Args:
            title: Optional title to filter by
            source: Optional source to filter by
            limit: Optional maximum number of documents to return
            offset: Optional offset for pagination

        Returns:
            A list of matching documents

        Raises:
            MemoryError: If the operation fails
        """
        metadata_filters = {}
        if title is not None:
            metadata_filters["title"] = title
        if source is not None:
            metadata_filters["source"] = source

        filter = MemoryFilter(
            item_type=MemoryItemType.DOCUMENT,
            metadata_filters=metadata_filters,
            limit=limit,
            offset=offset,
            sort_by="timestamp",
            sort_order="desc",
        )

        items = await self.search(filter)
        return [item for item in items if isinstance(item, Document)]

    async def get_interactions(
        self,
        interaction_type: Optional[str] = None,
        limit: Optional[int] = None,
        offset: int = 0,
    ) -> List[Interaction]:
        """Get interactions from memory.

        Args:
            interaction_type: Optional interaction type to filter by
            limit: Optional maximum number of interactions to return
            offset: Optional offset for pagination

        Returns:
            A list of matching interactions

        Raises:
            MemoryError: If the operation fails
        """
        metadata_filters = {}
        if interaction_type is not None:
            metadata_filters["interaction_type"] = interaction_type

        filter = MemoryFilter(
            item_type=MemoryItemType.INTERACTION,
            metadata_filters=metadata_filters,
            limit=limit,
            offset=offset,
            sort_by="timestamp",
            sort_order="desc",
        )

        items = await self.search(filter)
        return [item for item in items if isinstance(item, Interaction)]

    async def clear(self) -> None:
        """Clear all items from memory.

        Raises:
            MemoryError: If the operation fails
        """
        await self.storage.clear()


def create_memory(storage: Optional[MemoryStorageBase[MemoryItem]] = None) -> Memory:
    """Create a memory manager.

    Args:
        storage: Optional storage provider (defaults to InMemoryStorage)

    Returns:
        A memory manager
    """
    return Memory(storage)


__all__ = [
    "MemoryError",
    "MemoryItemType",
    "MemoryItem",
    "Message",
    "Fact",
    "Document",
    "Interaction",
    "MemoryFilter",
    "MemoryStorageBase",
    "InMemoryStorage",
    "Memory",
    "create_memory",
]
