"""Cross-encoder reranking provider implementation.

This module provides reranking functionality using cross-encoder models.
"""

import asyncio
from typing import List, Optional

import torch
from sentence_transformers import CrossEncoder

from pepperpy.rag.errors import RerankingError
from pepperpy.rag.providers.reranking.base import BaseRerankingProvider
from pepperpy.utils.logging import get_logger

# Logger for this module
logger = get_logger(__name__)

# Default model for cross-encoder
DEFAULT_MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"

# Maximum batch size for scoring
MAX_BATCH_SIZE = 32


class CrossEncoderProvider(BaseRerankingProvider):
    """Cross-encoder reranking provider.

    This provider uses cross-encoder models for reranking documents.
    """

    def __init__(
        self,
        model_name: str = DEFAULT_MODEL,
        batch_size: int = MAX_BATCH_SIZE,
        device: Optional[str] = None,
    ):
        """Initialize cross-encoder provider.

        Args:
            model_name: Name of the model to use
            batch_size: Maximum number of pairs to score in one batch
            device: Device to run model on (cuda/cpu)
        """
        super().__init__(model_name=model_name)
        self.batch_size = min(batch_size, MAX_BATCH_SIZE)

        # Determine device
        if device is None:
            device = "cuda" if torch.cuda.is_available() else "cpu"
        self.device = device

        # Initialize model
        self.model = CrossEncoder(model_name, device=device)

    async def _score_batch(
        self,
        query: str,
        documents: List[str],
    ) -> List[float]:
        """Score a batch of query-document pairs.

        Args:
            query: The query string
            documents: List of documents to score

        Returns:
            List of relevance scores

        Raises:
            RerankingError: If there is an error during scoring
        """
        try:
            # Create pairs for scoring
            pairs = [[query, doc] for doc in documents]

            # Run in executor to avoid blocking
            loop = asyncio.get_event_loop()
            scores = await loop.run_in_executor(
                None,
                lambda: self.model.predict(pairs),
            )

            return scores.tolist() if isinstance(scores, torch.Tensor) else scores

        except Exception as e:
            raise RerankingError(f"Error scoring batch with cross-encoder: {e}")

    async def _compute_scores(
        self,
        query: str,
        documents: List[str],
        scores: Optional[List[float]] = None,
    ) -> List[float]:
        """Compute relevance scores using cross-encoder model.

        Args:
            query: The query string
            documents: List of documents to score
            scores: Optional list of initial scores (not used)

        Returns:
            List of relevance scores

        Raises:
            RerankingError: If there is an error during scoring
        """
        try:
            # Split documents into batches
            batches = [
                documents[i : i + self.batch_size]
                for i in range(0, len(documents), self.batch_size)
            ]

            # Score each batch
            tasks = [self._score_batch(query, batch) for batch in batches]
            results = await asyncio.gather(*tasks)

            # Combine results
            scores = []
            for batch_scores in results:
                scores.extend(batch_scores)

            return scores

        except Exception as e:
            raise RerankingError(f"Error in cross-encoder provider: {e}")
