"""
Hybrid search capabilities for the RAG module.

This module provides components for combining keyword-based and semantic search approaches
to improve retrieval quality and coverage. It includes:

1. Keyword search: Traditional text search using BM25, TF-IDF, or other algorithms
2. Semantic search: Vector-based search using embeddings
3. Hybrid search: Combining keyword and semantic search results
4. Result fusion: Methods for merging and ranking results from different search approaches
"""

import math
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Protocol

from pepperpy.types.common import Document


class SearchType(Enum):
    """Types of search approaches that can be used in hybrid search."""

    KEYWORD = auto()  # Traditional keyword-based search (BM25, TF-IDF, etc.)
    SEMANTIC = auto()  # Vector-based semantic search using embeddings
    HYBRID = auto()  # Combination of keyword and semantic search


class SearchResult:
    """Represents a single search result with score and metadata."""

    def __init__(
        self,
        document: Document,
        score: float,
        search_type: SearchType,
        rank: Optional[int] = None,
        highlights: Optional[List[str]] = None,
    ):
        """
        Initialize a search result.

        Args:
            document: The retrieved document
            score: The relevance score (higher is better)
            search_type: The type of search that produced this result
            rank: The rank of this result in its original result set (optional)
            highlights: Highlighted text snippets from the document (optional)
        """
        self.document = document
        self.score = score
        self.search_type = search_type
        self.rank = rank
        self.highlights = highlights or []
        self.normalized_score: Optional[float] = None
        self.combined_score: Optional[float] = None

    def __repr__(self) -> str:
        """Return a string representation of the search result."""
        return (
            f"SearchResult(id={self.document.id}, "
            f"score={self.score:.4f}, "
            f"type={self.search_type.name})"
        )


class SearchResults:
    """Collection of search results with metadata."""

    def __init__(
        self,
        results: List[SearchResult],
        search_type: SearchType,
        query: str,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize a collection of search results.

        Args:
            results: List of search results
            search_type: The type of search that produced these results
            query: The original query
            metadata: Additional metadata about the search (optional)
        """
        self.results = results
        self.search_type = search_type
        self.query = query
        self.metadata = metadata or {}

    def __len__(self) -> int:
        """Return the number of results."""
        return len(self.results)

    def __getitem__(self, index: int) -> SearchResult:
        """Get a result by index."""
        return self.results[index]

    def __iter__(self):
        """Iterate over results."""
        return iter(self.results)

    def sort_by_score(self, descending: bool = True) -> "SearchResults":
        """
        Sort results by score.

        Args:
            descending: Whether to sort in descending order (default: True)

        Returns:
            Self, for method chaining
        """
        self.results.sort(key=lambda r: r.score, reverse=descending)
        # Update ranks after sorting
        for i, result in enumerate(self.results):
            result.rank = i + 1
        return self

    def top_k(self, k: int) -> "SearchResults":
        """
        Get the top k results.

        Args:
            k: Number of results to return

        Returns:
            A new SearchResults object with only the top k results
        """
        return SearchResults(
            results=self.results[:k],
            search_type=self.search_type,
            query=self.query,
            metadata=self.metadata.copy(),
        )


class SearchProvider(Protocol):
    """Protocol for search providers."""

    def search(self, query: str, **kwargs) -> SearchResults:
        """
        Search for documents matching the query.

        Args:
            query: The search query
            **kwargs: Additional search parameters

        Returns:
            Search results
        """
        ...


@dataclass
class KeywordSearchConfig:
    """Configuration for keyword search."""

    algorithm: str = "BM25"  # BM25, TF-IDF, etc.
    min_score: float = 0.0
    max_results: int = 100
    highlight: bool = True
    highlight_tag: str = "<mark>"
    fields: Optional[List[str]] = None
    boost_fields: Optional[Dict[str, float]] = None
    additional_params: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SemanticSearchConfig:
    """Configuration for semantic search."""

    model_name: str = "default"
    min_score: float = 0.0
    max_results: int = 100
    normalize_scores: bool = True
    fields: Optional[List[str]] = None
    additional_params: Dict[str, Any] = field(default_factory=dict)


@dataclass
class HybridSearchConfig:
    """Configuration for hybrid search."""

    keyword_weight: float = 0.5
    semantic_weight: float = 0.5
    fusion_method: str = (
        "linear_combination"  # linear_combination, reciprocal_rank_fusion, etc.
    )
    max_results: int = 100
    min_keyword_score: float = 0.0
    min_semantic_score: float = 0.0
    deduplicate: bool = True
    rerank: bool = False
    reranker_model: Optional[str] = None
    additional_params: Dict[str, Any] = field(default_factory=dict)


class KeywordSearch:
    """Keyword-based search implementation."""

    def __init__(self, config: Optional[KeywordSearchConfig] = None):
        """
        Initialize keyword search.

        Args:
            config: Search configuration (optional)
        """
        self.config = config or KeywordSearchConfig()

    def search(self, query: str, documents: List[Document], **kwargs) -> SearchResults:
        """
        Search for documents matching the query using keyword search.

        Args:
            query: The search query
            documents: The documents to search
            **kwargs: Additional search parameters

        Returns:
            Search results
        """
        # In a real implementation, this would use a proper keyword search algorithm
        # like BM25 or TF-IDF. This is a simplified example.
        results = []

        for i, doc in enumerate(documents):
            # Simple keyword matching (in a real implementation, use proper algorithms)
            content = doc.content.lower()
            query_terms = query.lower().split()

            # Count term occurrences
            term_counts = {}
            for term in query_terms:
                term_counts[term] = content.count(term)

            # Calculate a simple score based on term frequency
            score = sum(term_counts.values()) / (len(content.split()) + 1)

            # Only include results above the minimum score
            if score > self.config.min_score:
                # Create highlights (in a real implementation, use proper highlighting)
                highlights = []
                if self.config.highlight:
                    words = content.split()
                    for term in query_terms:
                        for i in range(len(words)):
                            if term in words[i].lower():
                                start = max(0, i - 3)
                                end = min(len(words), i + 4)
                                context = " ".join(words[start:end])
                                highlight = context.replace(
                                    words[i],
                                    f"{self.config.highlight_tag}{words[i]}</mark>",
                                )
                                highlights.append(highlight)
                                break

                result = SearchResult(
                    document=doc,
                    score=score,
                    search_type=SearchType.KEYWORD,
                    highlights=highlights,
                )
                results.append(result)

        # Sort results by score
        results.sort(key=lambda r: r.score, reverse=True)

        # Limit to max results
        results = results[: self.config.max_results]

        # Assign ranks
        for i, result in enumerate(results):
            result.rank = i + 1

        return SearchResults(
            results=results,
            search_type=SearchType.KEYWORD,
            query=query,
            metadata={"algorithm": self.config.algorithm},
        )


class SemanticSearch:
    """Semantic search implementation using embeddings."""

    def __init__(self, config: Optional[SemanticSearchConfig] = None):
        """
        Initialize semantic search.

        Args:
            config: Search configuration (optional)
        """
        self.config = config or SemanticSearchConfig()

    def search(self, query: str, documents: List[Document], **kwargs) -> SearchResults:
        """
        Search for documents matching the query using semantic search.

        Args:
            query: The search query
            documents: The documents to search
            **kwargs: Additional search parameters

        Returns:
            Search results
        """
        # In a real implementation, this would use embeddings and vector search
        # This is a simplified example that simulates semantic search
        results = []

        # Simulate query embedding (in a real implementation, use a proper embedding model)
        query_embedding = self._simulate_embedding(query)

        for doc in documents:
            # Simulate document embedding
            doc_embedding = self._simulate_embedding(doc.content)

            # Calculate cosine similarity (in a real implementation, use proper vector operations)
            similarity = self._cosine_similarity(query_embedding, doc_embedding)

            # Only include results above the minimum score
            if similarity > self.config.min_score:
                result = SearchResult(
                    document=doc, score=similarity, search_type=SearchType.SEMANTIC
                )
                results.append(result)

        # Sort results by score
        results.sort(key=lambda r: r.score, reverse=True)

        # Limit to max results
        results = results[: self.config.max_results]

        # Assign ranks
        for i, result in enumerate(results):
            result.rank = i + 1

        # Normalize scores if configured
        if self.config.normalize_scores:
            self._normalize_scores(results)

        return SearchResults(
            results=results,
            search_type=SearchType.SEMANTIC,
            query=query,
            metadata={"model": self.config.model_name},
        )

    def _simulate_embedding(self, text: str) -> List[float]:
        """
        Simulate creating an embedding for text.

        In a real implementation, this would use a proper embedding model.

        Args:
            text: The text to embed

        Returns:
            A simulated embedding vector
        """
        # This is a very simplified simulation that creates a pseudo-random vector
        # based on the content of the text. In a real implementation, use a proper
        # embedding model.
        import hashlib

        # Create a deterministic but varied vector based on text content
        vector_size = 128
        vector = [0.0] * vector_size

        # Use hash of text to seed the vector
        hash_obj = hashlib.md5(text.encode())
        hash_bytes = hash_obj.digest()

        # Fill the vector with values derived from the hash
        for i in range(min(len(hash_bytes), vector_size)):
            vector[i] = (hash_bytes[i] / 255.0) * 2.0 - 1.0

        # Add some variation based on word frequencies
        words = text.lower().split()
        word_counts = {}
        for word in words:
            if word not in word_counts:
                word_counts[word] = 0
            word_counts[word] += 1

        for word, count in word_counts.items():
            word_hash = hashlib.md5(word.encode()).digest()
            for i in range(min(len(word_hash), vector_size)):
                idx = (ord(word[0]) + i) % vector_size
                vector[idx] += (word_hash[i] / 255.0) * count / len(words)

        # Normalize the vector
        magnitude = math.sqrt(sum(x * x for x in vector))
        if magnitude > 0:
            vector = [x / magnitude for x in vector]

        return vector

    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """
        Calculate cosine similarity between two vectors.

        Args:
            vec1: First vector
            vec2: Second vector

        Returns:
            Cosine similarity (between -1 and 1, higher is more similar)
        """
        # Ensure vectors are the same length
        min_len = min(len(vec1), len(vec2))
        vec1 = vec1[:min_len]
        vec2 = vec2[:min_len]

        # Calculate dot product
        dot_product = sum(a * b for a, b in zip(vec1, vec2))

        # Calculate magnitudes
        magnitude1 = math.sqrt(sum(x * x for x in vec1))
        magnitude2 = math.sqrt(sum(x * x for x in vec2))

        # Calculate cosine similarity
        if magnitude1 > 0 and magnitude2 > 0:
            return dot_product / (magnitude1 * magnitude2)
        else:
            return 0.0

    def _normalize_scores(self, results: List[SearchResult]) -> None:
        """
        Normalize scores to be between 0 and 1.

        Args:
            results: List of search results to normalize
        """
        if not results:
            return

        # Find min and max scores
        min_score = min(r.score for r in results)
        max_score = max(r.score for r in results)

        # Normalize scores
        if max_score > min_score:
            for result in results:
                result.normalized_score = (result.score - min_score) / (
                    max_score - min_score
                )
        else:
            # If all scores are the same, set normalized score to 1
            for result in results:
                result.normalized_score = 1.0


class HybridSearch:
    """Hybrid search implementation combining keyword and semantic search."""

    def __init__(
        self,
        keyword_search: Optional[KeywordSearch] = None,
        semantic_search: Optional[SemanticSearch] = None,
        config: Optional[HybridSearchConfig] = None,
    ):
        """
        Initialize hybrid search.

        Args:
            keyword_search: Keyword search implementation (optional)
            semantic_search: Semantic search implementation (optional)
            config: Hybrid search configuration (optional)
        """
        self.keyword_search = keyword_search or KeywordSearch()
        self.semantic_search = semantic_search or SemanticSearch()
        self.config = config or HybridSearchConfig()

    def search(self, query: str, documents: List[Document], **kwargs) -> SearchResults:
        """
        Search for documents matching the query using hybrid search.

        Args:
            query: The search query
            documents: The documents to search
            **kwargs: Additional search parameters

        Returns:
            Search results
        """
        # Perform keyword search
        keyword_results = self.keyword_search.search(query, documents, **kwargs)

        # Perform semantic search
        semantic_results = self.semantic_search.search(query, documents, **kwargs)

        # Combine results using the configured fusion method
        if self.config.fusion_method == "linear_combination":
            combined_results = self._linear_combination_fusion(
                keyword_results, semantic_results
            )
        elif self.config.fusion_method == "reciprocal_rank_fusion":
            combined_results = self._reciprocal_rank_fusion(
                keyword_results, semantic_results
            )
        else:
            raise ValueError(f"Unknown fusion method: {self.config.fusion_method}")

        # Deduplicate results if configured
        if self.config.deduplicate:
            combined_results = self._deduplicate_results(combined_results)

        # Rerank results if configured
        if self.config.rerank:
            combined_results = self._rerank_results(combined_results, query)

        # Limit to max results
        combined_results = combined_results[: self.config.max_results]

        # Create final search results
        return SearchResults(
            results=combined_results,
            search_type=SearchType.HYBRID,
            query=query,
            metadata={
                "keyword_results_count": len(keyword_results),
                "semantic_results_count": len(semantic_results),
                "fusion_method": self.config.fusion_method,
                "keyword_weight": self.config.keyword_weight,
                "semantic_weight": self.config.semantic_weight,
            },
        )

    def _linear_combination_fusion(
        self, keyword_results: SearchResults, semantic_results: SearchResults
    ) -> List[SearchResult]:
        """
        Combine results using linear combination of scores.

        Args:
            keyword_results: Results from keyword search
            semantic_results: Results from semantic search

        Returns:
            Combined and sorted list of search results
        """
        # Create a dictionary to store combined results by document ID
        combined_dict: Dict[str, SearchResult] = {}

        # Process keyword results
        for result in keyword_results:
            if result.score < self.config.min_keyword_score:
                continue

            doc_id = result.document.id
            result.normalized_score = (
                result.score
            )  # Keyword scores are already normalized
            combined_dict[doc_id] = result

        # Process semantic results
        for result in semantic_results:
            if result.score < self.config.min_semantic_score:
                continue

            doc_id = result.document.id

            if doc_id in combined_dict:
                # Document exists in both result sets, combine scores
                keyword_result = combined_dict[doc_id]
                keyword_score = keyword_result.normalized_score or keyword_result.score
                semantic_score = result.normalized_score or result.score

                # Calculate combined score
                combined_score = (
                    self.config.keyword_weight * keyword_score
                    + self.config.semantic_weight * semantic_score
                )

                # Update the existing result
                keyword_result.combined_score = combined_score

                # Add semantic highlights if available
                if result.highlights:
                    keyword_result.highlights.extend(result.highlights)
            else:
                # Document only exists in semantic results
                result.combined_score = self.config.semantic_weight * (
                    result.normalized_score or result.score
                )
                combined_dict[doc_id] = result

        # Convert dictionary to list
        combined_results = list(combined_dict.values())

        # Sort by combined score
        combined_results.sort(key=lambda r: r.combined_score or 0.0, reverse=True)

        # Update ranks
        for i, result in enumerate(combined_results):
            result.rank = i + 1

        return combined_results

    def _reciprocal_rank_fusion(
        self, keyword_results: SearchResults, semantic_results: SearchResults
    ) -> List[SearchResult]:
        """
        Combine results using reciprocal rank fusion.

        Args:
            keyword_results: Results from keyword search
            semantic_results: Results from semantic search

        Returns:
            Combined and sorted list of search results
        """
        # Create a dictionary to store combined results by document ID
        combined_dict: Dict[str, SearchResult] = {}

        # Constant for RRF formula
        k = 60  # Standard value from the literature

        # Process keyword results
        for result in keyword_results:
            if result.score < self.config.min_keyword_score:
                continue

            doc_id = result.document.id
            rank = result.rank or 1000  # Use a high rank if not set

            # Calculate RRF score
            rrf_score = 1.0 / (k + rank)

            # Store result with RRF score
            result.combined_score = rrf_score * self.config.keyword_weight
            combined_dict[doc_id] = result

        # Process semantic results
        for result in semantic_results:
            if result.score < self.config.min_semantic_score:
                continue

            doc_id = result.document.id
            rank = result.rank or 1000  # Use a high rank if not set

            # Calculate RRF score
            rrf_score = 1.0 / (k + rank)

            if doc_id in combined_dict:
                # Document exists in both result sets, combine scores
                keyword_result = combined_dict[doc_id]

                # Add semantic RRF score
                keyword_result.combined_score = (
                    keyword_result.combined_score or 0.0
                ) + (rrf_score * self.config.semantic_weight)

                # Add semantic highlights if available
                if result.highlights:
                    keyword_result.highlights.extend(result.highlights)
            else:
                # Document only exists in semantic results
                result.combined_score = rrf_score * self.config.semantic_weight
                combined_dict[doc_id] = result

        # Convert dictionary to list
        combined_results = list(combined_dict.values())

        # Sort by combined score
        combined_results.sort(key=lambda r: r.combined_score or 0.0, reverse=True)

        # Update ranks
        for i, result in enumerate(combined_results):
            result.rank = i + 1

        return combined_results

    def _deduplicate_results(self, results: List[SearchResult]) -> List[SearchResult]:
        """
        Remove duplicate results based on document ID.

        Args:
            results: List of search results

        Returns:
            Deduplicated list of search results
        """
        seen_ids = set()
        deduplicated = []

        for result in results:
            doc_id = result.document.id
            if doc_id not in seen_ids:
                seen_ids.add(doc_id)
                deduplicated.append(result)

        return deduplicated

    def _rerank_results(
        self, results: List[SearchResult], query: str
    ) -> List[SearchResult]:
        """
        Rerank results using a more sophisticated model.

        In a real implementation, this would use a reranking model like a cross-encoder.
        This is a simplified example.

        Args:
            results: List of search results
            query: The original query

        Returns:
            Reranked list of search results
        """
        # In a real implementation, this would use a proper reranking model
        # This is a simplified example that just adjusts scores based on exact matches

        for result in results:
            content = result.document.content.lower()
            query_lower = query.lower()

            # Boost score for exact phrase matches
            if query_lower in content:
                result.combined_score = (result.combined_score or 0.0) * 1.5

        # Sort by adjusted score
        results.sort(key=lambda r: r.combined_score or 0.0, reverse=True)

        # Update ranks
        for i, result in enumerate(results):
            result.rank = i + 1

        return results


def create_hybrid_search(
    keyword_config: Optional[KeywordSearchConfig] = None,
    semantic_config: Optional[SemanticSearchConfig] = None,
    hybrid_config: Optional[HybridSearchConfig] = None,
) -> HybridSearch:
    """
    Create a hybrid search instance with the specified configurations.

    Args:
        keyword_config: Configuration for keyword search (optional)
        semantic_config: Configuration for semantic search (optional)
        hybrid_config: Configuration for hybrid search (optional)

    Returns:
        A configured HybridSearch instance
    """
    keyword_search = KeywordSearch(config=keyword_config)
    semantic_search = SemanticSearch(config=semantic_config)

    return HybridSearch(
        keyword_search=keyword_search,
        semantic_search=semantic_search,
        config=hybrid_config,
    )
