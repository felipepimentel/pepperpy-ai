"""
Reranking strategies for the RAG module.

This module provides components for reranking search results to improve relevance
and quality. It includes:

1. Cross-encoder reranking: Using cross-encoder models to score query-document pairs
2. Feature-based reranking: Using multiple features to score and rerank results
3. Ensemble reranking: Combining multiple reranking strategies
4. Custom reranking: Framework for implementing custom reranking algorithms
"""

import math
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Callable, Dict, List, Optional, Tuple

from pepperpy.types.common import Document


class RerankerType(Enum):
    """Types of rerankers that can be used to rerank search results."""

    CROSS_ENCODER = auto()  # Uses cross-encoder models to score query-document pairs
    FEATURE_BASED = auto()  # Uses multiple features to score and rerank results
    ENSEMBLE = auto()  # Combines multiple reranking strategies
    CUSTOM = auto()  # Custom reranking algorithm


class SearchResult:
    """Represents a single search result with score and metadata."""

    def __init__(
        self,
        document: Document,
        score: float,
        rank: Optional[int] = None,
        highlights: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize a search result.

        Args:
            document: The retrieved document
            score: The relevance score (higher is better)
            rank: The rank of this result in its original result set (optional)
            highlights: Highlighted text snippets from the document (optional)
            metadata: Additional metadata about the result (optional)
        """
        self.document = document
        self.score = score
        self.rank = rank
        self.highlights = highlights or []
        self.metadata = metadata or {}
        self.original_score = score  # Keep track of the original score
        self.reranked_score: Optional[float] = None

    def __repr__(self) -> str:
        """Return a string representation of the search result."""
        return (
            f"SearchResult(id={self.document.id}, "
            f"score={self.score:.4f}, "
            f"rank={self.rank})"
        )


class SearchResults:
    """Collection of search results with metadata."""

    def __init__(
        self,
        results: List[SearchResult],
        query: str,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize a collection of search results.

        Args:
            results: List of search results
            query: The original query
            metadata: Additional metadata about the search (optional)
        """
        self.results = results
        self.query = query
        self.metadata = metadata or {}
        self.reranked = False

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
            results=self.results[:k], query=self.query, metadata=self.metadata.copy()
        )


class Reranker(ABC):
    """Base class for rerankers."""

    @abstractmethod
    def rerank(self, results: SearchResults) -> SearchResults:
        """
        Rerank search results.

        Args:
            results: The search results to rerank

        Returns:
            Reranked search results
        """
        pass

    @property
    @abstractmethod
    def reranker_type(self) -> RerankerType:
        """Get the type of reranker."""
        pass


@dataclass
class CrossEncoderConfig:
    """Configuration for cross-encoder reranking."""

    model_name: str = "default"
    max_length: int = 512
    batch_size: int = 16
    normalize_scores: bool = True
    use_gpu: bool = True
    additional_params: Dict[str, Any] = field(default_factory=dict)


class CrossEncoderReranker(Reranker):
    """Reranker using cross-encoder models to score query-document pairs."""

    def __init__(self, config: Optional[CrossEncoderConfig] = None):
        """
        Initialize cross-encoder reranker.

        Args:
            config: Reranker configuration (optional)
        """
        self.config = config or CrossEncoderConfig()

    def rerank(self, results: SearchResults) -> SearchResults:
        """
        Rerank search results using a cross-encoder model.

        Args:
            results: The search results to rerank

        Returns:
            Reranked search results
        """
        # In a real implementation, this would use a proper cross-encoder model
        # This is a simplified example that simulates cross-encoder scoring

        query = results.query

        for result in results.results:
            # Simulate cross-encoder scoring (in a real implementation, use a proper model)
            reranked_score = self._simulate_cross_encoder_score(
                query, result.document.content
            )

            # Store the original score and update with the reranked score
            result.original_score = result.score
            result.reranked_score = reranked_score
            result.score = reranked_score

        # Sort by the new scores
        results.sort_by_score()

        # Mark as reranked
        results.reranked = True
        results.metadata["reranker"] = "cross_encoder"
        results.metadata["model"] = self.config.model_name

        return results

    def _simulate_cross_encoder_score(self, query: str, document_text: str) -> float:
        """
        Simulate cross-encoder scoring.

        In a real implementation, this would use a proper cross-encoder model.

        Args:
            query: The search query
            document_text: The document text

        Returns:
            A simulated cross-encoder score
        """
        # This is a very simplified simulation that calculates a score based on
        # term overlap, exact phrase matches, and document length

        # Normalize text
        query_lower = query.lower()
        doc_lower = document_text.lower()

        # Calculate term overlap
        query_terms = set(re.findall(r"\w+", query_lower))
        doc_terms = set(re.findall(r"\w+", doc_lower))

        if not query_terms or not doc_terms:
            return 0.0

        # Term overlap score
        overlap_score = len(query_terms.intersection(doc_terms)) / len(query_terms)

        # Exact phrase match bonus
        phrase_bonus = 0.0
        if query_lower in doc_lower:
            phrase_bonus = 0.3

        # Document length penalty (prefer shorter documents)
        length_penalty = 1.0 / (1.0 + math.log(1 + len(doc_terms) / 100.0))

        # Combine scores
        score = (overlap_score * 0.6) + phrase_bonus + (length_penalty * 0.1)

        # Add some randomness to simulate model variance
        import random

        score += random.uniform(-0.05, 0.05)

        # Ensure score is between 0 and 1
        score = max(0.0, min(1.0, score))

        return score

    @property
    def reranker_type(self) -> RerankerType:
        """Get the type of reranker."""
        return RerankerType.CROSS_ENCODER


@dataclass
class Feature:
    """Represents a feature used in feature-based reranking."""

    name: str
    weight: float = 1.0
    extractor: Callable[[str, Document], float] = field(repr=False)
    normalize: bool = True


@dataclass
class FeatureBasedConfig:
    """Configuration for feature-based reranking."""

    features: List[Feature] = field(default_factory=list)
    normalize_scores: bool = True
    additional_params: Dict[str, Any] = field(default_factory=dict)


class FeatureBasedReranker(Reranker):
    """Reranker using multiple features to score and rerank results."""

    def __init__(self, config: Optional[FeatureBasedConfig] = None):
        """
        Initialize feature-based reranker.

        Args:
            config: Reranker configuration (optional)
        """
        self.config = config or FeatureBasedConfig()

        # If no features are provided, use default features
        if not self.config.features:
            self.config.features = self._default_features()

    def rerank(self, results: SearchResults) -> SearchResults:
        """
        Rerank search results using multiple features.

        Args:
            results: The search results to rerank

        Returns:
            Reranked search results
        """
        query = results.query

        # Extract features for each result
        feature_scores = []
        for result in results.results:
            scores = {}
            for feature in self.config.features:
                score = feature.extractor(query, result.document)
                scores[feature.name] = score
            feature_scores.append(scores)

        # Normalize feature scores if configured
        if self.config.normalize_scores:
            feature_scores = self._normalize_feature_scores(feature_scores)

        # Calculate weighted scores and update results
        for i, result in enumerate(results.results):
            scores = feature_scores[i]
            weighted_score = 0.0

            for feature in self.config.features:
                weighted_score += scores[feature.name] * feature.weight

            # Store the original score and update with the reranked score
            result.original_score = result.score
            result.reranked_score = weighted_score
            result.score = weighted_score

            # Store feature scores in result metadata
            result.metadata["feature_scores"] = scores.copy()

        # Sort by the new scores
        results.sort_by_score()

        # Mark as reranked
        results.reranked = True
        results.metadata["reranker"] = "feature_based"
        results.metadata["features"] = [f.name for f in self.config.features]

        return results

    def _normalize_feature_scores(
        self, feature_scores: List[Dict[str, float]]
    ) -> List[Dict[str, float]]:
        """
        Normalize feature scores across all results.

        Args:
            feature_scores: List of dictionaries mapping feature names to scores

        Returns:
            Normalized feature scores
        """
        if not feature_scores:
            return []

        # Get all feature names
        feature_names = set()
        for scores in feature_scores:
            feature_names.update(scores.keys())

        # Normalize each feature
        for feature_name in feature_names:
            # Find min and max scores for this feature
            min_score = min(
                (scores.get(feature_name, 0.0) for scores in feature_scores),
                default=0.0,
            )
            max_score = max(
                (scores.get(feature_name, 0.0) for scores in feature_scores),
                default=1.0,
            )

            # Normalize scores
            if max_score > min_score:
                for scores in feature_scores:
                    if feature_name in scores:
                        scores[feature_name] = (scores[feature_name] - min_score) / (
                            max_score - min_score
                        )

        return feature_scores

    def _default_features(self) -> List[Feature]:
        """
        Create default features for feature-based reranking.

        Returns:
            List of default features
        """
        return [
            Feature(
                name="term_overlap",
                weight=0.4,
                extractor=self._term_overlap_extractor,
                normalize=True,
            ),
            Feature(
                name="exact_match",
                weight=0.3,
                extractor=self._exact_match_extractor,
                normalize=True,
            ),
            Feature(
                name="document_length",
                weight=0.1,
                extractor=self._document_length_extractor,
                normalize=True,
            ),
            Feature(
                name="original_score",
                weight=0.2,
                extractor=self._original_score_extractor,
                normalize=True,
            ),
        ]

    def _term_overlap_extractor(self, query: str, document: Document) -> float:
        """
        Extract term overlap feature.

        Args:
            query: The search query
            document: The document

        Returns:
            Term overlap score
        """
        query_terms = set(re.findall(r"\w+", query.lower()))
        doc_terms = set(re.findall(r"\w+", document.content.lower()))

        if not query_terms or not doc_terms:
            return 0.0

        return len(query_terms.intersection(doc_terms)) / len(query_terms)

    def _exact_match_extractor(self, query: str, document: Document) -> float:
        """
        Extract exact match feature.

        Args:
            query: The search query
            document: The document

        Returns:
            Exact match score
        """
        query_lower = query.lower()
        doc_lower = document.content.lower()

        if query_lower in doc_lower:
            return 1.0

        # Check for partial matches
        query_parts = query_lower.split()
        if len(query_parts) > 1:
            matches = 0
            for part in query_parts:
                if (
                    len(part) > 3 and part in doc_lower
                ):  # Only consider meaningful parts
                    matches += 1

            if matches > 0:
                return matches / len(query_parts)

        return 0.0

    def _document_length_extractor(self, query: str, document: Document) -> float:
        """
        Extract document length feature (shorter documents get higher scores).

        Args:
            query: The search query
            document: The document

        Returns:
            Document length score
        """
        doc_length = len(document.content)

        # Prefer documents between 100 and 2000 characters
        if doc_length < 100:
            return 0.5  # Too short
        elif doc_length < 2000:
            return 1.0  # Ideal length
        else:
            # Gradually decrease score for longer documents
            return 1.0 / (1.0 + math.log(1 + doc_length / 2000.0))

    def _original_score_extractor(self, query: str, document: Document) -> float:
        """
        Extract original score feature.

        Args:
            query: The search query
            document: The document

        Returns:
            Original score (assumed to be stored in document metadata)
        """
        # In a real implementation, this would access the original score
        # This is a placeholder that returns a default value
        return 0.5

    @property
    def reranker_type(self) -> RerankerType:
        """Get the type of reranker."""
        return RerankerType.FEATURE_BASED


@dataclass
class EnsembleConfig:
    """Configuration for ensemble reranking."""

    rerankers: List[Tuple[Reranker, float]] = field(default_factory=list)
    normalize_scores: bool = True
    additional_params: Dict[str, Any] = field(default_factory=dict)


class EnsembleReranker(Reranker):
    """Reranker combining multiple reranking strategies."""

    def __init__(self, config: Optional[EnsembleConfig] = None):
        """
        Initialize ensemble reranker.

        Args:
            config: Reranker configuration (optional)
        """
        self.config = config or EnsembleConfig()

    def rerank(self, results: SearchResults) -> SearchResults:
        """
        Rerank search results using an ensemble of rerankers.

        Args:
            results: The search results to rerank

        Returns:
            Reranked search results
        """
        if not self.config.rerankers:
            return results

        # Create a copy of the original results
        original_results = SearchResults(
            results=[
                SearchResult(
                    document=r.document,
                    score=r.score,
                    rank=r.rank,
                    highlights=r.highlights.copy() if r.highlights else None,
                    metadata=r.metadata.copy() if r.metadata else None,
                )
                for r in results.results
            ],
            query=results.query,
            metadata=results.metadata.copy(),
        )

        # Apply each reranker and collect scores
        all_scores = []
        for reranker, weight in self.config.rerankers:
            # Apply reranker to a copy of the original results
            reranked = reranker.rerank(
                SearchResults(
                    results=[
                        SearchResult(
                            document=r.document,
                            score=r.score,
                            rank=r.rank,
                            highlights=r.highlights.copy() if r.highlights else None,
                            metadata=r.metadata.copy() if r.metadata else None,
                        )
                        for r in original_results.results
                    ],
                    query=original_results.query,
                    metadata=original_results.metadata.copy(),
                )
            )

            # Collect scores
            scores = {}
            for result in reranked.results:
                scores[result.document.id] = result.score

            all_scores.append((scores, weight))

        # Normalize scores if configured
        if self.config.normalize_scores:
            all_scores = self._normalize_ensemble_scores(all_scores)

        # Calculate weighted ensemble scores
        ensemble_scores = {}
        for doc_id in {r.document.id for r in results.results}:
            weighted_score = 0.0
            for scores, weight in all_scores:
                if doc_id in scores:
                    weighted_score += scores[doc_id] * weight
            ensemble_scores[doc_id] = weighted_score

        # Update results with ensemble scores
        for result in results.results:
            doc_id = result.document.id
            if doc_id in ensemble_scores:
                result.original_score = result.score
                result.reranked_score = ensemble_scores[doc_id]
                result.score = ensemble_scores[doc_id]

        # Sort by the new scores
        results.sort_by_score()

        # Mark as reranked
        results.reranked = True
        results.metadata["reranker"] = "ensemble"
        results.metadata["ensemble_size"] = len(self.config.rerankers)

        return results

    def _normalize_ensemble_scores(
        self, all_scores: List[Tuple[Dict[str, float], float]]
    ) -> List[Tuple[Dict[str, float], float]]:
        """
        Normalize scores from each reranker.

        Args:
            all_scores: List of (scores_dict, weight) tuples

        Returns:
            Normalized scores
        """
        normalized = []

        for scores, weight in all_scores:
            if not scores:
                normalized.append((scores, weight))
                continue

            # Find min and max scores
            min_score = min(scores.values())
            max_score = max(scores.values())

            # Normalize scores
            if max_score > min_score:
                normalized_scores = {
                    doc_id: (score - min_score) / (max_score - min_score)
                    for doc_id, score in scores.items()
                }
                normalized.append((normalized_scores, weight))
            else:
                # If all scores are the same, set normalized score to 1
                normalized_scores = {doc_id: 1.0 for doc_id in scores}
                normalized.append((normalized_scores, weight))

        return normalized

    @property
    def reranker_type(self) -> RerankerType:
        """Get the type of reranker."""
        return RerankerType.ENSEMBLE


class CustomReranker(Reranker):
    """Custom reranker with user-provided reranking function."""

    def __init__(self, rerank_fn: Callable[[SearchResults], SearchResults]):
        """
        Initialize custom reranker.

        Args:
            rerank_fn: Function that reranks search results
        """
        self.rerank_fn = rerank_fn

    def rerank(self, results: SearchResults) -> SearchResults:
        """
        Rerank search results using the custom reranking function.

        Args:
            results: The search results to rerank

        Returns:
            Reranked search results
        """
        reranked = self.rerank_fn(results)

        # Mark as reranked
        reranked.reranked = True
        reranked.metadata["reranker"] = "custom"

        return reranked

    @property
    def reranker_type(self) -> RerankerType:
        """Get the type of reranker."""
        return RerankerType.CUSTOM


def create_cross_encoder_reranker(
    model_name: str = "default",
    max_length: int = 512,
    batch_size: int = 16,
    normalize_scores: bool = True,
    use_gpu: bool = True,
) -> CrossEncoderReranker:
    """
    Create a cross-encoder reranker.

    Args:
        model_name: Name of the cross-encoder model
        max_length: Maximum sequence length
        batch_size: Batch size for inference
        normalize_scores: Whether to normalize scores
        use_gpu: Whether to use GPU for inference

    Returns:
        A configured CrossEncoderReranker
    """
    config = CrossEncoderConfig(
        model_name=model_name,
        max_length=max_length,
        batch_size=batch_size,
        normalize_scores=normalize_scores,
        use_gpu=use_gpu,
    )

    return CrossEncoderReranker(config=config)


def create_feature_based_reranker(
    features: Optional[List[Feature]] = None, normalize_scores: bool = True
) -> FeatureBasedReranker:
    """
    Create a feature-based reranker.

    Args:
        features: List of features to use for reranking
        normalize_scores: Whether to normalize feature scores

    Returns:
        A configured FeatureBasedReranker
    """
    config = FeatureBasedConfig(
        features=features or [], normalize_scores=normalize_scores
    )

    return FeatureBasedReranker(config=config)


def create_ensemble_reranker(
    rerankers: List[Tuple[Reranker, float]], normalize_scores: bool = True
) -> EnsembleReranker:
    """
    Create an ensemble reranker.

    Args:
        rerankers: List of (reranker, weight) tuples
        normalize_scores: Whether to normalize scores

    Returns:
        A configured EnsembleReranker
    """
    config = EnsembleConfig(rerankers=rerankers, normalize_scores=normalize_scores)

    return EnsembleReranker(config=config)


def create_default_reranker() -> Reranker:
    """
    Create a default reranker.

    Returns:
        A default reranker (cross-encoder)
    """
    return create_cross_encoder_reranker()
