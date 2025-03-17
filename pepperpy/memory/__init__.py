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
    """Base class for all memory items.

    Memory items are the basic units of information stored in memory.
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
            item_id: The ID of the memory item (defaults to auto-generated ID)
        """
        self.content = content
        self.item_type = (
            item_type
            if isinstance(item_type, MemoryItemType)
            else MemoryItemType(item_type)
        )
        self.metadata = metadata or {}
        self.timestamp = timestamp or time.time()
        self.item_id = item_id or f"{self.item_type}_{int(self.timestamp * 1000)}"

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
            item_type=data.get("item_type", MemoryItemType.CUSTOM),
            metadata=data.get("metadata", {}),
            timestamp=data.get("timestamp"),
            item_id=data.get("item_id"),
        )

    def __str__(self) -> str:
        """Get the string representation of the memory item.

        Returns:
            The string representation of the memory item
        """
        return f"{self.item_type.value} ({self.datetime}): {self.content}"


class Message(MemoryItem):
    """Memory item representing a message.

    Messages are typically used to store conversation history.
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
            role: The role of the message sender (e.g., "user", "assistant")
            metadata: Additional metadata for the message
            timestamp: The timestamp of the message (defaults to current time)
            item_id: The ID of the message (defaults to auto-generated ID)
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
        return self.metadata.get("role", "unknown")


class Fact(MemoryItem):
    """Memory item representing a fact.

    Facts are typically used to store information about the world.
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
            confidence: The confidence score of the fact (0.0 to 1.0)
            metadata: Additional metadata for the fact
            timestamp: The timestamp of the fact (defaults to current time)
            item_id: The ID of the fact (defaults to auto-generated ID)
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
        """Get the confidence score of the fact.

        Returns:
            The confidence score of the fact
        """
        return float(self.metadata.get("confidence", 1.0))


class Document(MemoryItem):
    """Memory item representing a document.

    Documents are typically used to store text documents or articles.
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
            item_id: The ID of the document (defaults to auto-generated ID)
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
    """Memory item representing an interaction.

    Interactions are typically used to store user interactions with the system.
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
            item_id: The ID of the interaction (defaults to auto-generated ID)
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
    """Filter for searching memory.

    Memory filters are used to search for memory items that match specific criteria.
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
            metadata_filters: Filters to apply to memory item metadata
            content_filter: Filter to apply to memory item content
            limit: Maximum number of memory items to return
            offset: Number of memory items to skip
            sort_by: Field to sort memory items by
            sort_order: Sort order ("asc" or "desc")
        """
        self.item_type = (
            item_type
            if isinstance(item_type, MemoryItemType) or item_type is None
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
    """Base class for memory storage implementations.

    Memory storage implementations are responsible for storing and retrieving
    memory items.
    """

    @abstractmethod
    async def add(self, item: T) -> T:
        """Add a memory item.

        Args:
            item: The memory item to add

        Returns:
            The added memory item
        """
        pass

    @abstractmethod
    async def get(self, item_id: str) -> Optional[T]:
        """Get a memory item by ID.

        Args:
            item_id: The ID of the memory item to get

        Returns:
            The memory item with the given ID, or None if not found
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
            KeyError: If the memory item with the given ID does not exist
        """
        pass

    @abstractmethod
    async def delete(self, item_id: str) -> bool:
        """Delete a memory item by ID.

        Args:
            item_id: The ID of the memory item to delete

        Returns:
            True if the memory item was deleted, False if not found
        """
        pass

    @abstractmethod
    async def search(self, filter: MemoryFilter) -> List[T]:
        """Search for memory items.

        Args:
            filter: The filter to apply to the search

        Returns:
            A list of memory items that match the filter
        """
        pass

    @abstractmethod
    async def clear(self) -> None:
        """Clear all memory items."""
        pass


class InMemoryStorage(MemoryStorageBase[MemoryItem]):
    """In-memory implementation of memory storage.

    This implementation stores memory items in memory, which means they are lost
    when the process exits.
    """

    def __init__(self):
        """Initialize the storage."""
        self._items: Dict[str, MemoryItem] = {}

    async def add(self, item: MemoryItem) -> MemoryItem:
        """Add a memory item.

        Args:
            item: The memory item to add

        Returns:
            The added memory item
        """
        if item.item_id in self._items:
            logger.warning(f"Memory item {item.item_id} already exists, overwriting")

        self._items[item.item_id] = item
        logger.debug(f"Added memory item {item.item_id}")
        return item

    async def get(self, item_id: str) -> Optional[MemoryItem]:
        """Get a memory item by ID.

        Args:
            item_id: The ID of the memory item to get

        Returns:
            The memory item with the given ID, or None if not found
        """
        return self._items.get(item_id)

    async def update(self, item: MemoryItem) -> MemoryItem:
        """Update a memory item.

        Args:
            item: The memory item to update

        Returns:
            The updated memory item

        Raises:
            KeyError: If the memory item with the given ID does not exist
        """
        if item.item_id not in self._items:
            raise KeyError(f"Memory item {item.item_id} not found")

        self._items[item.item_id] = item
        logger.debug(f"Updated memory item {item.item_id}")
        return item

    async def delete(self, item_id: str) -> bool:
        """Delete a memory item by ID.

        Args:
            item_id: The ID of the memory item to delete

        Returns:
            True if the memory item was deleted, False if not found
        """
        if item_id not in self._items:
            logger.warning(f"Memory item {item_id} not found, cannot delete")
            return False

        del self._items[item_id]
        logger.debug(f"Deleted memory item {item_id}")
        return True

    async def search(self, filter: MemoryFilter) -> List[MemoryItem]:
        """Search for memory items.

        Args:
            filter: The filter to apply to the search

        Returns:
            A list of memory items that match the filter
        """
        results = []

        for item in self._items.values():
            # Check item type
            if filter.item_type and item.item_type != filter.item_type:
                continue

            # Check time range
            if filter.start_time and item.timestamp < filter.start_time:
                continue
            if filter.end_time and item.timestamp > filter.end_time:
                continue

            # Check content filter
            if (
                filter.content_filter
                and filter.content_filter.lower() not in item.content.lower()
            ):
                continue

            # Check metadata filters
            match = True
            for key, value in filter.metadata_filters.items():
                if key not in item.metadata or item.metadata[key] != value:
                    match = False
                    break
            if not match:
                continue

            results.append(item)

        # Sort results
        reverse = filter.sort_order.lower() == "desc"
        if filter.sort_by == "timestamp":
            results.sort(key=lambda x: x.timestamp, reverse=reverse)
        else:
            logger.warning(
                f"Sorting by {filter.sort_by} not supported, using timestamp"
            )
            results.sort(key=lambda x: x.timestamp, reverse=reverse)

        # Apply offset and limit
        start = filter.offset
        end = start + filter.limit if filter.limit else len(results)
        return results[start:end]

    async def clear(self) -> None:
        """Clear all memory items."""
        self._items.clear()
        logger.debug("Cleared all memory items")


class Memory:
    """Memory for storing and retrieving information.

    Memory is used to store and retrieve information across interactions.
    """

    def __init__(self, storage: Optional[MemoryStorageBase[MemoryItem]] = None):
        """Initialize the memory.

        Args:
            storage: The storage to use for memory items (defaults to InMemoryStorage)
        """
        self.storage = storage or InMemoryStorage()

    async def add_item(self, item: MemoryItem) -> MemoryItem:
        """Add a memory item.

        Args:
            item: The memory item to add

        Returns:
            The added memory item
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
            role: The role of the message sender (e.g., "user", "assistant")
            metadata: Additional metadata for the message
            timestamp: The timestamp of the message (defaults to current time)

        Returns:
            The added message
        """
        message = Message(
            content=content,
            role=role,
            metadata=metadata,
            timestamp=timestamp,
        )
        await self.storage.add(message)
        logger.debug(f"Added message from {role}")
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
            source: The source of the fact
            confidence: The confidence score of the fact (0.0 to 1.0)
            metadata: Additional metadata for the fact
            timestamp: The timestamp of the fact (defaults to current time)

        Returns:
            The added fact
        """
        fact = Fact(
            content=content,
            source=source,
            confidence=confidence,
            metadata=metadata,
            timestamp=timestamp,
        )
        await self.storage.add(fact)
        logger.debug(f"Added fact: {content}")
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
            title: The title of the document
            source: The source of the document
            metadata: Additional metadata for the document
            timestamp: The timestamp of the document (defaults to current time)

        Returns:
            The added document
        """
        document = Document(
            content=content,
            title=title,
            source=source,
            metadata=metadata,
            timestamp=timestamp,
        )
        await self.storage.add(document)
        logger.debug(f"Added document: {title or 'untitled'}")
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
            metadata: Additional metadata for the interaction
            timestamp: The timestamp of the interaction (defaults to current time)

        Returns:
            The added interaction
        """
        interaction = Interaction(
            content=content,
            interaction_type=interaction_type,
            metadata=metadata,
            timestamp=timestamp,
        )
        await self.storage.add(interaction)
        logger.debug(f"Added interaction: {interaction_type}")
        return interaction

    async def get_item(self, item_id: str) -> Optional[MemoryItem]:
        """Get a memory item by ID.

        Args:
            item_id: The ID of the memory item to get

        Returns:
            The memory item with the given ID, or None if not found
        """
        return await self.storage.get(item_id)

    async def update_item(self, item: MemoryItem) -> MemoryItem:
        """Update a memory item.

        Args:
            item: The memory item to update

        Returns:
            The updated memory item

        Raises:
            KeyError: If the memory item with the given ID does not exist
        """
        return await self.storage.update(item)

    async def delete_item(self, item_id: str) -> bool:
        """Delete a memory item by ID.

        Args:
            item_id: The ID of the memory item to delete

        Returns:
            True if the memory item was deleted, False if not found
        """
        return await self.storage.delete(item_id)

    async def search(self, filter: Optional[MemoryFilter] = None) -> List[MemoryItem]:
        """Search for memory items.

        Args:
            filter: The filter to apply to the search (defaults to no filter)

        Returns:
            A list of memory items that match the filter
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
            role: Filter by role (e.g., "user", "assistant")
            limit: Maximum number of messages to return
            offset: Number of messages to skip

        Returns:
            A list of messages that match the filter
        """
        # Create filter
        filter = MemoryFilter(
            item_type=MemoryItemType.MESSAGE,
            limit=limit,
            offset=offset,
            sort_by="timestamp",
            sort_order="desc",
        )

        # Add metadata filter for role
        if role:
            filter.metadata_filters["role"] = role

        # Search for messages
        items = await self.storage.search(filter)

        # Convert to Message objects
        messages: List[Message] = []
        for item in items:
            if isinstance(item, Message):
                messages.append(item)
            else:
                logger.warning(
                    f"Found non-Message item with type {item.item_type.value}"
                )

        return messages

    async def get_facts(
        self,
        source: Optional[str] = None,
        min_confidence: float = 0.0,
        limit: Optional[int] = None,
        offset: int = 0,
    ) -> List[Fact]:
        """Get facts from memory.

        Args:
            source: Filter by source
            min_confidence: Minimum confidence score
            limit: Maximum number of facts to return
            offset: Number of facts to skip

        Returns:
            A list of facts that match the filter
        """
        # Create filter
        filter = MemoryFilter(
            item_type=MemoryItemType.FACT,
            limit=limit,
            offset=offset,
            sort_by="timestamp",
            sort_order="desc",
        )

        # Add metadata filter for source
        if source:
            filter.metadata_filters["source"] = source

        # Search for facts
        items = await self.storage.search(filter)

        # Convert to Fact objects and filter by confidence
        facts: List[Fact] = []
        for item in items:
            if isinstance(item, Fact) and item.confidence >= min_confidence:
                facts.append(item)
            elif not isinstance(item, Fact):
                logger.warning(f"Found non-Fact item with type {item.item_type.value}")

        return facts

    async def get_documents(
        self,
        title: Optional[str] = None,
        source: Optional[str] = None,
        limit: Optional[int] = None,
        offset: int = 0,
    ) -> List[Document]:
        """Get documents from memory.

        Args:
            title: Filter by title
            source: Filter by source
            limit: Maximum number of documents to return
            offset: Number of documents to skip

        Returns:
            A list of documents that match the filter
        """
        # Create filter
        filter = MemoryFilter(
            item_type=MemoryItemType.DOCUMENT,
            limit=limit,
            offset=offset,
            sort_by="timestamp",
            sort_order="desc",
        )

        # Add metadata filters
        if title:
            filter.metadata_filters["title"] = title
        if source:
            filter.metadata_filters["source"] = source

        # Search for documents
        items = await self.storage.search(filter)

        # Convert to Document objects
        documents: List[Document] = []
        for item in items:
            if isinstance(item, Document):
                documents.append(item)
            else:
                logger.warning(
                    f"Found non-Document item with type {item.item_type.value}"
                )

        return documents

    async def get_interactions(
        self,
        interaction_type: Optional[str] = None,
        limit: Optional[int] = None,
        offset: int = 0,
    ) -> List[Interaction]:
        """Get interactions from memory.

        Args:
            interaction_type: Filter by interaction type
            limit: Maximum number of interactions to return
            offset: Number of interactions to skip

        Returns:
            A list of interactions that match the filter
        """
        # Create filter
        filter = MemoryFilter(
            item_type=MemoryItemType.INTERACTION,
            limit=limit,
            offset=offset,
            sort_by="timestamp",
            sort_order="desc",
        )

        # Add metadata filter for interaction type
        if interaction_type:
            filter.metadata_filters["interaction_type"] = interaction_type

        # Search for interactions
        items = await self.storage.search(filter)

        # Convert to Interaction objects
        interactions: List[Interaction] = []
        for item in items:
            if isinstance(item, Interaction):
                interactions.append(item)
            else:
                logger.warning(
                    f"Found non-Interaction item with type {item.item_type.value}"
                )

        return interactions

    async def clear(self) -> None:
        """Clear all memory items."""
        await self.storage.clear()


def create_memory(storage: Optional[MemoryStorageBase[MemoryItem]] = None) -> Memory:
    """Create a memory instance.

    Args:
        storage: The storage to use for memory items (defaults to InMemoryStorage)

    Returns:
        The created memory instance
    """
    return Memory(storage=storage)


# __all__ defines the public API
__all__ = [
    # Classes
    "Document",
    "Fact",
    "Interaction",
    "InMemoryStorage",
    "Memory",
    "MemoryFilter",
    "MemoryItem",
    "MemoryItemType",
    "MemoryStorageBase",
    "Message",
    # Functions
    "create_memory",
]
