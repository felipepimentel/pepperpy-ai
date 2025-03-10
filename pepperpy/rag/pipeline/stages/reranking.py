"""Reranking stage implementation.

This module provides functionality for reranking retrieved documents using
more sophisticated similarity metrics.
"""

from typing import Any, List, Optional, Union

from pepperpy.errors import PipelineStageError
from pepperpy.rag.pipeline.base import BasePipelineStage
from pepperpy.rag.providers.reranking.base import BaseRerankingProvider
from pepperpy.rag.storage.types import SearchResult


class RerankingStage(BasePipelineStage):
    """Reranking stage for improving document ranking.

    This stage takes a list of retrieved documents and reranks them using
    a more sophisticated similarity metric, typically based on cross-attention
    between the query and documents.
    """

    def __init__(
        self,
        reranking_provider: BaseRerankingProvider,
        limit: Optional[int] = None,
        min_score: Optional[float] = None,
        **kwargs: Any,
    ) -> None:
        """Initialize the reranking stage.

        Args:
            reranking_provider: Provider for reranking documents.
            limit: Maximum number of documents to return after reranking.
            min_score: Minimum score threshold for reranked documents.
            **kwargs: Additional keyword arguments.
        """
        super().__init__(**kwargs)
        self.reranking_provider = reranking_provider
        self.limit = limit
        self.min_score = min_score

    async def process(
        self,
        query: str,
        documents: Union[SearchResult, List[SearchResult]],
        **kwargs: Any,
    ) -> List[SearchResult]:
        """Process a query and documents to produce reranked results.

        Args:
            query: Query text to compare documents against.
            documents: Document or list of documents to rerank.
            **kwargs: Additional arguments passed to the reranking provider.

        Returns:
            List of reranked search results sorted by new scores.

        Raises:
            PipelineStageError: If reranking fails.
        """
        try:
            # Convert single document to list
            if isinstance(documents, SearchResult):
                documents = [documents]

            # Skip reranking if no documents
            if not documents:
                return []

            # Extract document texts and metadata
            doc_texts = []
            doc_metadata = []
            for result in documents:
                # Combine chunk contents into single text
                text = "\n".join(chunk.content for chunk in result.document.chunks)
                doc_texts.append(text)
                doc_metadata.append({
                    "original_score": result.score,
                    "document_id": result.document.id,
                })

            # Rerank documents
            reranked_scores = await self.reranking_provider.rerank(
                query=query,
                documents=doc_texts,
                **kwargs,
            )

            # Create reranked results
            reranked_results = []
            for i, (result, score) in enumerate(zip(documents, reranked_scores)):
                # Skip if below minimum score
                if self.min_score is not None and score < self.min_score:
                    continue

                # Create new search result with reranked score
                reranked_result = SearchResult(
                    document=result.document,
                    score=score,
                    metadata={
                        **(result.metadata or {}),
                        "original_score": result.score,
                        "rerank_position": i,
                    },
                )
                reranked_results.append(reranked_result)

            # Sort by score in descending order
            reranked_results.sort(key=lambda x: x.score, reverse=True)

            # Limit results if specified
            if self.limit is not None:
                reranked_results = reranked_results[: self.limit]

            return reranked_results

        except Exception as e:
            raise PipelineStageError(f"Error reranking documents: {str(e)}") from e
