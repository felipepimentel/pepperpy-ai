"""RAG pipeline orchestrator.

This module provides a pipeline orchestrator for the RAG system, integrating
the chunking, metadata extraction, and transformation components into a
cohesive workflow.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

from pepperpy.core.telemetry import get_provider_telemetry
from pepperpy.rag.chunking import (
    ChunkingConfig,
    ChunkingPipeline,
    ChunkingStrategy,
)
from pepperpy.rag.metadata import (
    MetadataEnrichmentPipeline,
    MetadataExtractorConfig,
    MetadataType,
)
from pepperpy.rag.transform import (
    DocumentTransformationPipeline,
    TransformationConfig,
    TransformationType,
)
from pepperpy.types.common import Document

# Set up telemetry
telemetry = get_provider_telemetry("rag_pipeline")


class PipelineStage(Enum):
    """Stages in the RAG pipeline."""

    TRANSFORM = "transform"  # Document transformation
    METADATA = "metadata"  # Metadata extraction
    CHUNK = "chunk"  # Document chunking
    EMBED = "embed"  # Document embedding
    INDEX = "index"  # Document indexing
    RETRIEVE = "retrieve"  # Document retrieval
    RERANK = "rerank"  # Result reranking
    GENERATE = "generate"  # Response generation


@dataclass
class PipelineConfig:
    """Configuration for the RAG pipeline.

    This class defines the configuration for the RAG pipeline, including
    which stages to include and their order.
    """

    stages: List[PipelineStage] = field(
        default_factory=lambda: [
            PipelineStage.TRANSFORM,
            PipelineStage.METADATA,
            PipelineStage.CHUNK,
        ]
    )
    transformation_config: Optional[TransformationConfig] = None
    metadata_config: Optional[MetadataExtractorConfig] = None
    chunking_config: Optional[ChunkingConfig] = None
    params: Dict[str, Any] = field(default_factory=dict)


class RAGPipeline:
    """Pipeline for processing documents in the RAG system.

    This class provides a pipeline for processing documents in the RAG system,
    including transformation, metadata extraction, and chunking.
    """

    def __init__(self, config: Optional[PipelineConfig] = None):
        """Initialize the RAG pipeline.

        Args:
            config: Optional configuration for the pipeline.
                If not provided, default configuration is used.
        """
        self.config = config or PipelineConfig()
        self._init_components()

    def _init_components(self):
        """Initialize pipeline components based on configuration."""
        # Initialize transformation pipeline if needed
        if PipelineStage.TRANSFORM in self.config.stages:
            self.transformation_pipeline = DocumentTransformationPipeline(
                transformers=None  # Use default transformers
            )
        else:
            self.transformation_pipeline = None

        # Initialize metadata pipeline if needed
        if PipelineStage.METADATA in self.config.stages:
            self.metadata_pipeline = MetadataEnrichmentPipeline(
                extractors=None  # Use default extractors
            )
        else:
            self.metadata_pipeline = None

        # Initialize chunking pipeline if needed
        if PipelineStage.CHUNK in self.config.stages:
            # For now, just use a single chunking strategy
            # In a real implementation, this would be more configurable
            chunking_config = self.config.chunking_config or ChunkingConfig()
            self.chunking_pipeline = ChunkingPipeline(
                strategies=[(chunking_config.strategy, chunking_config)]
            )
        else:
            self.chunking_pipeline = None

    def process(self, document: Document) -> List[Document]:
        """Process a document through the RAG pipeline.

        Args:
            document: The document to process.

        Returns:
            A list of processed documents. If chunking is enabled, this will
            be a list of chunks. Otherwise, it will be a list containing the
            single processed document.
        """
        telemetry.info(
            "rag_pipeline_started",
            "Processing document through RAG pipeline",
            {"document_id": document.id},
        )

        processed_document = document
        result_documents = [processed_document]

        # Apply each stage in the configured order
        for stage in self.config.stages:
            if stage == PipelineStage.TRANSFORM and self.transformation_pipeline:
                # Transform the document
                telemetry.info(
                    "rag_pipeline_transform_stage",
                    "Applying transformation stage",
                    {"document_id": document.id},
                )
                result_documents = [
                    self.transformation_pipeline.process(doc)
                    for doc in result_documents
                ]

            elif stage == PipelineStage.METADATA and self.metadata_pipeline:
                # Extract metadata
                telemetry.info(
                    "rag_pipeline_metadata_stage",
                    "Applying metadata extraction stage",
                    {"document_id": document.id},
                )
                result_documents = [
                    self.metadata_pipeline.process(doc) for doc in result_documents
                ]

            elif stage == PipelineStage.CHUNK and self.chunking_pipeline:
                # Chunk the document
                telemetry.info(
                    "rag_pipeline_chunk_stage",
                    "Applying chunking stage",
                    {"document_id": document.id},
                )
                chunked_documents = []
                for doc in result_documents:
                    chunks = self.chunking_pipeline.process(doc)
                    chunked_documents.extend(chunks)
                result_documents = chunked_documents

        telemetry.info(
            "rag_pipeline_completed",
            f"RAG pipeline completed, produced {len(result_documents)} documents",
            {"document_id": document.id, "result_count": len(result_documents)},
        )

        return result_documents

    def batch_process(self, documents: List[Document]) -> List[Document]:
        """Process multiple documents through the RAG pipeline.

        Args:
            documents: The documents to process.

        Returns:
            A list of processed documents.
        """
        telemetry.info(
            "rag_batch_pipeline_started",
            f"Processing {len(documents)} documents through RAG pipeline",
            {"document_count": len(documents)},
        )

        result_documents = []
        for doc in documents:
            processed_docs = self.process(doc)
            result_documents.extend(processed_docs)

        telemetry.info(
            "rag_batch_pipeline_completed",
            f"RAG batch pipeline completed, produced {len(result_documents)} documents",
            {"input_count": len(documents), "output_count": len(result_documents)},
        )

        return result_documents


class RAGPipelineBuilder:
    """Builder for creating RAG pipelines with fluent interface.

    This class provides a fluent interface for building RAG pipelines with
    specific configurations.
    """

    def __init__(self):
        """Initialize the RAG pipeline builder."""
        self.stages = []
        self.transformation_config = None
        self.metadata_config = None
        self.chunking_config = None
        self.params = {}

    def with_transformation(
        self,
        include_types: Optional[List[TransformationType]] = None,
        exclude_types: Optional[List[TransformationType]] = None,
        preserve_original: bool = True,
    ) -> "RAGPipelineBuilder":
        """Add transformation stage to the pipeline.

        Args:
            include_types: Optional list of transformation types to include.
            exclude_types: Optional list of transformation types to exclude.
            preserve_original: Whether to preserve the original content.

        Returns:
            The builder instance for method chaining.
        """
        self.stages.append(PipelineStage.TRANSFORM)
        self.transformation_config = TransformationConfig(
            include_types=include_types,
            exclude_types=exclude_types,
            preserve_original=preserve_original,
        )
        return self

    def with_metadata_extraction(
        self,
        include_types: Optional[List[MetadataType]] = None,
        exclude_types: Optional[List[MetadataType]] = None,
        confidence_threshold: float = 0.5,
    ) -> "RAGPipelineBuilder":
        """Add metadata extraction stage to the pipeline.

        Args:
            include_types: Optional list of metadata types to include.
            exclude_types: Optional list of metadata types to exclude.
            confidence_threshold: Minimum confidence for extracted metadata.

        Returns:
            The builder instance for method chaining.
        """
        self.stages.append(PipelineStage.METADATA)
        self.metadata_config = MetadataExtractorConfig(
            include_types=include_types,
            exclude_types=exclude_types,
            confidence_threshold=confidence_threshold,
        )
        return self

    def with_chunking(
        self,
        strategy: ChunkingStrategy = ChunkingStrategy.FIXED_SIZE,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        respect_boundaries: bool = True,
    ) -> "RAGPipelineBuilder":
        """Add chunking stage to the pipeline.

        Args:
            strategy: The chunking strategy to use.
            chunk_size: The size of each chunk.
            chunk_overlap: The overlap between chunks.
            respect_boundaries: Whether to respect sentence/paragraph boundaries.

        Returns:
            The builder instance for method chaining.
        """
        self.stages.append(PipelineStage.CHUNK)
        self.chunking_config = ChunkingConfig(
            strategy=strategy,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            respect_sentence_boundaries=respect_boundaries,
            respect_paragraph_boundaries=respect_boundaries,
        )
        return self

    def with_param(self, key: str, value: Any) -> "RAGPipelineBuilder":
        """Add a custom parameter to the pipeline configuration.

        Args:
            key: The parameter key.
            value: The parameter value.

        Returns:
            The builder instance for method chaining.
        """
        self.params[key] = value
        return self

    def build(self) -> RAGPipeline:
        """Build the RAG pipeline with the configured settings.

        Returns:
            A configured RAG pipeline.
        """
        config = PipelineConfig(
            stages=self.stages,
            transformation_config=self.transformation_config,
            metadata_config=self.metadata_config,
            chunking_config=self.chunking_config,
            params=self.params,
        )
        return RAGPipeline(config)


# Convenience functions


def create_default_pipeline() -> RAGPipeline:
    """Create a default RAG pipeline with standard settings.

    Returns:
        A configured RAG pipeline with default settings.
    """
    return (
        RAGPipelineBuilder()
        .with_transformation()
        .with_metadata_extraction()
        .with_chunking()
        .build()
    )


def create_simple_pipeline() -> RAGPipeline:
    """Create a simple RAG pipeline with minimal processing.

    This pipeline only includes chunking, without transformation or metadata extraction.

    Returns:
        A configured RAG pipeline with minimal processing.
    """
    return RAGPipelineBuilder().with_chunking().build()


def create_metadata_focused_pipeline() -> RAGPipeline:
    """Create a RAG pipeline focused on metadata extraction.

    This pipeline includes transformation and metadata extraction, but not chunking.

    Returns:
        A configured RAG pipeline focused on metadata extraction.
    """
    return RAGPipelineBuilder().with_transformation().with_metadata_extraction().build()


def process_document(
    document: Document, pipeline: Optional[RAGPipeline] = None
) -> List[Document]:
    """Process a document through a RAG pipeline.

    Args:
        document: The document to process.
        pipeline: Optional RAG pipeline to use. If not provided, a default pipeline is used.

    Returns:
        A list of processed documents.
    """
    if pipeline is None:
        pipeline = create_default_pipeline()
    return pipeline.process(document)


def process_documents(
    documents: List[Document], pipeline: Optional[RAGPipeline] = None
) -> List[Document]:
    """Process multiple documents through a RAG pipeline.

    Args:
        documents: The documents to process.
        pipeline: Optional RAG pipeline to use. If not provided, a default pipeline is used.

    Returns:
        A list of processed documents.
    """
    if pipeline is None:
        pipeline = create_default_pipeline()
    return pipeline.batch_process(documents)
