"""Implementations of different embedding strategies."""

import asyncio
from typing import Dict, List, Optional

import numpy as np
from sentence_transformers import SentenceTransformer

from .base import Embedder
from .config import EmbeddingConfig
from .types import Chunk, Embedding


class TransformerEmbedder(Embedder):
    """Embedder using Sentence Transformers."""

    def __init__(self, config: EmbeddingConfig):
        super().__init__(name="transformer_embedder")
        self.config = config
        self._model = None
        self._lock = asyncio.Lock()

    @property
    def model(self) -> SentenceTransformer:
        """Get or initialize the embedding model."""
        if self._model is None:
            self._model = SentenceTransformer(
                self.config.model_name,
                cache_folder=self.config.cache_dir,
                device=self.config.embedding_device,
            )
        return self._model

    async def embed_chunks(self, chunks: List[Chunk]) -> List[Embedding]:
        """Generate embeddings for chunks."""
        async with self._lock:
            # Batch chunks for efficient processing
            embeddings = []
            for i in range(0, len(chunks), self.config.batch_size):
                batch = chunks[i : i + self.config.batch_size]
                texts = [chunk.content for chunk in batch]

                # Generate embeddings
                vectors = self.model.encode(
                    texts,
                    normalize_embeddings=self.config.normalize_embeddings,
                    show_progress_bar=False,
                )

                # Create Embedding objects
                for chunk, vector in zip(batch, vectors):
                    embeddings.append(
                        Embedding(
                            id=f"emb_{chunk.id}",
                            vector=vector.tolist(),
                            chunk_id=chunk.id,
                            model=self.config.model_name,
                            metadata={
                                "chunk_type": chunk.type.value,
                                "model_name": self.config.model_name,
                                **chunk.metadata,
                            },
                        )
                    )

            return embeddings

    async def embed_query(self, query: str) -> List[float]:
        """Generate embedding for search query."""
        async with self._lock:
            vector = self.model.encode(
                query,
                normalize_embeddings=self.config.normalize_embeddings,
                show_progress_bar=False,
            )
            return vector.tolist()


class CachedEmbedder(Embedder):
    """Embedder with caching support."""

    def __init__(self, config: EmbeddingConfig, base_embedder: Embedder):
        super().__init__(name="cached_embedder")
        self.config = config
        self.base_embedder = base_embedder
        self._cache: Dict[str, List[float]] = {}

    async def embed_chunks(self, chunks: List[Chunk]) -> List[Embedding]:
        """Generate embeddings for chunks with caching."""
        embeddings = []
        uncached_chunks = []

        # Check cache first
        for chunk in chunks:
            cache_key = f"{chunk.id}_{chunk.content}"
            if cache_key in self._cache:
                embeddings.append(
                    Embedding(
                        id=f"emb_{chunk.id}",
                        vector=self._cache[cache_key],
                        chunk_id=chunk.id,
                        model=self.config.model_name,
                        metadata={
                            "chunk_type": chunk.type.value,
                            "model_name": self.config.model_name,
                            "cached": True,
                            **chunk.metadata,
                        },
                    )
                )
            else:
                uncached_chunks.append((cache_key, chunk))

        # Generate embeddings for uncached chunks
        if uncached_chunks:
            new_embeddings = await self.base_embedder.embed_chunks([
                chunk for _, chunk in uncached_chunks
            ])

            # Update cache and add to results
            for (cache_key, _), embedding in zip(uncached_chunks, new_embeddings):
                self._cache[cache_key] = embedding.vector
                embeddings.append(embedding)

        return embeddings

    async def embed_query(self, query: str) -> List[float]:
        """Generate embedding for search query with caching."""
        cache_key = f"query_{query}"
        if cache_key in self._cache:
            return self._cache[cache_key]

        vector = await self.base_embedder.embed_query(query)
        self._cache[cache_key] = vector
        return vector


class BatchedEmbedder(Embedder):
    """Embedder with request batching support."""

    def __init__(self, config: EmbeddingConfig, base_embedder: Embedder):
        super().__init__(name="batched_embedder")
        self.config = config
        self.base_embedder = base_embedder
        self._batch: List[Chunk] = []
        self._lock = asyncio.Lock()

    async def embed_chunks(self, chunks: List[Chunk]) -> List[Embedding]:
        """Generate embeddings for chunks with batching."""
        async with self._lock:
            return await self.base_embedder.embed_chunks(chunks)

    async def embed_query(self, query: str) -> List[float]:
        """Generate embedding for search query."""
        return await self.base_embedder.embed_query(query)

    async def _process_batch(self) -> List[Embedding]:
        """Process accumulated batch of chunks."""
        if not self._batch:
            return []

        batch = self._batch
        self._batch = []
        return await self.base_embedder.embed_chunks(batch)


class HybridEmbedder(Embedder):
    """Embedder combining multiple embedding strategies."""

    def __init__(
        self,
        config: EmbeddingConfig,
        embedders: List[Embedder],
        weights: Optional[List[float]] = None,
    ):
        super().__init__(name="hybrid_embedder")
        self.config = config
        self.embedders = embedders
        self.weights = weights or [1.0] * len(embedders)
        if len(self.weights) != len(embedders):
            raise ValueError("Number of weights must match number of embedders")

    async def embed_chunks(self, chunks: List[Chunk]) -> List[Embedding]:
        """Generate embeddings using multiple strategies."""
        # Get embeddings from all embedders
        all_embeddings = await asyncio.gather(*[
            embedder.embed_chunks(chunks) for embedder in self.embedders
        ])

        # Combine embeddings
        combined_embeddings = []
        for chunk_idx in range(len(chunks)):
            chunk = chunks[chunk_idx]
            vectors = [
                np.array(embeddings[chunk_idx].vector) for embeddings in all_embeddings
            ]

            # Weighted average of embeddings
            combined_vector = np.average(vectors, axis=0, weights=self.weights)

            if self.config.normalize_embeddings:
                combined_vector = combined_vector / np.linalg.norm(combined_vector)

            combined_embeddings.append(
                Embedding(
                    id=f"emb_{chunk.id}",
                    vector=combined_vector.tolist(),
                    chunk_id=chunk.id,
                    model="hybrid",
                    metadata={
                        "chunk_type": chunk.type.value,
                        "embedders": [e.name for e in self.embedders],
                        "weights": self.weights,
                        **chunk.metadata,
                    },
                )
            )

        return combined_embeddings

    async def embed_query(self, query: str) -> List[float]:
        """Generate query embedding using multiple strategies."""
        # Get embeddings from all embedders
        vectors = await asyncio.gather(*[
            embedder.embed_query(query) for embedder in self.embedders
        ])

        # Combine embeddings
        combined_vector = np.average(
            [np.array(v) for v in vectors],
            axis=0,
            weights=self.weights,
        )

        if self.config.normalize_embeddings:
            combined_vector = combined_vector / np.linalg.norm(combined_vector)

        return combined_vector.tolist()
