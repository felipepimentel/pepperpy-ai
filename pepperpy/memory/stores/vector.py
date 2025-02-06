"""Vector memory store implementation.

This module implements a memory store using vector embeddings for semantic search.
Memory entries are stored with their vector embeddings for efficient similarity search.
"""

import json
from collections.abc import AsyncIterator
from pathlib import Path
from typing import Any

import numpy as np
from sentence_transformers import SentenceTransformer

from pepperpy.memory.base import (
    BaseMemoryStore,
    MemoryEntry,
    MemoryQuery,
    MemorySearchResult,
)
from pepperpy.memory.config import VectorStoreConfig
from pepperpy.monitoring.logger import get_logger

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
        """
        super().__init__("vector")
        self.config = config
        self.model = SentenceTransformer(config.model_name)
        self.embeddings: np.ndarray | None = None
        self.keys: list[str] = []
        self.storage_path = Path(config.storage_path or "data/vector_store")
        self.storage_path.mkdir(parents=True, exist_ok=True)

    async def _initialize(self) -> None:
        """Initialize the vector store."""
        # Load existing embeddings if any
        if (self.storage_path / "embeddings.npy").exists():
            self.embeddings = np.load(str(self.storage_path / "embeddings.npy"))
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
            embedding = self.model.encode(
                content_str,
                convert_to_numpy=True,
                normalize_embeddings=True,
            )

            if self.embeddings is None:
                self.embeddings = embedding.reshape(1, -1)
                self.keys = [entry.key]
            else:
                if entry.key in self.keys:
                    idx = self.keys.index(entry.key)
                    self.embeddings[idx] = embedding
                else:
                    self.embeddings = np.vstack([self.embeddings, embedding])
                    self.keys.append(entry.key)

            # Save embeddings
            np.save(str(self.storage_path / "embeddings.npy"), self.embeddings)
            with open(self.storage_path / "keys.json", "w") as f:
                json.dump(self.keys, f)

        except Exception as e:
            logger.error(
                "Failed to store in vector store",
                extra={"key": entry.key, "error": str(e)},
            )
            raise MemoryError(f"Failed to store in vector store: {e}") from e

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
                # Load embeddings if needed
                if (
                    self.embeddings is None
                    and (self.storage_path / "embeddings.npy").exists()
                ):
                    self.embeddings = np.load(str(self.storage_path / "embeddings.npy"))
                    with open(self.storage_path / "keys.json") as f:
                        self.keys = json.load(f)

                if not self.embeddings is not None:
                    return

                # Get query embedding
                query_embedding = self.model.encode(
                    query.query,
                    convert_to_numpy=True,
                    normalize_embeddings=True,
                )

                # Calculate similarities
                similarities = np.dot(self.embeddings, query_embedding)
                matching_keys = [
                    (key, float(similarity))
                    for key, similarity in zip(self.keys, similarities, strict=False)
                    if similarity >= query.min_score
                ]

                # Sort by similarity
                matching_keys.sort(key=lambda x: x[1], reverse=True)

                # Process entries
                count = 0
                for key, similarity in matching_keys:
                    if query.limit and count >= query.limit:
                        break

                    # Load entry
                    entry_path = self.storage_path / f"{key}.json"
                    if not entry_path.exists():
                        continue

                    with open(entry_path) as f:
                        entry_data = json.load(f)
                        entry = MemoryEntry[dict[str, Any]].model_validate(entry_data)

                    # Apply filters
                    if "type" in query.filters and entry.type != query.filters["type"]:
                        continue
                    if (
                        "scope" in query.filters
                        and entry.scope != query.filters["scope"]
                    ):
                        continue
                    if query.metadata:
                        if not entry.metadata:
                            continue
                        if not all(
                            entry.metadata.get(k) == v
                            for k, v in query.metadata.items()
                        ):
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
            key: Entry key

        Raises:
            MemoryError: If deletion fails
        """
        try:
            entry_path = self.storage_path / f"{key}.json"
            if not entry_path.exists():
                return

            # Remove entry file
            entry_path.unlink()

            # Update embeddings
            if key in self.keys and self.embeddings is not None:
                idx = self.keys.index(key)
                self.keys.pop(idx)
                self.embeddings = np.delete(self.embeddings, idx, axis=0)

                # Save updated embeddings
                if len(self.keys) > 0:
                    np.save(str(self.storage_path / "embeddings.npy"), self.embeddings)
                    with open(self.storage_path / "keys.json", "w") as f:
                        json.dump(self.keys, f)
                else:
                    # Remove embedding files if no entries left
                    (self.storage_path / "embeddings.npy").unlink(missing_ok=True)
                    (self.storage_path / "keys.json").unlink(missing_ok=True)
                    self.embeddings = None

        except Exception as e:
            logger.error(
                "Failed to delete from vector store",
                extra={"key": key, "error": str(e)},
            )
            raise MemoryError(f"Failed to delete from vector store: {e}") from e
