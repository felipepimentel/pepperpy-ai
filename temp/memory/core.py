"""Core functionality for memory management in PepperPy.

This module provides the core functionality for memory management in PepperPy,
including memory storage, retrieval, and manipulation.
"""

import time
from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Generic, List, Optional, TypeVar, Union

from pepperpy.utils.logging import get_logger

# Logger for this module
logger = get_logger(__name__)

# Type variable for memory item types
T = TypeVar("T")


class MemoryItemType(str, Enum):
    """Types of memory items."""

    MESSAGE = "message"
    FACT = "fact"
    DOCUMENT = "document"
    INTERACTION = "interaction"
    CUSTOM = "custom"


class MemoryItem:
    """Base class for memory items.

    A memory item is a piece of information that can be stored in memory.
    """

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
            metadata: Additional metadata for the memory item
            timestamp: The timestamp of the memory item (defaults to current time)
            item_id: The ID of the memory item (defaults to None, will be set by storage)
        """
        self.content = content
        self.item_type = (
            item_type
            if isinstance(item_type, MemoryItemType)
            else MemoryItemType(item_type)
        )
        self.metadata = metadata or {}
        self.timestamp = timestamp or time.time()
        self.item_id = item_id

    @property
    def datetime(self) -> datetime:
        """Get the datetime of the memory item.

        Returns:
            The datetime of the memory item
        """
        return datetime.fromtimestamp(self.timestamp)

    def to_dict(self) -> Dict[str, Any]:
        """Convert the memory item to a dictionary.

        Returns:
            The memory item as a dictionary
        """
        return {
            "content": self.content,
            "item_type": self.item_type.value,
            "metadata": self.metadata,
            "timestamp": self.timestamp,
            "item_id": self.item_id,
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
            metadata=data["metadata"],
            timestamp=data["timestamp"],
            item_id=data.get("item_id"),
        )

    def __str__(self) -> str:
        """Get a string representation of the memory item.

        Returns:
            A string representation of the memory item
        """
        return f"{self.item_type.value}: {self.content}"


class Message(MemoryItem):
    """A message memory item.

    A message is a piece of text sent by a user or assistant.
    """

    def __init__(
        self,
        content: str,
        role: str,
        metadata: Optional[Dict[str, Any]] = None,
        timestamp: Optional[float] = None,
        item_id: Optional[str] = None,
    ):
        """Initialize a message.

        Args:
            content: The content of the message
            role: The role of the sender (e.g., "user", "assistant")
            metadata: Additional metadata for the message
            timestamp: The timestamp of the message (defaults to current time)
            item_id: The ID of the message (defaults to None, will be set by storage)
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
        """Get the role of the sender.

        Returns:
            The role of the sender
        """
        return self.metadata.get("role", "unknown")


class Fact(MemoryItem):
    """A fact memory item.

    A fact is a piece of information that is known to be true.
    """

    def __init__(
        self,
        content: str,
        source: Optional[str] = None,
        confidence: float = 1.0,
        metadata: Optional[Dict[str, Any]] = None,
        timestamp: Optional[float] = None,
        item_id: Optional[str] = None,
    ):
        """Initialize a fact.

        Args:
            content: The content of the fact
            source: The source of the fact
            confidence: The confidence in the fact (0.0 to 1.0)
            metadata: Additional metadata for the fact
            timestamp: The timestamp of the fact (defaults to current time)
            item_id: The ID of the fact (defaults to None, will be set by storage)
        """
        metadata = metadata or {}
        if source:
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
            The source of the fact
        """
        return self.metadata.get("source")

    @property
    def confidence(self) -> float:
        """Get the confidence in the fact.

        Returns:
            The confidence in the fact
        """
        return self.metadata.get("confidence", 1.0)


class Document(MemoryItem):
    """A document memory item.

    A document is a piece of text from an external source.
    """

    def __init__(
        self,
        content: str,
        title: Optional[str] = None,
        source: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        timestamp: Optional[float] = None,
        item_id: Optional[str] = None,
    ):
        """Initialize a document.

        Args:
            content: The content of the document
            title: The title of the document
            source: The source of the document
            metadata: Additional metadata for the document
            timestamp: The timestamp of the document (defaults to current time)
            item_id: The ID of the document (defaults to None, will be set by storage)
        """
        metadata = metadata or {}
        if title:
            metadata["title"] = title
        if source:
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
            The title of the document
        """
        return self.metadata.get("title")

    @property
    def source(self) -> Optional[str]:
        """Get the source of the document.

        Returns:
            The source of the document
        """
        return self.metadata.get("source")


class Interaction(MemoryItem):
    """An interaction memory item.

    An interaction is a record of an interaction between the user and the system.
    """

    def __init__(
        self,
        content: str,
        interaction_type: str,
        metadata: Optional[Dict[str, Any]] = None,
        timestamp: Optional[float] = None,
        item_id: Optional[str] = None,
    ):
        """Initialize an interaction.

        Args:
            content: The content of the interaction
            interaction_type: The type of the interaction
            metadata: Additional metadata for the interaction
            timestamp: The timestamp of the interaction (defaults to current time)
            item_id: The ID of the interaction (defaults to None, will be set by storage)
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
        return self.metadata.get("interaction_type", "unknown")


class MemoryFilter:
    """Filter for memory items.

    A memory filter is used to filter memory items based on various criteria.
    """

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
            item_type: The type of memory items to filter for
            start_time: The minimum timestamp of memory items to include
            end_time: The maximum timestamp of memory items to include
            metadata_filters: Filters for metadata fields
            content_filter: Filter for the content field
            limit: The maximum number of memory items to return
            offset: The number of memory items to skip
            sort_by: The field to sort by
            sort_order: The sort order ("asc" or "desc")
        """
        self.item_type = (
            item_type
            if isinstance(item_type, MemoryItemType)
            else MemoryItemType(item_type)
            if item_type
            else None
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
        """Convert the memory filter to a dictionary.

        Returns:
            The memory filter as a dictionary
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
        """Create a memory filter from a dictionary.

        Args:
            data: The dictionary to create the memory filter from

        Returns:
            The created memory filter
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
    """Base class for memory storage.

    A memory storage is responsible for storing and retrieving memory items.
    """

    @abstractmethod
    async def add(self, item: T) -> T:
        """Add a memory item to storage.

        Args:
            item: The memory item to add

        Returns:
            The added memory item with its ID set
        """
        pass

    @abstractmethod
    async def get(self, item_id: str) -> Optional[T]:
        """Get a memory item by ID.

        Args:
            item_id: The ID of the memory item to get

        Returns:
            The memory item, or None if not found
        """
        pass

    @abstractmethod
    async def update(self, item: T) -> T:
        """Update a memory item.

        Args:
            item: The memory item to update

        Returns:
            The updated memory item

        Raises:
            ValueError: If the memory item does not have an ID
        """
        pass

    @abstractmethod
    async def delete(self, item_id: str) -> bool:
        """Delete a memory item by ID.

        Args:
            item_id: The ID of the memory item to delete

        Returns:
            True if the memory item was deleted, False otherwise
        """
        pass

    @abstractmethod
    async def search(self, filter: MemoryFilter) -> List[T]:
        """Search for memory items.

        Args:
            filter: The filter to apply

        Returns:
            The matching memory items
        """
        pass

    @abstractmethod
    async def clear(self) -> None:
        """Clear all memory items."""
        pass


class InMemoryStorage(MemoryStorageBase[MemoryItem]):
    """In-memory storage for memory items.

    This storage keeps memory items in memory, which means they are lost when the
    application is restarted.
    """

    def __init__(self):
        """Initialize in-memory storage."""
        self._items: Dict[str, MemoryItem] = {}
        self._next_id = 1

    async def add(self, item: MemoryItem) -> MemoryItem:
        """Add a memory item to storage.

        Args:
            item: The memory item to add

        Returns:
            The added memory item with its ID set
        """
        # Generate an ID if not provided
        if not item.item_id:
            item.item_id = str(self._next_id)
            self._next_id += 1

        # Store the item
        self._items[item.item_id] = item

        return item

    async def get(self, item_id: str) -> Optional[MemoryItem]:
        """Get a memory item by ID.

        Args:
            item_id: The ID of the memory item to get

        Returns:
            The memory item, or None if not found
        """
        return self._items.get(item_id)

    async def update(self, item: MemoryItem) -> MemoryItem:
        """Update a memory item.

        Args:
            item: The memory item to update

        Returns:
            The updated memory item

        Raises:
            ValueError: If the memory item does not have an ID
        """
        if not item.item_id:
            raise ValueError("Memory item does not have an ID")

        # Check if the item exists
        if item.item_id not in self._items:
            raise ValueError(f"Memory item with ID {item.item_id} not found")

        # Update the item
        self._items[item.item_id] = item

        return item

    async def delete(self, item_id: str) -> bool:
        """Delete a memory item by ID.

        Args:
            item_id: The ID of the memory item to delete

        Returns:
            True if the memory item was deleted, False otherwise
        """
        if item_id in self._items:
            del self._items[item_id]
            return True

        return False

    async def search(self, filter: MemoryFilter) -> List[MemoryItem]:
        """Search for memory items.

        Args:
            filter: The filter to apply

        Returns:
            The matching memory items
        """
        # Start with all items
        items = list(self._items.values())

        # Apply filters
        if filter.item_type:
            items = [item for item in items if item.item_type == filter.item_type]

        if filter.start_time:
            items = [item for item in items if item.timestamp >= filter.start_time]

        if filter.end_time:
            items = [item for item in items if item.timestamp <= filter.end_time]

        if filter.metadata_filters:
            for key, value in filter.metadata_filters.items():
                items = [item for item in items if item.metadata.get(key) == value]

        if filter.content_filter:
            items = [
                item
                for item in items
                if filter.content_filter.lower() in item.content.lower()
            ]

        # Sort items
        reverse = filter.sort_order.lower() == "desc"
        if filter.sort_by == "timestamp":
            items.sort(key=lambda item: item.timestamp, reverse=reverse)
        elif filter.sort_by == "content":
            items.sort(key=lambda item: item.content, reverse=reverse)

        # Apply offset and limit
        if filter.offset:
            items = items[filter.offset :]

        if filter.limit:
            items = items[: filter.limit]

        return items

    async def clear(self) -> None:
        """Clear all memory items."""
        self._items.clear()
        self._next_id = 1


class Memory:
    """Memory manager.

    The memory manager provides a high-level interface for working with memory items.
    """

    def __init__(self, storage: Optional[MemoryStorageBase[MemoryItem]] = None):
        """Initialize the memory manager.

        Args:
            storage: The storage to use (defaults to in-memory storage)
        """
        self.storage = storage or InMemoryStorage()

    async def add_item(self, item: MemoryItem) -> MemoryItem:
        """Add a memory item.

        Args:
            item: The memory item to add

        Returns:
            The added memory item with its ID set
        """
        return await self.storage.add(item)

    async def add_message(
        self,
        content: str,
        role: str,
        metadata: Optional[Dict[str, Any]] = None,
        timestamp: Optional[float] = None,
    ) -> Message:
        """Add a message.

        Args:
            content: The content of the message
            role: The role of the sender
            metadata: Additional metadata for the message
            timestamp: The timestamp of the message

        Returns:
            The added message with its ID set
        """
        message = Message(
            content=content,
            role=role,
            metadata=metadata,
            timestamp=timestamp,
        )

        await self.storage.add(message)

        return message

    async def add_fact(
        self,
        content: str,
        source: Optional[str] = None,
        confidence: float = 1.0,
        metadata: Optional[Dict[str, Any]] = None,
        timestamp: Optional[float] = None,
    ) -> Fact:
        """Add a fact.

        Args:
            content: The content of the fact
            source: The source of the fact
            confidence: The confidence in the fact
            metadata: Additional metadata for the fact
            timestamp: The timestamp of the fact

        Returns:
            The added fact with its ID set
        """
        fact = Fact(
            content=content,
            source=source,
            confidence=confidence,
            metadata=metadata,
            timestamp=timestamp,
        )

        await self.storage.add(fact)

        return fact

    async def add_document(
        self,
        content: str,
        title: Optional[str] = None,
        source: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        timestamp: Optional[float] = None,
    ) -> Document:
        """Add a document.

        Args:
            content: The content of the document
            title: The title of the document
            source: The source of the document
            metadata: Additional metadata for the document
            timestamp: The timestamp of the document

        Returns:
            The added document with its ID set
        """
        document = Document(
            content=content,
            title=title,
            source=source,
            metadata=metadata,
            timestamp=timestamp,
        )

        await self.storage.add(document)

        return document

    async def add_interaction(
        self,
        content: str,
        interaction_type: str,
        metadata: Optional[Dict[str, Any]] = None,
        timestamp: Optional[float] = None,
    ) -> Interaction:
        """Add an interaction.

        Args:
            content: The content of the interaction
            interaction_type: The type of the interaction
            metadata: Additional metadata for the interaction
            timestamp: The timestamp of the interaction

        Returns:
            The added interaction with its ID set
        """
        interaction = Interaction(
            content=content,
            interaction_type=interaction_type,
            metadata=metadata,
            timestamp=timestamp,
        )

        await self.storage.add(interaction)

        return interaction

    async def get_item(self, item_id: str) -> Optional[MemoryItem]:
        """Get a memory item by ID.

        Args:
            item_id: The ID of the memory item to get

        Returns:
            The memory item, or None if not found
        """
        return await self.storage.get(item_id)

    async def update_item(self, item: MemoryItem) -> MemoryItem:
        """Update a memory item.

        Args:
            item: The memory item to update

        Returns:
            The updated memory item

        Raises:
            ValueError: If the memory item does not have an ID
        """
        return await self.storage.update(item)

    async def delete_item(self, item_id: str) -> bool:
        """Delete a memory item by ID.

        Args:
            item_id: The ID of the memory item to delete

        Returns:
            True if the memory item was deleted, False otherwise
        """
        return await self.storage.delete(item_id)

    async def search(self, filter: Optional[MemoryFilter] = None) -> List[MemoryItem]:
        """Search for memory items.

        Args:
            filter: The filter to apply (defaults to no filter)

        Returns:
            The matching memory items
        """
        return await self.storage.search(filter or MemoryFilter())

    async def get_messages(
        self,
        role: Optional[str] = None,
        limit: Optional[int] = None,
        offset: int = 0,
    ) -> List[Message]:
        """Get messages.

        Args:
            role: The role of the sender to filter for
            limit: The maximum number of messages to return
            offset: The number of messages to skip

        Returns:
            The matching messages
        """
        # Create a filter for messages
        filter = MemoryFilter(
            item_type=MemoryItemType.MESSAGE,
            limit=limit,
            offset=offset,
            sort_by="timestamp",
            sort_order="desc",
        )

        # Add role filter if specified
        if role:
            filter.metadata_filters = {"role": role}

        # Search for messages
        items = await self.storage.search(filter)

        # Convert to Message objects
        messages = []
        for item in items:
            if isinstance(item, Message):
                messages.append(item)

        return messages

    async def get_facts(
        self,
        source: Optional[str] = None,
        min_confidence: float = 0.0,
        limit: Optional[int] = None,
        offset: int = 0,
    ) -> List[Fact]:
        """Get facts.

        Args:
            source: The source of the facts to filter for
            min_confidence: The minimum confidence of the facts to include
            limit: The maximum number of facts to return
            offset: The number of facts to skip

        Returns:
            The matching facts
        """
        # Create a filter for facts
        filter = MemoryFilter(
            item_type=MemoryItemType.FACT,
            limit=limit,
            offset=offset,
            sort_by="timestamp",
            sort_order="desc",
        )

        # Add source filter if specified
        if source:
            filter.metadata_filters = {"source": source}

        # Search for facts
        items = await self.storage.search(filter)

        # Convert to Fact objects and filter by confidence
        facts = []
        for item in items:
            if isinstance(item, Fact) and item.confidence >= min_confidence:
                facts.append(item)

        return facts

    async def get_documents(
        self,
        title: Optional[str] = None,
        source: Optional[str] = None,
        limit: Optional[int] = None,
        offset: int = 0,
    ) -> List[Document]:
        """Get documents.

        Args:
            title: The title of the documents to filter for
            source: The source of the documents to filter for
            limit: The maximum number of documents to return
            offset: The number of documents to skip

        Returns:
            The matching documents
        """
        # Create a filter for documents
        filter = MemoryFilter(
            item_type=MemoryItemType.DOCUMENT,
            limit=limit,
            offset=offset,
            sort_by="timestamp",
            sort_order="desc",
        )

        # Add title and source filters if specified
        metadata_filters = {}
        if title:
            metadata_filters["title"] = title
        if source:
            metadata_filters["source"] = source

        if metadata_filters:
            filter.metadata_filters = metadata_filters

        # Search for documents
        items = await self.storage.search(filter)

        # Convert to Document objects
        documents = []
        for item in items:
            if isinstance(item, Document):
                documents.append(item)

        return documents

    async def get_interactions(
        self,
        interaction_type: Optional[str] = None,
        limit: Optional[int] = None,
        offset: int = 0,
    ) -> List[Interaction]:
        """Get interactions.

        Args:
            interaction_type: The type of the interactions to filter for
            limit: The maximum number of interactions to return
            offset: The number of interactions to skip

        Returns:
            The matching interactions
        """
        # Create a filter for interactions
        filter = MemoryFilter(
            item_type=MemoryItemType.INTERACTION,
            limit=limit,
            offset=offset,
            sort_by="timestamp",
            sort_order="desc",
        )

        # Add interaction type filter if specified
        if interaction_type:
            filter.metadata_filters = {"interaction_type": interaction_type}

        # Search for interactions
        items = await self.storage.search(filter)

        # Convert to Interaction objects
        interactions = []
        for item in items:
            if isinstance(item, Interaction):
                interactions.append(item)

        return interactions

    async def clear(self) -> None:
        """Clear all memory items."""
        await self.storage.clear()


# Factory function to create a memory manager
def create_memory(storage: Optional[MemoryStorageBase[MemoryItem]] = None) -> Memory:
    """Create a memory manager.

    Args:
        storage: The storage to use (defaults to in-memory storage)

    Returns:
        The created memory manager
    """
    return Memory(storage=storage)
