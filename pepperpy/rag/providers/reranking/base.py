"""Base reranking provider implementation.

This module provides the base class for reranking providers.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Tuple

from pepperpy.rag.errors import RerankingError
from pepperpy.utils.logging import get_logger

# Logger for this module
logger = get_logger(__name__)


class BaseRerankingProvider(ABC):
    """Base class for reranking providers.

    This class defines the interface that all reranking providers must implement.
    """

    def __init__(self, model_name: Optional[str] = None):
        """Initialize base reranking provider.

        Args:
            model_name: Optional name of the model to use
        """
        self.model_name = model_name

    @abstractmethod
    async def _compute_scores(
        self,
        query: str,
        documents: List[str],
        scores: Optional[List[float]] = None,
    ) -> List[float]:
        """Internal method to compute relevance scores.

        Args:
            query: The query string
            documents: List of documents to score
            scores: Optional list of initial scores

        Returns:
            List of relevance scores

        Raises:
            RerankingError: If there is an error during scoring
        """
        ...

    async def rerank(
        self,
        query: str,
        documents: List[str],
        scores: Optional[List[float]] = None,
    ) -> List[Tuple[int, float]]:
        """Rerank documents based on relevance to query.

        Args:
            query: The query string
            documents: List of documents to rerank
            scores: Optional list of initial scores

        Returns:
            List of tuples containing (original_index, new_score)

        Raises:
            RerankingError: If there is an error during reranking
        """
        try:
            # Compute relevance scores
            new_scores = await self._compute_scores(
                query=query,
                documents=documents,
                scores=scores,
            )

            # Create index-score pairs
            pairs = list(enumerate(new_scores))

            # Sort by score in descending order
            pairs.sort(key=lambda x: x[1], reverse=True)

            return pairs

        except Exception as e:
            raise RerankingError(f"Error in reranking: {e}")

    def __repr__(self) -> str:
        """Get string representation of provider.

        Returns:
            String representation
        """
        return f"{self.__class__.__name__}(model_name={self.model_name})"
