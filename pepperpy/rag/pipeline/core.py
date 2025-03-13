"""RAG Pipeline implementation.

This module provides the core implementation of the RAG pipeline system,
which orchestrates the retrieval, reranking, and generation stages.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Generic, List, Optional, TypeVar, Union, cast

from pepperpy.core.telemetry import get_provider_telemetry
from pepperpy.errors import PepperpyError
from pepperpy.rag.chunking import (
    ChunkingConfig as ChunkingConfigOld,
)
from pepperpy.rag.chunking import (
    ChunkingPipeline,
)
from pepperpy.rag.chunking import (
    ChunkingStrategy as ChunkingStrategyOld,
)
from pepperpy.rag.interfaces import (
    AbstractPipelineStage,
    EmbeddingProvider,
    GenerationProvider,
    RerankerProvider,
)
from pepperpy.rag.metadata import (
    MetadataEnrichmentPipeline,
)
from pepperpy.rag.models import (
    ChunkingConfig,
    ChunkingStrategy,
    Document,
    Metadata,
    MetadataExtractorConfig,
    MetadataType,
    RerankingResult,
    RetrievalResult,
    TransformationConfig,
    TransformationType,
)
from pepperpy.rag.pipeline.stages.generation import (
    GenerationStage,
    GenerationStageConfig,
)
from pepperpy.rag.pipeline.stages.reranking import (
    RerankingStage,
    RerankingStageConfig,
)
from pepperpy.rag.pipeline.stages.retrieval import (
    RetrievalStage,
    RetrievalStageConfig,
)
from pepperpy.rag.transform import (
    DocumentTransformationPipeline,
)
from pepperpy.types.common import Document as CommonDocument
from pepperpy.types.common import Metadata as CommonMetadata
from pepperpy.utils.logging import get_logger

# Set up logger
logger = get_logger(__name__)

# Set up telemetry
telemetry = get_provider_telemetry("rag_pipeline")

# Type variables for generic pipeline components
Input = TypeVar("Input")
Output = TypeVar("Output")

# Pipeline specific types
PipelineInput = Union[str, Dict[str, Any]]
PipelineOutput = Union[str, List[Any], Dict[str, Any]]
PipelineStep = Union[str, Dict[str, Any]]


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

    This class defines the configuration for both the traditional RAG pipeline
    and the advanced pipeline with retrieval, reranking, and generation stages.
    """

    # General pipeline configuration
    name: str = "rag_pipeline"
    description: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    # Traditional pipeline stages configuration
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

    # Advanced pipeline stages configuration
    retrieval_config: Optional[RetrievalStageConfig] = None
    reranking_config: Optional[RerankingStageConfig] = None
    generation_config: Optional[GenerationStageConfig] = None

    # Additional parameters
    params: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Initialize default values."""
        if self.metadata is None:
            self.metadata = {}
        if self.params is None:
            self.params = {}


class AbstractPipeline(Generic[Input, Output]):
    """Base class for pipelines.

    A pipeline is a sequence of stages that process data in order.
    """

    def __init__(self, config: PipelineConfig):
        """Initialize the pipeline.

        Args:
            config: Pipeline configuration
        """
        self.config = config
        self.stages: List[AbstractPipelineStage] = []

    def add_stage(self, stage: AbstractPipelineStage) -> "AbstractPipeline":
        """Add a stage to the pipeline.

        Args:
            stage: The stage to add

        Returns:
            The pipeline instance for chaining
        """
        self.stages.append(stage)
        return self

    async def process(
        self,
        input_data: Input,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Output:
        """Process input data through all stages.

        Args:
            input_data: The input data to process
            metadata: Optional metadata to include with the processing

        Returns:
            The final processed output data

        Raises:
            PepperpyError: If processing fails
        """
        current_data = input_data
        current_metadata = metadata or {}

        try:
            for stage in self.stages:
                current_data = await stage.process(current_data, current_metadata)
            return cast(Output, current_data)
        except Exception as e:
            raise PepperpyError(f"Pipeline processing failed: {str(e)}") from e


class RAGPipeline:
    """RAG Pipeline implementation that coordinates multiple stages.

    This class provides the implementation of the RAG pipeline, which can operate
    in two modes:
    1. Traditional mode - for document preprocessing (transform, metadata, chunk)
    2. Advanced mode - for RAG retrieval, reranking, and generation
    """

    def __init__(self, config: Optional[PipelineConfig] = None):
        """Initialize the RAG pipeline.

        Args:
            config: Optional pipeline configuration
        """
        self.config = config or PipelineConfig()

        # Initialize pipeline components as None
        self.transform_pipeline: Optional[DocumentTransformationPipeline] = None
        self.metadata_pipeline: Optional[MetadataEnrichmentPipeline] = None
        self.chunking_pipeline: Optional[ChunkingPipeline] = None
        self.retrieval_stage: Optional[RetrievalStage] = None
        self.reranking_stage: Optional[RerankingStage] = None
        self.generation_stage: Optional[GenerationStage] = None

        # Initialize the pipeline components based on the configuration
        self._initialize_components()

    def _initialize_components(self):
        """Initialize pipeline components based on configuration."""
        # Initialize traditional pipeline components
        stages = self.config.stages

        if PipelineStage.TRANSFORM in stages:
            # Create transformation pipeline with transformers
            # Note: The DocumentTransformationPipeline doesn't take a config parameter directly
            self.transform_pipeline = DocumentTransformationPipeline(
                transformers=None  # Use default transformers
            )
            logger.debug("Initialized transformation pipeline")

        if PipelineStage.METADATA in stages:
            # Create metadata pipeline with extractors
            # Note: The MetadataEnrichmentPipeline doesn't take a config parameter directly
            self.metadata_pipeline = MetadataEnrichmentPipeline(
                extractors=None  # Use default extractors
            )
            logger.debug("Initialized metadata pipeline")

        if PipelineStage.CHUNK in stages:
            chunking_config = self.config.chunking_config or ChunkingConfig()
            # Convert our ChunkingConfig to the old ChunkingConfig format
            # Create a new ChunkingConfigOld instance with appropriate parameters
            old_config = ChunkingConfigOld()

            # Manually set attributes instead of using constructor parameters
            old_config.strategy = ChunkingStrategyOld(chunking_config.strategy.value)
            old_config.chunk_size = chunking_config.chunk_size
            old_config.chunk_overlap = chunking_config.chunk_overlap
            old_config.separator = chunking_config.separator
            old_config.keep_separator = chunking_config.keep_separator
            old_config.respect_sentence_boundaries = (
                chunking_config.respect_sentence_boundaries
            )
            old_config.respect_paragraph_boundaries = (
                chunking_config.respect_paragraph_boundaries
            )
            old_config.min_chunk_size = chunking_config.min_chunk_size
            old_config.max_chunk_size = chunking_config.max_chunk_size

            self.chunking_pipeline = ChunkingPipeline(
                strategies=[(old_config.strategy, old_config)]
            )
            logger.debug("Initialized chunking pipeline")

        # Initialize advanced pipeline components if configs are provided
        if self.config.retrieval_config:
            # Note: actual retrieval_stage initialization requires
            # embedding_provider and document_store which should be provided later
            logger.debug("Retrieval stage config prepared")

        if self.config.reranking_config:
            # Note: actual reranking_stage initialization requires
            # reranker_provider which should be provided later
            logger.debug("Reranking stage config prepared")

        if self.config.generation_config:
            # Note: actual generation_stage initialization requires
            # generation_provider which should be provided later
            logger.debug("Generation stage config prepared")

    def process(self, document: Document) -> List[Document]:
        """Process a document through the traditional RAG pipeline.

        This method processes a document through the transformation, metadata
        extraction, and chunking stages of the pipeline.

        Args:
            document: The document to process

        Returns:
            List of processed document chunks

        Raises:
            PepperpyError: If processing fails
        """
        try:
            # Using info instead of span for telemetry
            telemetry.info(
                "rag_pipeline_process",
                "Processing document through RAG pipeline",
                {"document_id": document.id},
            )

            # Convert Document to CommonDocument for pipeline processing
            # We need to convert the metadata to a dict
            metadata_dict = {}
            if document.metadata:
                metadata_dict = document.metadata.to_dict()

            # Create a CommonDocument with the appropriate metadata
            # We need to determine what type of metadata CommonDocument expects
            common_doc = None

            # Try to create a CommonDocument with different metadata approaches
            try:
                # First try: Convert our Metadata to CommonMetadata
                common_metadata = CommonMetadata()

                # Copy metadata fields from document.metadata to common_metadata
                if document.metadata:
                    if document.metadata.source:
                        common_metadata.source = document.metadata.source
                    if document.metadata.title:
                        common_metadata.title = document.metadata.title
                    if document.metadata.author:
                        common_metadata.author = document.metadata.author
                    if document.metadata.created_at:
                        common_metadata.created_at = document.metadata.created_at
                    # Copy custom fields
                    for key, value in document.metadata.custom.items():
                        common_metadata.custom[key] = value
                    # Copy tags from document.metadata to common_metadata
                    if hasattr(common_metadata, "tags") and document.metadata.tags:
                        # Handle tags based on the type of common_metadata.tags
                        if hasattr(common_metadata.tags, "clear"):
                            # Clear existing tags first if the method exists
                            common_metadata.tags.clear()

                        # Add each tag individually
                        for tag in document.metadata.tags:
                            if isinstance(common_metadata.tags, list):
                                if tag not in common_metadata.tags:
                                    common_metadata.tags.append(tag)
                            elif hasattr(common_metadata.tags, "add"):
                                common_metadata.tags.add(tag)

                common_doc = CommonDocument(
                    id=document.id,
                    content=document.content,
                    metadata=common_metadata,
                )
            except Exception as e:
                logger.warning(
                    f"Failed to create CommonDocument with converted metadata: {e}"
                )
                # Second try: Create with minimal metadata
                try:
                    common_doc = CommonDocument(
                        id=document.id,
                        content=document.content,
                    )
                    # Add metadata after creation if possible
                    if document.metadata:
                        common_doc.metadata.custom = document.metadata.custom.copy()
                except Exception as e2:
                    logger.warning(
                        f"Failed to create CommonDocument with minimal metadata: {e2}"
                    )
                    # Last resort: Create without metadata
                    common_doc = CommonDocument(
                        id=document.id,
                        content=document.content,
                    )

            if common_doc is None:
                # If all approaches failed, create a minimal document
                common_doc = CommonDocument(
                    id=document.id,
                    content=document.content,
                )
                logger.warning("Failed to create CommonDocument with metadata")

            result: List[CommonDocument] = [common_doc]
            stages = self.config.stages

            # Apply transformations if enabled
            if PipelineStage.TRANSFORM in stages and self.transform_pipeline:
                telemetry.info(
                    "rag_pipeline_transform_stage",
                    "Applying transformation stage",
                    {"document_id": document.id},
                )
                # Process the document and get a list of transformed documents
                transformed_doc = self.transform_pipeline.process(common_doc)
                if transformed_doc:
                    result = [transformed_doc]
                logger.debug(f"Transformation produced {len(result)} documents")

            # Apply metadata extraction if enabled
            if PipelineStage.METADATA in stages and self.metadata_pipeline:
                telemetry.info(
                    "rag_pipeline_metadata_stage",
                    "Applying metadata extraction stage",
                    {"document_id": document.id},
                )
                # Process each document to extract metadata
                processed_docs = []
                for doc in result:
                    processed_doc = self.metadata_pipeline.process(doc)
                    if processed_doc:
                        processed_docs.append(processed_doc)
                if processed_docs:
                    result = processed_docs
                logger.debug(f"Metadata extraction processed {len(result)} documents")

            # Apply chunking if enabled
            if PipelineStage.CHUNK in stages and self.chunking_pipeline:
                telemetry.info(
                    "rag_pipeline_chunk_stage",
                    "Applying chunking stage",
                    {"document_id": document.id},
                )
                chunked_docs = []
                for doc in result:
                    chunks = self.chunking_pipeline.process(doc)
                    if chunks:
                        chunked_docs.extend(chunks)
                if chunked_docs:
                    result = chunked_docs
                logger.debug(f"Chunking produced {len(result)} document chunks")

            telemetry.info(
                "rag_pipeline_completed",
                f"RAG pipeline completed, produced {len(result)} documents",
                {"document_id": document.id, "result_count": len(result)},
            )

            # Convert CommonDocument back to Document
            final_result = []
            for doc in result:
                # Convert metadata dict to Metadata object
                metadata_obj = Metadata()  # Default empty metadata
                if doc.metadata:
                    # Ensure we're passing a dict to from_dict
                    metadata_dict = {}
                    if isinstance(doc.metadata, dict):
                        metadata_dict = doc.metadata
                    elif hasattr(doc.metadata, "to_dict"):
                        metadata_dict = doc.metadata.to_dict()

                    # Create a new Metadata object from the dict
                    metadata_obj = Metadata.from_dict(metadata_dict)

                final_result.append(
                    Document(
                        id=doc.id,
                        content=doc.content,
                        metadata=metadata_obj,
                    )
                )

            return final_result
        except Exception as e:
            error_msg = f"Error processing document: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise PepperpyError(error_msg) from e

    def batch_process(self, documents: List[Document]) -> List[Document]:
        """Process multiple documents through the traditional RAG pipeline.

        Args:
            documents: The documents to process

        Returns:
            List of processed document chunks

        Raises:
            PepperpyError: If processing fails
        """
        try:
            telemetry.info(
                "rag_batch_pipeline_started",
                f"Processing {len(documents)} documents through RAG pipeline",
                {"document_count": len(documents)},
            )

            result = []
            for doc in documents:
                processed = self.process(doc)
                result.extend(processed)

            telemetry.info(
                "rag_batch_pipeline_completed",
                f"RAG batch pipeline completed, produced {len(result)} documents",
                {"input_count": len(documents), "output_count": len(result)},
            )

            return result
        except Exception as e:
            error_msg = f"Error batch processing documents: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise PepperpyError(error_msg) from e

    async def execute(
        self, query: str, context: Optional[Dict[str, Any]] = None, **kwargs: Any
    ) -> Dict[str, Any]:
        """Process a query through the advanced RAG pipeline stages.

        This method executes the retrieval, reranking, and generation stages
        of the RAG pipeline to generate a response for the given query.

        Args:
            query: The query to process
            context: Optional context information
            **kwargs: Additional arguments for pipeline stages

        Returns:
            Dictionary with the pipeline results, including:
            - retrieved_documents: Documents retrieved from the retrieval stage
            - reranked_documents: Documents after reranking
            - response: Generated response

        Raises:
            PipelineError: If any stage fails
        """
        result: Dict[str, Any] = {
            "query": query,
            "context": context or {},
        }

        try:
            # Retrieval stage
            if self.retrieval_stage:
                logger.debug(f"Running retrieval stage for query: {query}")
                retrieval_result = self.retrieval_stage.process(query)
                result["retrieved_documents"] = retrieval_result.documents

            # Reranking stage
            if self.reranking_stage and "retrieved_documents" in result:
                logger.debug(f"Running reranking stage for query: {query}")
                reranking_result = self.reranking_stage.process(
                    RetrievalResult(
                        documents=result["retrieved_documents"], query=query
                    )
                )
                result["reranked_documents"] = reranking_result.documents

            # Generation stage
            if self.generation_stage:
                logger.debug(f"Running generation stage for query: {query}")
                # Use reranked documents if available, otherwise use retrieved documents
                documents = result.get(
                    "reranked_documents", result.get("retrieved_documents", [])
                )
                generation_result = self.generation_stage.process(
                    RerankingResult(documents=documents, query=query)
                )
                result["response"] = generation_result.response

            return result
        except Exception as e:
            logger.error(f"Pipeline error: {str(e)}", exc_info=True)
            raise PepperpyError(f"Pipeline processing failed: {str(e)}") from e

    def set_retrieval_stage(
        self,
        embedding_provider: EmbeddingProvider,
        document_store: Any,
        config: Optional[RetrievalStageConfig] = None,
    ):
        """Set the retrieval stage for the pipeline.

        Args:
            embedding_provider: The embedding provider.
            document_store: The document store.
            config: Optional stage configuration.
        """
        self.retrieval_stage = RetrievalStage(
            embedding_provider=embedding_provider,
            document_store=document_store,
            config=config or self.config.retrieval_config,
        )
        logger.debug("Set retrieval stage for RAG pipeline")

    def set_reranking_stage(
        self,
        reranker_provider: RerankerProvider,
        config: Optional[RerankingStageConfig] = None,
    ):
        """Set the reranking stage for the pipeline.

        Args:
            reranker_provider: The reranker provider.
            config: Optional stage configuration.
        """
        self.reranking_stage = RerankingStage(
            reranker_provider=reranker_provider,
            config=config or self.config.reranking_config,
        )
        logger.debug("Set reranking stage for RAG pipeline")

    def set_generation_stage(
        self,
        generation_provider: GenerationProvider,
        config: Optional[GenerationStageConfig] = None,
    ):
        """Set the generation stage for the pipeline.

        Args:
            generation_provider: The generation provider.
            config: Optional stage configuration.
        """
        self.generation_stage = GenerationStage(
            generation_provider=generation_provider,
            config=config or self.config.generation_config,
        )
        logger.debug("Set generation stage for RAG pipeline")


class RAGPipelineBuilder:
    """Builder for RAG pipeline instances.

    This class provides a fluent interface for building RAG pipeline instances
    with custom configuration.
    """

    def __init__(self):
        """Initialize the builder."""
        self.config = PipelineConfig()

    def with_transformations(
        self,
        include_types: Optional[List[str]] = None,
        exclude_types: Optional[List[str]] = None,
        preserve_original: bool = True,
    ) -> "RAGPipelineBuilder":
        """Configure the document transformation stage.

        Args:
            include_types: Types of transformations to apply.
            exclude_types: Types of transformations to exclude.
            preserve_original: Whether to preserve the original content.

        Returns:
            The builder for chaining.
        """
        # Convert string types to TransformationType enum values if provided
        include_enum_types = None
        if include_types:
            include_enum_types = [TransformationType(t) for t in include_types]

        exclude_enum_types = None
        if exclude_types:
            exclude_enum_types = [TransformationType(t) for t in exclude_types]

        self.config.transformation_config = TransformationConfig(
            include_types=include_enum_types,
            exclude_types=exclude_enum_types,
            preserve_original=preserve_original,
        )

        if PipelineStage.TRANSFORM not in self.config.stages:
            self.config.stages.append(PipelineStage.TRANSFORM)

        return self

    def with_metadata_extraction(
        self,
        include_types: Optional[List[str]] = None,
        exclude_types: Optional[List[str]] = None,
        confidence_threshold: float = 0.5,
    ) -> "RAGPipelineBuilder":
        """Configure the metadata extraction stage.

        Args:
            include_types: Types of metadata to extract.
            exclude_types: Types of metadata to exclude.
            confidence_threshold: Minimum confidence for extracted metadata.

        Returns:
            The builder for chaining.
        """
        # Convert string types to MetadataType enum values if provided
        include_enum_types = None
        if include_types:
            include_enum_types = [MetadataType(t) for t in include_types]

        exclude_enum_types = None
        if exclude_types:
            exclude_enum_types = [MetadataType(t) for t in exclude_types]

        self.config.metadata_config = MetadataExtractorConfig(
            include_types=include_enum_types,
            exclude_types=exclude_enum_types,
            confidence_threshold=confidence_threshold,
        )

        if PipelineStage.METADATA not in self.config.stages:
            self.config.stages.append(PipelineStage.METADATA)

        return self

    def with_chunking(
        self,
        strategy: ChunkingStrategy = ChunkingStrategy.FIXED_SIZE,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        respect_boundaries: bool = True,
    ) -> "RAGPipelineBuilder":
        """Configure the chunking stage.

        Args:
            strategy: Chunking strategy to use.
            chunk_size: Size of each chunk.
            chunk_overlap: Overlap between chunks.
            respect_boundaries: Whether to respect document boundaries.

        Returns:
            The builder for chaining.
        """
        self.config.chunking_config = ChunkingConfig(
            strategy=strategy,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            respect_sentence_boundaries=respect_boundaries,
            respect_paragraph_boundaries=respect_boundaries,
        )

        if PipelineStage.CHUNK not in self.config.stages:
            self.config.stages.append(PipelineStage.CHUNK)

        return self

    def with_retrieval(
        self,
        top_k: int = 5,
    ) -> "RAGPipelineBuilder":
        """Configure the retrieval stage.

        Args:
            top_k: Number of documents to retrieve.

        Returns:
            The builder for chaining.
        """
        self.config.retrieval_config = RetrievalStageConfig(
            name="retrieval",
            type="retrieval",
            top_k=top_k,
        )

        if PipelineStage.RETRIEVE not in self.config.stages:
            self.config.stages.append(PipelineStage.RETRIEVE)

        return self

    def with_reranking(
        self,
        top_k: int = 3,
    ) -> "RAGPipelineBuilder":
        """Configure the reranking stage.

        Args:
            top_k: Number of documents to keep after reranking.

        Returns:
            The builder for chaining.
        """
        self.config.reranking_config = RerankingStageConfig(
            name="reranking",
            type="reranking",
            top_k=top_k,
        )

        if PipelineStage.RERANK not in self.config.stages:
            self.config.stages.append(PipelineStage.RERANK)

        return self

    def with_generation(
        self,
        prompt_template: str = "Baseado nos seguintes documentos, responda a pergunta:\n\nDocumentos: {documents}\n\nPergunta: {query}\n\nResposta:",
        document_separator: str = "\n---\n",
    ) -> "RAGPipelineBuilder":
        """Configure the generation stage.

        Args:
            prompt_template: Template for the generation prompt.
            document_separator: Separator between documents in the prompt.

        Returns:
            The builder for chaining.
        """
        self.config.generation_config = GenerationStageConfig(
            name="generation",
            type="generation",
            prompt_template=prompt_template,
            document_separator=document_separator,
        )

        if PipelineStage.GENERATE not in self.config.stages:
            self.config.stages.append(PipelineStage.GENERATE)

        return self

    def with_param(self, key: str, value: Any) -> "RAGPipelineBuilder":
        """Add a custom parameter to the pipeline configuration.

        Args:
            key: Parameter key.
            value: Parameter value.

        Returns:
            The builder for chaining.
        """
        self.config.params[key] = value
        return self

    def build(self) -> RAGPipeline:
        """Build the RAG pipeline instance.

        Returns:
            Configured RAG pipeline instance.
        """
        return RAGPipeline(config=self.config)


def create_default_pipeline() -> RAGPipeline:
    """Create a default RAG pipeline.

    Returns:
        Default RAG pipeline instance.
    """
    return (
        RAGPipelineBuilder()
        .with_transformations()
        .with_metadata_extraction()
        .with_chunking()
        .build()
    )


def create_simple_pipeline() -> RAGPipeline:
    """Create a simple RAG pipeline with minimal processing.

    Returns:
        Simple RAG pipeline instance.
    """
    return (
        RAGPipelineBuilder()
        .with_chunking(
            strategy=ChunkingStrategy.FIXED_SIZE, chunk_size=1000, chunk_overlap=0
        )
        .build()
    )


def create_metadata_focused_pipeline() -> RAGPipeline:
    """Create a metadata-focused RAG pipeline.

    Returns:
        Metadata-focused RAG pipeline instance.
    """
    # Use string literals for transformation types instead of enum values
    return (
        RAGPipelineBuilder()
        .with_transformations(include_types=["text_extraction", "html_extraction"])
        .with_metadata_extraction(confidence_threshold=0.3)
        .with_chunking(respect_boundaries=True)
        .build()
    )


def process_document(
    document: Document, pipeline: Optional[RAGPipeline] = None
) -> List[Document]:
    """Process a document through a RAG pipeline.

    Args:
        document: Document to process.
        pipeline: Optional pipeline to use.

    Returns:
        Processed document chunks.
    """
    # Create default pipeline if none provided
    if pipeline is None:
        pipeline = create_default_pipeline()

    # Process the document
    return pipeline.process(document)


def process_documents(
    documents: List[Document], pipeline: Optional[RAGPipeline] = None
) -> List[Document]:
    """Process multiple documents through a RAG pipeline.

    Args:
        documents: Documents to process.
        pipeline: Optional pipeline to use.

    Returns:
        Processed document chunks.
    """
    # Create default pipeline if none provided
    if pipeline is None:
        pipeline = create_default_pipeline()

    # Process the documents
    return pipeline.batch_process(documents)
