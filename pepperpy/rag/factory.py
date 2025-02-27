"""Factory for creating RAG pipelines."""

from typing import Dict, Optional, Type

from .base import (
    RagPipeline,
)
from .config import RagConfig
from .pipeline import StandardRagPipeline
from .registry import registry


class RagPipelineFactory:
    """Factory for creating RAG pipelines with different configurations."""

    @staticmethod
    def create_pipeline(
        config: RagConfig,
        pipeline_class: Optional[Type[RagPipeline]] = None,
        components: Optional[Dict[str, str]] = None,
    ) -> RagPipeline:
        """Create a RAG pipeline with the specified configuration.

        Args:
            config: Configuration for the pipeline
            pipeline_class: Optional custom pipeline class
            components: Optional mapping of component types to specific implementations

        Returns:
            Configured RAG pipeline instance
        """
        # Use default components if none specified
        components = components or {
            "chunker": "default",
            "embedder": "default",
            "indexer": "default",
            "retriever": "default",
            "augmenter": "default",
        }

        # Get component classes from registry
        chunker_class = registry.get_chunker(components["chunker"])
        embedder_class = registry.get_embedder(components["embedder"])
        indexer_class = registry.get_indexer(components["indexer"])
        retriever_class = registry.get_retriever(components["retriever"])
        augmenter_class = registry.get_augmenter(components["augmenter"])

        # Instantiate components with config
        chunker = chunker_class(config=config.chunking)
        embedder = embedder_class(config=config.embedding)
        indexer = indexer_class(config=config.indexing)
        retriever = retriever_class(
            config=config.retrieval, embedder=embedder, indexer=indexer
        )
        augmenter = augmenter_class(config=config.augmentation)

        # Create pipeline
        pipeline_class = pipeline_class or StandardRagPipeline
        pipeline = pipeline_class(
            chunker=chunker,
            embedder=embedder,
            indexer=indexer,
            retriever=retriever,
            augmenter=augmenter,
        )

        return pipeline

    @staticmethod
    def create_qa_pipeline(
        config: RagConfig,
        components: Optional[Dict[str, str]] = None,
    ) -> RagPipeline:
        """Create a pipeline optimized for question answering."""
        qa_components = {
            "chunker": "qa_chunker",
            "embedder": "qa_embedder",
            "indexer": "qa_indexer",
            "retriever": "qa_retriever",
            "augmenter": "qa_augmenter",
        }
        if components:
            qa_components.update(components)

        return RagPipelineFactory.create_pipeline(
            config=config,
            components=qa_components,
        )

    @staticmethod
    def create_summarization_pipeline(
        config: RagConfig,
        components: Optional[Dict[str, str]] = None,
    ) -> RagPipeline:
        """Create a pipeline optimized for summarization."""
        summary_components = {
            "chunker": "summary_chunker",
            "embedder": "default",
            "indexer": "default",
            "retriever": "standard",
            "augmenter": "template",
        }
        if components:
            summary_components.update(components)

        return RagPipelineFactory.create_pipeline(
            config=config,
            components=summary_components,
        )

    @staticmethod
    def create_knowledge_base_pipeline(
        config: RagConfig,
        components: Optional[Dict[str, str]] = None,
    ) -> RagPipeline:
        """Create a pipeline optimized for knowledge base access."""
        kb_components = {
            "chunker": "kb_chunker",
            "embedder": "kb_embedder",
            "indexer": "kb_indexer",
            "retriever": "kb_retriever",
            "augmenter": "kb_augmenter",
        }
        if components:
            kb_components.update(components)

        return RagPipelineFactory.create_pipeline(
            config=config,
            components=kb_components,
        )
