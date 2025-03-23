"""Pipeline class for PepperPy RAG.

This module provides the RAGPipeline class for orchestrating the RAG pipeline stages.
"""

import logging
from typing import Any, List, Optional

from ..document import Document
from ..query import Query
from ..result import RetrievalResult
from .stages import (
    ChunkingStage,
    EmbeddingStage,
    PipelineStage,
    RerankingStage,
    RetrievalStage,
)


class RAGPipeline:
    """RAG pipeline class.

    This class orchestrates the RAG pipeline stages.
    """

    def __init__(
        self,
        stages: Optional[List[PipelineStage]] = None,
    ):
        """Initialize the pipeline.

        Args:
            stages: Optional list of pipeline stages
        """
        self.stages = stages or [
            ChunkingStage(),
            EmbeddingStage(),
            RetrievalStage(),
            RerankingStage(),
        ]
        self._logger = logging.getLogger(__name__)

    async def process(
        self,
        documents: List[Document],
        query: Optional[Query] = None,
        **kwargs: Any,
    ) -> RetrievalResult:
        """Process documents through the pipeline.

        Args:
            documents: List of documents to process
            query: Optional query for retrieval/reranking
            **kwargs: Additional arguments

        Returns:
            Retrieval results
        """
        self._logger.info(f"Processing {len(documents)} documents through pipeline")

        # Process documents through each stage
        processed_docs = documents
        for stage in self.stages:
            self._logger.debug(f"Processing through stage: {stage.__class__.__name__}")
            processed_docs = await stage.process(
                processed_docs,
                query=query.text if query else None,
                **kwargs,
            )

        # Create retrieval result
        result = RetrievalResult(
            query=query or Query(text=""),  # Use empty query if none provided
            documents=processed_docs,
            scores=[1.0] * len(processed_docs),  # TODO: Implement actual scoring
            metadata={
                "pipeline_stages": [stage.__class__.__name__ for stage in self.stages],
            },
        )

        self._logger.info("Pipeline processing complete")
        return result
