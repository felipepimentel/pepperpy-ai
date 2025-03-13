"""
PepperPy RAG Pipeline Reranking Stage Module.

This module contains the reranking stage for the RAG pipeline.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from pepperpy.errors import PepperpyError, PepperpyValueError
from pepperpy.rag.document.core import Document as OldDocument
from pepperpy.rag.document.core import Metadata as OldMetadata
from pepperpy.rag.interfaces import PipelineStage, RerankerProvider
from pepperpy.rag.models import Document, Metadata, RerankingResult, RetrievalResult
from pepperpy.rag.pipeline.stages.base import StageConfig


@dataclass
class RerankingStageConfig(StageConfig):
    """Configuration for the reranking stage."""

    top_k: int = 3

    def __post_init__(self):
        if not self.type:
            self.type = "reranking"


class RerankingStage(PipelineStage):
    """Reranking stage for the RAG pipeline."""

    def __init__(
        self,
        reranker_provider: RerankerProvider,
        config: Optional[RerankingStageConfig] = None,
    ):
        """Initialize the reranking stage.

        Args:
            reranker_provider: The reranker provider.
            config: The stage configuration.
        """
        self.reranker_provider = reranker_provider
        self.config = config or RerankingStageConfig(name="reranking", type="reranking")

    def process(self, retrieval_result: RetrievalResult) -> RerankingResult:
        """Process retrieval results.

        Args:
            retrieval_result: The retrieval results to process.

        Returns:
            The reranking results.

        Raises:
            PepperpyError: If the reranking fails.
        """
        try:
            query = retrieval_result.query
            documents = retrieval_result.documents

            if not documents:
                return RerankingResult(
                    documents=[],
                    query=query,
                    scores=[],
                )

            # Convert documents to the format expected by the reranker provider
            # The reranker provider expects OldDocument objects
            provider_compatible_docs: List[OldDocument] = []
            for doc in documents:
                # Convert Document to OldDocument
                # First convert metadata to OldMetadata
                old_metadata = OldMetadata()
                if doc.metadata:
                    metadata_dict = doc.metadata.to_dict()
                    # Set attributes on OldMetadata
                    if "source" in metadata_dict:
                        old_metadata.source = metadata_dict["source"]
                    if "created_at" in metadata_dict:
                        old_metadata.created_at = metadata_dict["created_at"]
                    if "author" in metadata_dict:
                        old_metadata.author = metadata_dict["author"]
                    if "title" in metadata_dict:
                        old_metadata.title = metadata_dict["title"]
                    if "tags" in metadata_dict and isinstance(
                        metadata_dict["tags"], list
                    ):
                        old_metadata.tags = set(metadata_dict["tags"])
                    if "custom" in metadata_dict and isinstance(
                        metadata_dict["custom"], dict
                    ):
                        old_metadata.custom = metadata_dict["custom"]

                # Create OldDocument with OldMetadata
                old_doc = OldDocument(
                    id=doc.id,
                    content=doc.content,
                    metadata=old_metadata,
                )
                provider_compatible_docs.append(old_doc)

            # Rerank the documents
            reranked_documents = self.reranker_provider.rerank(
                query, provider_compatible_docs
            )

            # Get scores if available
            try:
                scores = self.reranker_provider.get_scores(
                    query, provider_compatible_docs
                )
            except (NotImplementedError, AttributeError):
                scores = None

            # Limit to top-k if there are enough documents
            if len(reranked_documents) > self.config.top_k:
                reranked_documents = reranked_documents[: self.config.top_k]
                if scores:
                    scores = scores[: self.config.top_k]

            # Convert reranked documents back to our Document type
            result_documents: List[Document] = []
            for doc in reranked_documents:
                # Create a new Document with the same content and metadata
                metadata_obj = Metadata()
                if hasattr(doc, "metadata") and doc.metadata:
                    if isinstance(doc.metadata, dict):
                        metadata_obj = Metadata.from_dict(doc.metadata)
                    elif hasattr(doc.metadata, "to_dict"):
                        metadata_obj = Metadata.from_dict(doc.metadata.to_dict())

                result_documents.append(
                    Document(
                        id=doc.id if hasattr(doc, "id") else "",
                        content=doc.content if hasattr(doc, "content") else "",
                        metadata=metadata_obj,
                    )
                )

            # Return the results with our Document type
            return RerankingResult(
                documents=result_documents,
                query=query,
                scores=scores,
            )
        except Exception as e:
            raise PepperpyError(
                f"Failed to rerank documents for query: {retrieval_result.query}. Error: {str(e)}"
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
        cls, data: Dict[str, Any], reranker_provider: RerankerProvider
    ) -> "RerankingStage":
        """Create a stage from a dictionary.

        Args:
            data: The stage data.
            reranker_provider: The reranker provider.

        Returns:
            The created stage.

        Raises:
            PepperpyValueError: If the data is invalid.
        """
        if not isinstance(data, dict):
            raise PepperpyValueError(f"Expected dictionary, got {type(data).__name__}")

        if data.get("type") != "reranking":
            raise PepperpyValueError(
                f"Expected type 'reranking', got {data.get('type')}"
            )

        params = data.get("params", {})
        config = RerankingStageConfig(
            name=data.get("name", "reranking"),
            type="reranking",
            enabled=data.get("enabled", True),
            params=params,
        )

        if "top_k" in params:
            config.top_k = params["top_k"]

        return cls(
            reranker_provider=reranker_provider,
            config=config,
        )
