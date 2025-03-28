"""Hierarchical memory system for agents.

This module provides a hierarchical memory system for agents, with different
memory types for different purposes.
"""

import asyncio
import json
import os
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple

from pepperpy.agents.base import Memory, Message


class MemoryType(Enum):
    """Types of memory in the hierarchical system."""

    WORKING = "working"  # Short-term, active context
    EPISODIC = "episodic"  # Experiences and interactions
    SEMANTIC = "semantic"  # Knowledge, facts, concepts
    PROCEDURAL = "procedural"  # Skills, procedures, patterns


@dataclass
class MemoryItem:
    """Item stored in memory."""

    content: Any
    memory_type: MemoryType
    timestamp: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)
    embedding: Optional[List[float]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "content": self.content
            if not isinstance(self.content, Message)
            else {"role": self.content.role, "content": self.content.content},
            "memory_type": self.memory_type.value,
            "timestamp": self.timestamp,
            "metadata": self.metadata,
            "embedding": self.embedding,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MemoryItem":
        """Create from dictionary."""
        content = data["content"]
        if isinstance(content, dict) and "role" in content and "content" in content:
            content = Message(role=content["role"], content=content["content"])

        return cls(
            content=content,
            memory_type=MemoryType(data["memory_type"]),
            timestamp=data["timestamp"],
            metadata=data["metadata"],
            embedding=data.get("embedding"),
        )


class HierarchicalMemory(Memory):
    """Hierarchical memory system for agents.

    This implementation provides multiple types of memory:
    - Working memory: short-term context for current processing
    - Episodic memory: experiences and interactions
    - Semantic memory: knowledge, facts, concepts
    - Procedural memory: skills, procedures, patterns
    """

    def __init__(
        self,
        embeddings_provider=None,
        storage_provider=None,
        working_memory_limit: int = 100,
        episodic_memory_limit: int = 1000,
        persistence_path: Optional[str] = None,
    ):
        """Initialize hierarchical memory."""
        self._embeddings = embeddings_provider
        self._storage = storage_provider
        self._working_memory_limit = working_memory_limit
        self._episodic_memory_limit = episodic_memory_limit
        self._persistence_path = persistence_path

        # Memory stores
        self._working_memory: List[MemoryItem] = []
        self._episodic_memory: List[MemoryItem] = []
        self._semantic_memory: Dict[str, MemoryItem] = {}
        self._procedural_memory: Dict[str, MemoryItem] = {}

        # Thread safety
        self._lock = asyncio.Lock()
        self._initialized = False

    async def _ensure_initialized(self) -> None:
        """Ensure memory is initialized."""
        if not self._initialized:
            # Load persisted memory if path provided
            if self._persistence_path and os.path.exists(self._persistence_path):
                await self._load()

            self._initialized = True

    # Memory interface implementation
    async def save(self, path: Optional[str] = None) -> None:
        """Save memory to storage."""
        target_path = path or self._persistence_path
        if not target_path:
            return

        await self._save(target_path)

    async def load(self, path: Optional[str] = None) -> None:
        """Load memory from storage."""
        target_path = path or self._persistence_path
        if not target_path or not os.path.exists(target_path):
            return

        await self._load()

    # Message methods
    async def add_message(self, message: Message) -> None:
        """Add a message to memory."""
        async with self._lock:
            await self._ensure_initialized()

            # Store in working memory (most recent context)
            self._add_to_working_memory(
                MemoryItem(
                    content=message,
                    memory_type=MemoryType.WORKING,
                    metadata={"role": message.role},
                )
            )

            # Store in episodic memory (conversation history)
            self._add_to_episodic_memory(
                MemoryItem(
                    content=message,
                    memory_type=MemoryType.EPISODIC,
                    metadata={"role": message.role, "type": "message"},
                )
            )

    async def get_messages(self) -> List[Message]:
        """Get all messages from memory."""
        async with self._lock:
            await self._ensure_initialized()

            # Get from working memory for immediate context
            messages = []
            for item in self._working_memory:
                if isinstance(item.content, Message):
                    messages.append(item.content)

            return messages

    async def get_messages_by_role(self, role: str) -> List[Message]:
        """Get messages from a specific role."""
        async with self._lock:
            await self._ensure_initialized()

            # Get from working memory
            messages = []
            for item in self._working_memory:
                if isinstance(item.content, Message) and item.content.role == role:
                    messages.append(item.content)

            return messages

    # Semantic memory methods
    async def store_knowledge(
        self, key: str, content: Any, metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Store knowledge in semantic memory."""
        async with self._lock:
            await self._ensure_initialized()

            # Create memory item
            item = MemoryItem(
                content=content,
                memory_type=MemoryType.SEMANTIC,
                metadata=metadata or {},
            )

            # Generate embedding if provider available
            if self._embeddings and isinstance(content, str):
                try:
                    embedding = await self._get_embedding(content)
                    item.embedding = embedding
                except Exception:
                    # Fail gracefully if embedding generation fails
                    pass

            self._semantic_memory[key] = item

            # Persist if path configured
            if self._persistence_path:
                await self.save()

    async def retrieve_knowledge(self, key: str) -> Optional[Any]:
        """Retrieve knowledge from semantic memory."""
        async with self._lock:
            await self._ensure_initialized()

            item = self._semantic_memory.get(key)
            return item.content if item else None

    async def search_semantic_memory(
        self, query: str, max_results: int = 5
    ) -> List[Tuple[float, Any]]:
        """Search semantic memory using embeddings similarity."""
        if not self._embeddings:
            return []

        async with self._lock:
            await self._ensure_initialized()

            try:
                # Generate query embedding
                query_embedding = await self._get_embedding(query)

                # Collect items with embeddings
                items_with_embeddings = [
                    (key, item)
                    for key, item in self._semantic_memory.items()
                    if item.embedding is not None
                ]

                if not items_with_embeddings:
                    return []

                # Calculate similarities
                similarities = []
                for key, item in items_with_embeddings:
                    if item.embedding:  # Check is not None
                        similarity = self._calculate_similarity(
                            query_embedding, item.embedding
                        )
                        similarities.append((similarity, item.content))

                # Sort by similarity (highest first) and return top results
                similarities.sort(reverse=True)
                return similarities[:max_results]

            except Exception:
                # Fail gracefully if similarity search fails
                return []

    # Procedural memory methods
    async def store_procedure(
        self, name: str, procedure: Any, metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Store a procedure in procedural memory."""
        async with self._lock:
            await self._ensure_initialized()

            self._procedural_memory[name] = MemoryItem(
                content=procedure,
                memory_type=MemoryType.PROCEDURAL,
                metadata=metadata or {},
            )

            # Persist if path configured
            if self._persistence_path:
                await self.save()

    async def retrieve_procedure(self, name: str) -> Optional[Any]:
        """Retrieve a procedure from procedural memory."""
        async with self._lock:
            await self._ensure_initialized()

            item = self._procedural_memory.get(name)
            return item.content if item else None

    # Episodic memory methods
    async def add_experience(
        self, experience: Any, metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Add an experience to episodic memory."""
        async with self._lock:
            await self._ensure_initialized()

            # Create memory item
            item = MemoryItem(
                content=experience,
                memory_type=MemoryType.EPISODIC,
                metadata=metadata or {"type": "experience"},
            )

            # Generate embedding if provider available and content is string
            if self._embeddings and isinstance(experience, str):
                try:
                    embedding = await self._get_embedding(experience)
                    item.embedding = embedding
                except Exception:
                    # Fail gracefully if embedding generation fails
                    pass

            self._add_to_episodic_memory(item)

            # Persist if path configured
            if self._persistence_path:
                await self.save()

    async def retrieve_experiences(
        self,
        filter_fn: Optional[Callable[[MemoryItem], bool]] = None,
        max_count: int = 10,
    ) -> List[Any]:
        """Retrieve experiences from episodic memory."""
        async with self._lock:
            await self._ensure_initialized()

            filtered = self._episodic_memory
            if filter_fn:
                filtered = [item for item in filtered if filter_fn(item)]

            # Sort by timestamp (most recent first) and limit
            sorted_items = sorted(filtered, key=lambda x: x.timestamp, reverse=True)
            return [item.content for item in sorted_items[:max_count]]

    async def search_experiences(
        self, query: str, max_results: int = 5
    ) -> List[Tuple[float, Any]]:
        """Search episodic memory using embeddings similarity."""
        if not self._embeddings:
            return []

        async with self._lock:
            await self._ensure_initialized()

            try:
                # Generate query embedding
                query_embedding = await self._get_embedding(query)

                # Collect items with embeddings
                items_with_embeddings = [
                    item for item in self._episodic_memory if item.embedding is not None
                ]

                if not items_with_embeddings:
                    return []

                # Calculate similarities
                similarities = []
                for item in items_with_embeddings:
                    if item.embedding:  # Check is not None
                        similarity = self._calculate_similarity(
                            query_embedding, item.embedding
                        )
                        similarities.append((similarity, item.content))

                # Sort by similarity (highest first) and return top results
                similarities.sort(reverse=True)
                return similarities[:max_results]

            except Exception:
                # Fail gracefully if similarity search fails
                return []

    # Utility methods
    async def clear(self) -> None:
        """Clear all memory."""
        async with self._lock:
            await self._ensure_initialized()

            self._working_memory.clear()
            self._episodic_memory.clear()
            self._semantic_memory.clear()
            self._procedural_memory.clear()

    async def _get_embedding(self, text: str) -> List[float]:
        """Get embedding for text using provider."""
        if not self._embeddings:
            raise ValueError("No embeddings provider configured")

        # Generically handle different embedding provider interfaces
        try:
            if hasattr(self._embeddings, "embed_query"):
                # LangChain style
                result = await self._embeddings.embed_query(text)
                return result
            elif hasattr(self._embeddings, "get_embeddings"):
                # Custom provider style
                result = await self._embeddings.get_embeddings([text])
                return result[0] if result else []
            elif hasattr(self._embeddings, "embed"):
                # OpenAI style
                result = await self._embeddings.embed(text)
                if isinstance(result, list):
                    return result
                # Handle object with embeddings attribute
                if hasattr(result, "embeddings") and result.embeddings:
                    return result.embeddings[0]
                return []
            elif callable(self._embeddings):
                # Direct callable
                result = await self._embeddings(text)
                return result if isinstance(result, list) else []
            else:
                raise ValueError("Unsupported embeddings provider interface")
        except Exception as e:
            raise ValueError(f"Failed to generate embedding: {e}")

    def _calculate_similarity(
        self, embedding1: List[float], embedding2: List[float]
    ) -> float:
        """Calculate cosine similarity between embeddings."""
        if not embedding1 or not embedding2:
            return 0.0

        # Cosine similarity
        dot_product = sum(a * b for a, b in zip(embedding1, embedding2))
        magnitude1 = sum(a * a for a in embedding1) ** 0.5
        magnitude2 = sum(b * b for b in embedding2) ** 0.5

        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0

        return dot_product / (magnitude1 * magnitude2)

    async def _save(self, path: str) -> None:
        """Save memory to storage."""
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(path), exist_ok=True)

            memory_data = {
                "working": [item.to_dict() for item in self._working_memory],
                "episodic": [item.to_dict() for item in self._episodic_memory],
                "semantic": {k: v.to_dict() for k, v in self._semantic_memory.items()},
                "procedural": {
                    k: v.to_dict() for k, v in self._procedural_memory.items()
                },
            }

            # Use storage provider if available, otherwise direct file
            if self._storage:
                # Generic handling for different storage provider interfaces
                if hasattr(self._storage, "save"):
                    await self._storage.save(path, memory_data)
                elif hasattr(self._storage, "write"):
                    await self._storage.write(path, memory_data)
                elif hasattr(self._storage, "store"):
                    await self._storage.store(path, memory_data)
                else:
                    # Fall back to direct file storage
                    with open(path, "w") as f:
                        json.dump(memory_data, f)
            else:
                # Direct file storage
                with open(path, "w") as f:
                    json.dump(memory_data, f)
        except Exception as e:
            print(f"Failed to save memory: {e}")

    async def _load(self) -> None:
        """Load memory from storage."""
        if not self._persistence_path or not os.path.exists(self._persistence_path):
            return

        try:
            # Use storage provider if available, otherwise direct file
            memory_data = None

            if self._storage:
                # Generic handling for different storage provider interfaces
                if hasattr(self._storage, "load"):
                    memory_data = await self._storage.load(self._persistence_path)
                elif hasattr(self._storage, "read"):
                    memory_data = await self._storage.read(self._persistence_path)
                elif hasattr(self._storage, "retrieve"):
                    memory_data = await self._storage.retrieve(self._persistence_path)

            # Fall back to direct file if no storage provider or method not found
            if memory_data is None:
                with open(self._persistence_path, "r") as f:
                    memory_data = json.load(f)

            # Load working memory
            self._working_memory = [
                MemoryItem.from_dict(item) for item in memory_data.get("working", [])
            ]

            # Load episodic memory
            self._episodic_memory = [
                MemoryItem.from_dict(item) for item in memory_data.get("episodic", [])
            ]

            # Load semantic memory
            self._semantic_memory = {
                k: MemoryItem.from_dict(v)
                for k, v in memory_data.get("semantic", {}).items()
            }

            # Load procedural memory
            self._procedural_memory = {
                k: MemoryItem.from_dict(v)
                for k, v in memory_data.get("procedural", {}).items()
            }
        except Exception as e:
            print(f"Failed to load memory: {e}")

    def _add_to_working_memory(self, item: MemoryItem) -> None:
        """Add an item to working memory, respecting the limit."""
        self._working_memory.append(item)

        # Enforce the working memory limit (FIFO)
        if len(self._working_memory) > self._working_memory_limit:
            # Remove oldest items
            excess = len(self._working_memory) - self._working_memory_limit
            self._working_memory = self._working_memory[excess:]

    def _add_to_episodic_memory(self, item: MemoryItem) -> None:
        """Add an item to episodic memory, respecting the limit."""
        self._episodic_memory.append(item)

        # Enforce the episodic memory limit (FIFO)
        if len(self._episodic_memory) > self._episodic_memory_limit:
            # Remove oldest items
            excess = len(self._episodic_memory) - self._episodic_memory_limit
            self._episodic_memory = self._episodic_memory[excess:]


class MemoryManager:
    """Memory manager for agents.

    This provides a facade over hierarchical memory to make it easy to use
    with PepperPy agents. It abstracts the memory management details and
    provides a convenient interface for agents to store and retrieve memory.
    """

    def __init__(
        self,
        embeddings_provider=None,
        storage_provider=None,
        working_memory_limit: int = 100,
        episodic_memory_limit: int = 1000,
        persistence_path: Optional[str] = None,
    ):
        """Initialize memory manager."""
        self.memory = HierarchicalMemory(
            embeddings_provider=embeddings_provider,
            storage_provider=storage_provider,
            working_memory_limit=working_memory_limit,
            episodic_memory_limit=episodic_memory_limit,
            persistence_path=persistence_path,
        )
        self._initialized = False
        self._lock = asyncio.Lock()

    async def __aenter__(self) -> "MemoryManager":
        """Initialize memory when used as context manager."""
        async with self._lock:
            if not self._initialized:
                await self.memory._ensure_initialized()
                self._initialized = True
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Clean up when exiting context."""
        if self._initialized and self.memory._persistence_path:
            await self.memory.save()

    # Message methods
    async def add_message(self, message: Message) -> None:
        """Add a message to memory."""
        await self.memory.add_message(message)

    async def store(self, memory_object: Any, key: Optional[str] = None) -> None:
        """Store any memory object.

        This method intelligently handles different types of memory objects:
        - Message: stored in both working and episodic memory
        - Other objects: stored in semantic memory with a key
        """
        if isinstance(memory_object, Message):
            await self.memory.add_message(memory_object)
        elif key:
            await self.memory.store_knowledge(key, memory_object)
        else:
            # Generate a key if not provided
            key = f"item_{int(time.time())}_{id(memory_object)}"
            await self.memory.store_knowledge(key, memory_object)

    async def get_messages(self) -> List[Message]:
        """Get all messages from memory."""
        return await self.memory.get_messages()

    # Knowledge (semantic memory) methods
    async def store_knowledge(
        self, key: str, content: Any, metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Store knowledge in semantic memory."""
        await self.memory.store_knowledge(key, content, metadata)

    async def retrieve_knowledge(self, key: str) -> Optional[Any]:
        """Retrieve knowledge from semantic memory."""
        return await self.memory.retrieve_knowledge(key)

    async def search_knowledge(
        self, query: str, max_results: int = 5
    ) -> List[Tuple[float, Any]]:
        """Search semantic memory using embeddings similarity."""
        return await self.memory.search_semantic_memory(query, max_results)

    # Procedures (procedural memory) methods
    async def store_procedure(
        self, name: str, procedure: Any, metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Store a procedure in procedural memory."""
        await self.memory.store_procedure(name, procedure, metadata)

    async def retrieve_procedure(self, name: str) -> Optional[Any]:
        """Retrieve a procedure from procedural memory."""
        return await self.memory.retrieve_procedure(name)

    # Experiences (episodic memory) methods
    async def add_experience(
        self, experience: Any, metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Add an experience to episodic memory."""
        await self.memory.add_experience(experience, metadata)

    async def retrieve_experiences(
        self,
        filter_fn: Optional[Callable[[MemoryItem], bool]] = None,
        max_count: int = 10,
    ) -> List[Any]:
        """Retrieve experiences from episodic memory."""
        return await self.memory.retrieve_experiences(filter_fn, max_count)

    async def search_experiences(
        self, query: str, max_results: int = 5
    ) -> List[Tuple[float, Any]]:
        """Search episodic memory using embeddings similarity."""
        return await self.memory.search_experiences(query, max_results)

    # Utility methods
    async def clear(self) -> None:
        """Clear all memory."""
        await self.memory.clear()

    async def save(self, path: Optional[str] = None) -> None:
        """Save memory to storage."""
        await self.memory.save(path)

    async def load(self, path: Optional[str] = None) -> None:
        """Load memory from storage."""
        await self.memory.load(path)
