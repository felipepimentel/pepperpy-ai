"""Indexer implementations for the RAG system."""

import os
from typing import Dict, List

import faiss
import numpy as np
from annoy import AnnoyIndex

from .base import Indexer
from .config import IndexConfig
from .types import Embedding, SearchQuery, SearchResult


class FaissIndexer(Indexer):
    """FAISS-based vector indexer with GPU support."""

    def __init__(self, config: IndexConfig):
        super().__init__(name="faiss_indexer", version="0.1.0")
        self.config = config
        self._index = None
        self._embeddings: Dict[int, Embedding] = {}
        self._init_index()

    async def index_embeddings(self, embeddings: List[Embedding]):
        """Index a batch of embeddings."""
        if not embeddings:
            return

        # Convert embeddings to numpy array
        vectors = np.array([e.vector for e in embeddings], dtype=np.float32)
        ids = list(
            range(len(self._embeddings), len(self._embeddings) + len(embeddings))
        )

        # Add to index
        self._index.add(vectors)

        # Store mapping of ids to embeddings
        for idx, embedding in zip(ids, embeddings):
            self._embeddings[idx] = embedding

    async def search(
        self, query_embedding: List[float], query: SearchQuery
    ) -> List[SearchResult]:
        """Search for similar vectors."""
        if not self._index or not self._embeddings:
            return []

        # Convert query to numpy array
        query_vector = np.array([query_embedding], dtype=np.float32)

        # Search index
        distances, indices = self._index.search(query_vector, query.top_k)

        # Convert results
        results = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx == -1 or dist > 1.0 - query.threshold:
                continue

            embedding = self._embeddings[int(idx)]
            results.append(
                SearchResult(
                    chunk=embedding.chunk,
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
        """Save index to disk."""
        if not self._index or not self._embeddings:
            return

        os.makedirs(os.path.dirname(path), exist_ok=True)

        # Save FAISS index
        faiss.write_index(self._index, f"{path}.faiss")

        # Save embeddings mapping
        np.save(f"{path}.npy", self._embeddings)

    async def load(self, path: str):
        """Load index from disk."""
        if not os.path.exists(f"{path}.faiss"):
            raise FileNotFoundError(f"No index found at {path}.faiss")

        # Load FAISS index
        self._index = faiss.read_index(f"{path}.faiss")

        # Load embeddings mapping
        self._embeddings = np.load(f"{path}.npy", allow_pickle=True).item()

    def _init_index(self):
        """Initialize FAISS index."""
        # Create index based on config
        if self.config.metric == "cosine":
            self._index = faiss.IndexFlatIP(
                len(next(iter(self._embeddings.values())).vector)
                if self._embeddings
                else 768
            )
        else:  # L2 distance
            self._index = faiss.IndexFlatL2(
                len(next(iter(self._embeddings.values())).vector)
                if self._embeddings
                else 768
            )

        # Enable GPU if configured
        if self.config.use_gpu:
            res = faiss.StandardGpuResources()
            self._index = faiss.index_cpu_to_gpu(res, 0, self._index)


class AnnoyIndexer(Indexer):
    """Annoy-based vector indexer."""

    def __init__(self, config: IndexConfig):
        super().__init__(name="annoy_indexer", version="0.1.0")
        self.config = config
        self._index = None
        self._embeddings: Dict[int, Embedding] = {}
        self._next_id = 0
        self._init_index()

    async def index_embeddings(self, embeddings: List[Embedding]):
        """Index a batch of embeddings."""
        if not embeddings:
            return

        # Add vectors to index
        for embedding in embeddings:
            self._index.add_item(self._next_id, embedding.vector)
            self._embeddings[self._next_id] = embedding
            self._next_id += 1

        # Build index after adding all vectors
        self._index.build(self.config.nprobe)

    async def search(
        self, query_embedding: List[float], query: SearchQuery
    ) -> List[SearchResult]:
        """Search for similar vectors."""
        if not self._index or not self._embeddings:
            return []

        # Search index
        indices, distances = self._index.get_nns_by_vector(
            query_embedding, query.top_k, include_distances=True
        )

        # Convert results
        results = []
        for idx, dist in zip(indices, distances):
            if dist > 1.0 - query.threshold:
                continue

            embedding = self._embeddings[idx]
            results.append(
                SearchResult(
                    chunk=embedding.chunk,
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
        """Save index to disk."""
        if not self._index or not self._embeddings:
            return

        os.makedirs(os.path.dirname(path), exist_ok=True)

        # Save Annoy index
        self._index.save(f"{path}.ann")

        # Save embeddings mapping
        np.save(f"{path}.npy", self._embeddings)

    async def load(self, path: str):
        """Load index from disk."""
        if not os.path.exists(f"{path}.ann"):
            raise FileNotFoundError(f"No index found at {path}.ann")

        # Load embeddings mapping
        self._embeddings = np.load(f"{path}.npy", allow_pickle=True).item()

        # Initialize and load Annoy index
        self._init_index()
        self._index.load(f"{path}.ann")

        # Update next id
        self._next_id = max(self._embeddings.keys()) + 1 if self._embeddings else 0

    def _init_index(self):
        """Initialize Annoy index."""
        vector_dim = (
            len(next(iter(self._embeddings.values())).vector)
            if self._embeddings
            else 768
        )
        metric = "angular" if self.config.metric == "cosine" else "euclidean"
        self._index = AnnoyIndex(vector_dim, metric)


class HybridIndexer(Indexer):
    """Hybrid indexer that combines multiple indexers."""

    def __init__(self, config: IndexConfig, indexers: List[Indexer]):
        super().__init__(name="hybrid_indexer", version="0.1.0")
        self.config = config
        self.indexers = indexers

    async def index_embeddings(self, embeddings: List[Embedding]):
        """Index embeddings in all sub-indexers."""
        for indexer in self.indexers:
            await indexer.index_embeddings(embeddings)

    async def search(
        self, query_embedding: List[float], query: SearchQuery
    ) -> List[SearchResult]:
        """Search across all sub-indexers and merge results."""
        all_results = []
        for indexer in self.indexers:
            results = await indexer.search(query_embedding, query)
            all_results.append(results)

        # Merge results by averaging scores for same chunks
        merged: Dict[str, SearchResult] = {}
        for results in all_results:
            for result in results:
                chunk_id = result.chunk.id
                if chunk_id not in merged:
                    merged[chunk_id] = result
                else:
                    # Average scores
                    merged[chunk_id].score = (merged[chunk_id].score + result.score) / 2

        # Sort by score and return top k
        sorted_results = sorted(merged.values(), key=lambda x: x.score, reverse=True)
        return sorted_results[: query.top_k]

    async def save(self, path: str):
        """Save all sub-indexers."""
        for i, indexer in enumerate(self.indexers):
            await indexer.save(f"{path}_sub{i}")

    async def load(self, path: str):
        """Load all sub-indexers."""
        for i, indexer in enumerate(self.indexers):
            await indexer.load(f"{path}_sub{i}")
