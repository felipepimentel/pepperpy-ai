"""Reranking stage for the RAG pipeline."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from pepperpy.core.errors import PepperPyError
from pepperpy.rag.document.core import DocumentChunk


@dataclass
class RerankingResult:
    """Result from the reranking stage."""

    chunks: List[DocumentChunk]
    metadata: Dict[str, Any] = field(default_factory=dict)
    scores: Optional[List[float]] = None


@dataclass
class RerankingStageConfig:
    """Configuration for the reranking stage."""

    provider: str
    top_k: int = 3
    score_threshold: float = 0.5
    metadata_filters: Optional[Dict[str, Any]] = None


class RerankerProvider(ABC):
    """Base class for reranking providers."""

    @abstractmethod
    async def rerank(
        self,
        query: str,
        chunks: List[DocumentChunk],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> List[DocumentChunk]:
        """Rerank document chunks.

        Args:
            query: User query
            chunks: Document chunks to rerank
            metadata: Optional metadata

        Returns:
            Reranked document chunks

        Raises:
            PepperPyError: If reranking fails
        """
        pass


class RerankingStage:
    """Stage for reranking retrieved document chunks."""

    def __init__(self, config: RerankingStageConfig):
        """Initialize the stage.

        Args:
            config: Stage configuration
        """
        self.config = config

    async def process(
        self,
        query: str,
        chunks: List[DocumentChunk],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> List[DocumentChunk]:
        """Process the query and chunks to rerank them.

        Args:
            query: User query
            chunks: Retrieved document chunks
            metadata: Optional metadata

        Returns:
            List of reranked document chunks

        Raises:
            PepperPyError: If reranking fails
        """
        try:
            # TODO: Call reranking provider to rerank chunks
            # This should be implemented by the provider
            raise PepperPyError("Reranking not implemented")

        except Exception as e:
            raise PepperPyError(f"Error in reranking stage: {e}")


# Export all classes
__all__ = [
    "RerankingStageConfig",
    "RerankerProvider",
    "RerankingStage",
    "RerankingResult",
]
