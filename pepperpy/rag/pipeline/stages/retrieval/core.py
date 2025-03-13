"""
PepperPy RAG Pipeline Retrieval Stage Module.

This module contains the retrieval stage for the RAG pipeline.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional

from pepperpy.errors import PepperpyError, PepperpyValueError
from pepperpy.rag.interfaces import EmbeddingProvider, PipelineStage
from pepperpy.rag.models import RetrievalResult
from pepperpy.rag.pipeline.stages.base import StageConfig


@dataclass
class RetrievalStageConfig(StageConfig):
    """Configuration for the retrieval stage."""

    top_k: int = 5

    def __post_init__(self):
        if not self.type:
            self.type = "retrieval"


class RetrievalStage(PipelineStage):
    """Retrieval stage for the RAG pipeline."""

    def __init__(
        self,
        embedding_provider: EmbeddingProvider,
        document_store: Any,  # DocumentStore
        config: Optional[RetrievalStageConfig] = None,
    ):
        """Initialize the retrieval stage.

        Args:
            embedding_provider: The embedding provider.
            document_store: The document store.
            config: The stage configuration.
        """
        self.embedding_provider = embedding_provider
        self.document_store = document_store
        self.config = config or RetrievalStageConfig(name="retrieval", type="retrieval")

    def process(self, query: str) -> RetrievalResult:
        """Process a query.

        Args:
            query: The query to process.

        Returns:
            The retrieval results.

        Raises:
            PepperpyError: If the retrieval fails.
        """
        try:
            # Embed the query
            query_embedding = self.embedding_provider.embed_query(query)

            # Get the top-k documents from the document store
            documents, scores = self.document_store.search(
                query_embedding, top_k=self.config.top_k
            )

            # Return the results
            return RetrievalResult(
                documents=documents,
                query=query,
                query_embedding=query_embedding,
                scores=scores,
            )
        except Exception as e:
            raise PepperpyError(
                f"Failed to retrieve documents for query: {query}. Error: {str(e)}"
            ) from e

    def to_dict(self) -> Dict[str, Any]:
        """Convert the stage to a dictionary.

        Returns:
            The stage as a dictionary.
        """
        return {
            "type": self.config.type,
            "name": self.config.name,
            "enabled": self.config.enabled,
            "params": {
                "top_k": self.config.top_k,
                **self.config.params,
            },
        }

    @classmethod
    def from_dict(
        cls,
        data: Dict[str, Any],
        embedding_provider: EmbeddingProvider,
        document_store: Any,
    ) -> "RetrievalStage":
        """Create a stage from a dictionary.

        Args:
            data: The stage data.
            embedding_provider: The embedding provider.
            document_store: The document store.

        Returns:
            The created stage.

        Raises:
            PepperpyValueError: If the data is invalid.
        """
        if not isinstance(data, dict):
            raise PepperpyValueError(f"Expected dictionary, got {type(data).__name__}")

        if data.get("type") != "retrieval":
            raise PepperpyValueError(
                f"Expected type 'retrieval', got {data.get('type')}"
            )

        params = data.get("params", {})
        config = RetrievalStageConfig(
            name=data.get("name", "retrieval"),
            type="retrieval",
            enabled=data.get("enabled", True),
            params=params,
        )

        if "top_k" in params:
            config.top_k = params["top_k"]

        return cls(
            embedding_provider=embedding_provider,
            document_store=document_store,
            config=config,
        )
