"""Retriever implementations for the RAG system."""

from typing import Dict, List, Optional

import numpy as np

from .base import Embedder, Indexer, Retriever
from .config import RetrievalConfig
from .types import SearchQuery, SearchResult


class StandardRetriever(Retriever):
    """Standard retriever using embeddings and vector search."""

    def __init__(self, config: RetrievalConfig, embedder: Embedder, indexer: Indexer):
        super().__init__(name="standard_retriever", version="0.1.0")
        self.config = config
        self.embedder = embedder
        self.indexer = indexer

    async def retrieve(self, query: SearchQuery) -> List[SearchResult]:
        """Retrieve relevant chunks using vector similarity."""
        # Generate query embedding
        query_embedding = await self.embedder.embed_query(query.text)

        # Search index
        results = await self.indexer.search(query_embedding, query)
        return results


class HybridRetriever(Retriever):
    """Hybrid retriever combining multiple retrieval methods."""

    def __init__(
        self,
        config: RetrievalConfig,
        retrievers: List[Retriever],
        weights: Optional[List[float]] = None,
    ):
        super().__init__(name="hybrid_retriever", version="0.1.0")
        self.config = config
        self.retrievers = retrievers
        if weights is None:
            weights = [1.0 / len(retrievers)] * len(retrievers)
        self.weights = np.array(weights) / sum(weights)  # Normalize weights

    async def retrieve(self, query: SearchQuery) -> List[SearchResult]:
        """Combine results from multiple retrievers."""
        all_results = []
        for retriever, weight in zip(self.retrievers, self.weights):
            results = await retriever.retrieve(query)
            # Apply weight to scores
            for result in results:
                result.score *= weight
            all_results.extend(results)

        # Merge results by chunk ID
        merged: Dict[str, SearchResult] = {}
        for result in all_results:
            chunk_id = result.chunk.id
            if chunk_id not in merged:
                merged[chunk_id] = result
            else:
                # Sum weighted scores
                merged[chunk_id].score += result.score

        # Sort by score and return top k
        sorted_results = sorted(merged.values(), key=lambda x: x.score, reverse=True)
        return sorted_results[: query.top_k]


class ReRankingRetriever(Retriever):
    """Retriever with re-ranking of initial results."""

    def __init__(
        self,
        config: RetrievalConfig,
        base_retriever: Retriever,
        reranker: Embedder,
    ):
        super().__init__(name="reranking_retriever", version="0.1.0")
        self.config = config
        self.base_retriever = base_retriever
        self.reranker = reranker

    async def retrieve(self, query: SearchQuery) -> List[SearchResult]:
        """Retrieve and re-rank results."""
        # Get initial results
        initial_results = await self.base_retriever.retrieve(query)
        if not initial_results or not self.config.rerank_top_k:
            return initial_results

        # Prepare texts for re-ranking
        query_embedding = await self.reranker.embed_query(query.text)
        chunks = [
            result.chunk for result in initial_results[: self.config.rerank_top_k]
        ]
        chunk_embeddings = await self.reranker.embed_chunks(chunks)

        # Calculate new scores
        for result, embedding in zip(
            initial_results[: self.config.rerank_top_k], chunk_embeddings
        ):
            # Use cosine similarity for re-ranking
            similarity = np.dot(query_embedding, embedding.vector) / (
                np.linalg.norm(query_embedding) * np.linalg.norm(embedding.vector)
            )
            result.score = float(similarity)
            result.metadata["reranked"] = True

        # Sort by new scores
        reranked = sorted(
            initial_results[: self.config.rerank_top_k],
            key=lambda x: x.score,
            reverse=True,
        )
        remaining = initial_results[self.config.rerank_top_k :]

        # Combine reranked and remaining results
        return reranked + remaining
