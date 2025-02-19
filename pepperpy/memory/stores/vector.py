"""Vector memory store implementation.

This module implements a memory store using vector embeddings for semantic search.
Memory entries are stored with their vector embeddings for efficient similarity search.
"""

import json
from collections.abc import AsyncIterator
from pathlib import Path
from typing import Any, TypeVar, cast

# Import vector dependencies with proper error handling
try:
    import numpy as np  # type: ignore[import]
    import numpy.typing as npt  # type: ignore[import]
    from sentence_transformers import SentenceTransformer  # type: ignore[import]

    has_vector_deps = True
    NDArrayFloat = npt.NDArray[np.float32]  # type: ignore[name-defined]
except ImportError:
    has_vector_deps = False
    np = None  # type: ignore[assignment]
    npt = None  # type: ignore[assignment]
    SentenceTransformer = None  # type: ignore[assignment,valid-type]
    NDArrayFloat = Any  # type: ignore[misc,valid-type]

from pepperpy.core.logging import get_logger
from pepperpy.memory.base import (
    BaseMemoryStore,
    MemoryEntry,
    MemoryQuery,
    MemorySearchResult,
)
from pepperpy.memory.config import VectorStoreConfig
from pepperpy.memory.exceptions import MemoryError

# Type aliases
T = TypeVar("T")

logger = get_logger(__name__)


class VectorMemoryStore(BaseMemoryStore[dict[str, Any]]):
    """Vector memory store implementation.

    This store uses sentence transformers to create vector embeddings of content
    for semantic similarity search.
    """

    def __init__(self, config: VectorStoreConfig) -> None:
        """Initialize the vector store.

        Args:
            config: Store configuration

        Raises:
            ImportError: If required dependencies are not installed
        """
        if not has_vector_deps:
            raise ImportError(
                "Vector store dependencies not installed. "
                "Please install with 'pip install pepperpy[vector]'"
            )

        super().__init__("vector")
        self.config = config
        self.model = SentenceTransformer(str(config.model_name))  # type: ignore[operator]
        self.embeddings: NDArrayFloat | None = None  # type: ignore[valid-type]
        self.keys: list[str] = []
        self.storage_path = Path(str(config.storage_path or "data/vector_store"))
        self.storage_path.mkdir(parents=True, exist_ok=True)

    async def _initialize(self) -> None:
        """Initialize the vector store."""
        # Load existing embeddings if any
        if (self.storage_path / "embeddings.npy").exists():
            self.embeddings = cast(
                NDArrayFloat,  # type: ignore[valid-type]
                np.load(str(self.storage_path / "embeddings.npy")),  # type: ignore[union-attr]
            )
            with open(self.storage_path / "keys.json") as f:
                self.keys = json.load(f)

    async def _cleanup(self) -> None:
        """Clean up the vector store."""
        self.embeddings = None
        self.keys = []

    async def _store(self, entry: MemoryEntry[dict[str, Any]]) -> None:
        """Store a memory entry.

        Args:
            entry: Memory entry to store

        Raises:
            MemoryError: If storing fails
        """
        try:
            # Save entry data
            entry_path = self.storage_path / f"{entry.key}.json"
            entry_data = entry.model_dump()
            with open(entry_path, "w") as f:
                json.dump(entry_data, f)

            # Create and store embedding
            content_str = json.dumps(entry.value)
            embedding = cast(
                NDArrayFloat,  # type: ignore[valid-type]
                self.model.encode(  # type: ignore[union-attr]
                    content_str,
                    convert_to_numpy=True,
                    normalize_embeddings=True,
                ),
            )

            if self.embeddings is None:  # type: ignore[has-type]
                self.embeddings = embedding.reshape(1, -1)  # type: ignore[union-attr]
                self.keys = [entry.key]
            else:
                if entry.key in self.keys:
                    idx = self.keys.index(entry.key)
                    self.embeddings[idx] = embedding  # type: ignore[index]
                else:
                    self.embeddings = np.vstack([self.embeddings, embedding])  # type: ignore[union-attr]
                    self.keys.append(entry.key)

            # Save embeddings
            np.save(str(self.storage_path / "embeddings.npy"), self.embeddings)  # type: ignore[union-attr]
            with open(self.storage_path / "keys.json", "w") as f:
                json.dump(self.keys, f)

        except Exception as e:
            logger.error(
                "Failed to store in vector store",
                extra={"key": entry.key, "error": str(e)},
            )
            raise MemoryError(f"Failed to store in vector store: {e}") from e

    def _load_embeddings(self) -> None:
        """Load embeddings from storage if needed.

        This is a helper function to ensure embeddings are loaded when required.
        """
        if self.embeddings is None and (self.storage_path / "embeddings.npy").exists():
            self.embeddings = cast(
                NDArrayFloat,  # type: ignore[valid-type]
                np.load(str(self.storage_path / "embeddings.npy")),  # type: ignore[union-attr]
            )
            with open(self.storage_path / "keys.json") as f:
                self.keys = json.load(f)

    def _compute_similarities(self, query_text: str) -> list[tuple[str, float]]:
        """Compute similarity scores between query and stored embeddings.

        Args:
            query_text: The query text to compare against stored embeddings

        Returns:
            List of (key, similarity) pairs sorted by similarity
        """
        if self.embeddings is None:  # type: ignore[has-type]
            return []

        query_embedding = cast(
            NDArrayFloat,  # type: ignore[valid-type]
            self.model.encode(  # type: ignore[union-attr]
                query_text,
                convert_to_numpy=True,
                normalize_embeddings=True,
            ),
        )

        similarities = np.dot(self.embeddings, query_embedding)  # type: ignore[union-attr]
        return [
            (key, float(sim))
            for key, sim in zip(self.keys, similarities, strict=False)  # type: ignore[arg-type]
        ]

    def _load_entry(self, key: str) -> MemoryEntry[dict[str, Any]] | None:
        """Load a memory entry from storage.

        Args:
            key: The key of the entry to load

        Returns:
            The loaded memory entry or None if not found
        """
        entry_path = self.storage_path / f"{key}.json"
        if not entry_path.exists():
            return None

        with open(entry_path) as f:
            entry_data = json.load(f)
            return MemoryEntry[dict[str, Any]].model_validate(entry_data)

    def _matches_filters(
        self, entry: MemoryEntry[dict[str, Any]], query: MemoryQuery
    ) -> bool:
        """Check if an entry matches the query filters.

        Args:
            entry: The entry to check
            query: The query containing filters

        Returns:
            True if the entry matches all filters, False otherwise
        """
        if "type" in query.filters and entry.type != query.filters["type"]:
            return False
        if "scope" in query.filters and entry.scope != query.filters["scope"]:
            return False
        if query.metadata:
            if not entry.metadata:
                return False
            if not all(entry.metadata.get(k) == v for k, v in query.metadata.items()):
                return False
        return True

    def _retrieve(
        self,
        query: MemoryQuery,
    ) -> AsyncIterator[MemorySearchResult[dict[str, Any]]]:
        """Retrieve memory entries.

        Args:
            query: Memory query parameters.

        Yields:
            Memory search results.

        Raises:
            MemoryError: If retrieval fails.
        """

        async def retrieve_generator() -> (
            AsyncIterator[MemorySearchResult[dict[str, Any]]]
        ):
            try:
                # Ensure embeddings are loaded
                self._load_embeddings()
                if not self.embeddings is not None:  # type: ignore[has-type]
                    return

                # Get similarity scores
                matching_keys: list[tuple[str, float]] = [
                    (key, sim)
                    for key, sim in self._compute_similarities(query.query)
                    if sim >= query.min_score
                ]
                matching_keys.sort(key=lambda x: x[1], reverse=True)  # type: ignore[arg-type]

                # Process entries
                count = 0
                for key, similarity in matching_keys:
                    if query.limit and count >= query.limit:
                        break

                    entry = self._load_entry(key)
                    if entry is None:
                        continue

                    if not self._matches_filters(entry, query):
                        continue

                    yield MemorySearchResult(
                        entry=entry,
                        score=similarity,
                    )
                    count += 1

            except Exception as e:
                logger.error(
                    "Failed to retrieve from vector store",
                    extra={"query": query.model_dump(), "error": str(e)},
                )
                raise MemoryError(f"Failed to retrieve from vector store: {e}") from e

        return retrieve_generator()

    async def _delete(self, key: str) -> None:
        """Delete a memory entry.

        Args:
            key: The key of the entry to delete
        """
        if key not in self.keys:
            return

        # Delete entry file
        entry_path = self.storage_path / f"{key}.json"
        if entry_path.exists():
            entry_path.unlink()

        # Update embeddings
        if self.embeddings is not None:  # type: ignore[has-type]
            idx = self.keys.index(key)
            self.embeddings = np.delete(self.embeddings, idx, axis=0)  # type: ignore[union-attr]
            self.keys.remove(key)

            # Save updated embeddings
            np.save(str(self.storage_path / "embeddings.npy"), self.embeddings)  # type: ignore[union-attr]
            with open(self.storage_path / "keys.json", "w") as f:
                json.dump(self.keys, f)
