"""Implementations of different indexing strategies."""

import asyncio
import os
from typing import Dict, List

import faiss
import numpy as np
from annoy import AnnoyIndex

from .base import Indexer
from .config import IndexConfig
from .types import Embedding, SearchQuery, SearchResult


class FaissIndexer(Indexer):
    """Vector indexing using FAISS."""

    def __init__(self, config: IndexConfig):
        super().__init__(name="faiss_indexer")
        self.config = config
        self._index = None
        self._embeddings: Dict[int, Embedding] = {}
        self._next_id = 0
        self._dimension = None
        self._lock = asyncio.Lock()

    async def index_embeddings(self, embeddings: List[Embedding]):
        """Add embeddings to the index."""
        if not embeddings:
            return

        async with self._lock:
            # Initialize index if needed
            if self._index is None:
                self._dimension = len(embeddings[0].vector)
                self._init_index()

            # Convert embeddings to numpy array
            vectors = np.array([emb.vector for emb in embeddings], dtype=np.float32)
            ids = list(range(self._next_id, self._next_id + len(embeddings)))

            # Add to index
            self._index.add_with_ids(vectors, np.array(ids))

            # Store mapping of ids to embeddings
            for idx, embedding in zip(ids, embeddings):
                self._embeddings[idx] = embedding

            self._next_id += len(embeddings)

    async def search(
        self, query_embedding: List[float], query: SearchQuery
    ) -> List[SearchResult]:
        """Search for similar vectors."""
        if self._index is None:
            return []

        async with self._lock:
            # Convert query to numpy array
            vector = np.array([query_embedding], dtype=np.float32)

            # Search index
            distances, indices = self._index.search(vector, query.top_k)

            # Convert results
            results = []
            for dist, idx in zip(distances[0], indices[0]):
                if idx == -1 or dist < query.threshold:
                    continue

                embedding = self._embeddings[int(idx)]
                results.append(
                    SearchResult(
                        chunk_id=embedding.chunk_id,
                        score=float(1.0 - dist),  # Convert distance to similarity score
                        metadata={
                            "model": embedding.model,
                            "distance": float(dist),
                            **embedding.metadata,
                        },
                    )
                )

            return results

    async def save(self, path: str):
        """Save the index to disk."""
        if self._index is None:
            return

        async with self._lock:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(path), exist_ok=True)

            # Save FAISS index
            faiss.write_index(self._index, f"{path}.faiss")

            # Save embeddings mapping
            np.save(f"{path}.embeddings.npy", self._embeddings)

    async def load(self, path: str):
        """Load the index from disk."""
        async with self._lock:
            # Load FAISS index
            self._index = faiss.read_index(f"{path}.faiss")

            # Load embeddings mapping
            self._embeddings = np.load(
                f"{path}.embeddings.npy", allow_pickle=True
            ).item()

            # Update next id
            self._next_id = max(self._embeddings.keys()) + 1 if self._embeddings else 0

    def _init_index(self):
        """Initialize the FAISS index."""
        if self.config.use_gpu and faiss.get_num_gpus() > 0:
            # Create GPU index
            res = faiss.StandardGpuResources()
            config = faiss.GpuIndexFlatConfig()
            config.device = 0

            if self.config.metric == "cosine":
                index = faiss.GpuIndexFlatIP(res, self._dimension, config)
            else:  # L2
                index = faiss.GpuIndexFlatL2(res, self._dimension, config)
        else:
            # Create CPU index
            if self.config.metric == "cosine":
                index = faiss.IndexFlatIP(self._dimension)
            else:  # L2
                index = faiss.IndexFlatL2(self._dimension)

        self._index = index


class AnnoyIndexer(Indexer):
    """Vector indexing using Annoy."""

    def __init__(self, config: IndexConfig):
        super().__init__(name="annoy_indexer")
        self.config = config
        self._index = None
        self._embeddings: Dict[int, Embedding] = {}
        self._next_id = 0
        self._dimension = None
        self._lock = asyncio.Lock()
        self._dirty = False

    async def index_embeddings(self, embeddings: List[Embedding]):
        """Add embeddings to the index."""
        if not embeddings:
            return

        async with self._lock:
            # Initialize index if needed
            if self._index is None:
                self._dimension = len(embeddings[0].vector)
                self._init_index()

            # Add vectors to index
            for embedding in embeddings:
                self._index.add_item(self._next_id, embedding.vector)
                self._embeddings[self._next_id] = embedding
                self._next_id += 1

            self._dirty = True

    async def search(
        self, query_embedding: List[float], query: SearchQuery
    ) -> List[SearchResult]:
        """Search for similar vectors."""
        if self._index is None:
            return []

        async with self._lock:
            # Build index if needed
            if self._dirty:
                self._index.build(self.config.n_trees)
                self._dirty = False

            # Search index
            indices, distances = self._index.get_nns_by_vector(
                query_embedding,
                query.top_k,
                include_distances=True,
            )

            # Convert results
            results = []
            for idx, dist in zip(indices, distances):
                if dist < query.threshold:
                    continue

                embedding = self._embeddings[idx]
                results.append(
                    SearchResult(
                        chunk_id=embedding.chunk_id,
                        score=float(1.0 - dist),  # Convert distance to similarity score
                        metadata={
                            "model": embedding.model,
                            "distance": float(dist),
                            **embedding.metadata,
                        },
                    )
                )

            return results

    async def save(self, path: str):
        """Save the index to disk."""
        if self._index is None:
            return

        async with self._lock:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(path), exist_ok=True)

            # Build index if needed
            if self._dirty:
                self._index.build(self.config.n_trees)
                self._dirty = False

            # Save Annoy index
            self._index.save(f"{path}.ann")

            # Save embeddings mapping
            np.save(f"{path}.embeddings.npy", self._embeddings)

    async def load(self, path: str):
        """Load the index from disk."""
        async with self._lock:
            # Load embeddings mapping first to get dimension
            self._embeddings = np.load(
                f"{path}.embeddings.npy", allow_pickle=True
            ).item()
            self._dimension = len(next(iter(self._embeddings.values())).vector)

            # Initialize and load Annoy index
            self._init_index()
            self._index.load(f"{path}.ann")

            # Update next id
            self._next_id = max(self._embeddings.keys()) + 1 if self._embeddings else 0

    def _init_index(self):
        """Initialize the Annoy index."""
        metric = "angular" if self.config.metric == "cosine" else "euclidean"
        self._index = AnnoyIndex(self._dimension, metric)


class HybridIndexer(Indexer):
    """Combines multiple indexing strategies."""

    def __init__(self, config: IndexConfig, indexers: List[Indexer]):
        super().__init__(name="hybrid_indexer")
        self.config = config
        self.indexers = indexers

    async def index_embeddings(self, embeddings: List[Embedding]):
        """Add embeddings to all indexes."""
        await asyncio.gather(*[
            indexer.index_embeddings(embeddings) for indexer in self.indexers
        ])

    async def search(
        self, query_embedding: List[float], query: SearchQuery
    ) -> List[SearchResult]:
        """Search using all indexes and merge results."""
        # Get results from all indexers
        all_results = await asyncio.gather(*[
            indexer.search(query_embedding, query) for indexer in self.indexers
        ])

        # Merge results
        merged = {}
        for results in all_results:
            for result in results:
                if result.chunk_id not in merged:
                    merged[result.chunk_id] = result
                else:
                    # Average scores
                    merged[result.chunk_id].score = (
                        merged[result.chunk_id].score + result.score
                    ) / 2

        # Sort by score and return top k
        results = sorted(merged.values(), key=lambda x: x.score, reverse=True)[
            : query.top_k
        ]

        return results

    async def save(self, path: str):
        """Save all indexes."""
        await asyncio.gather(*[
            indexer.save(f"{path}.{i}") for i, indexer in enumerate(self.indexers)
        ])

    async def load(self, path: str):
        """Load all indexes."""
        await asyncio.gather(*[
            indexer.load(f"{path}.{i}") for i, indexer in enumerate(self.indexers)
        ])
