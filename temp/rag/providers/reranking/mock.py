"""Mock reranking provider implementation.

This module provides a mock reranking provider for testing purposes.
"""

import hashlib
from typing import List, Optional

from pepperpy.rag.errors import RerankingError
from pepperpy.rag.providers.reranking.base import BaseRerankingProvider
from pepperpy.utils.logging import get_logger

# Logger for this module
logger = get_logger(__name__)


class MockRerankingProvider(BaseRerankingProvider):
    """Mock reranking provider for testing.

    This provider generates deterministic scores based on text similarity.
    """

    def __init__(self, model_name: Optional[str] = None):
        """Initialize mock reranking provider.

        Args:
            model_name: Optional name for the mock model
        """
        super().__init__(model_name=model_name or "mock-reranker")

    def _text_to_hash(self, text: str) -> int:
        """Convert text to a deterministic hash value.

        Args:
            text: Input text

        Returns:
            Hash value
        """
        # Get hash of text
        text_hash = hashlib.sha256(text.encode()).hexdigest()
        # Convert first 8 bytes to integer
        return int(text_hash[:16], 16)

    def _compute_similarity(self, query: str, document: str) -> float:
        """Compute a deterministic similarity score between query and document.

        Args:
            query: Query text
            document: Document text

        Returns:
            Similarity score between 0 and 1
        """
        # Get hash values
        query_hash = self._text_to_hash(query)
        doc_hash = self._text_to_hash(document)

        # XOR the hashes and normalize to [0, 1]
        xor = query_hash ^ doc_hash
        similarity = 1.0 - (xor / (2**64 - 1))

        return similarity

    async def _compute_scores(
        self,
        query: str,
        documents: List[str],
        scores: Optional[List[float]] = None,
    ) -> List[float]:
        """Compute mock relevance scores.

        Args:
            query: The query string
            documents: List of documents to score
            scores: Optional list of initial scores

        Returns:
            List of relevance scores

        Raises:
            RerankingError: If there is an error during scoring
        """
        try:
            # Compute similarity scores
            similarities = [self._compute_similarity(query, doc) for doc in documents]

            if scores is not None:
                # Combine with initial scores using average
                return [(sim + score) / 2 for sim, score in zip(similarities, scores)]

            return similarities

        except Exception as e:
            raise RerankingError(f"Error in mock reranking provider: {e}")
