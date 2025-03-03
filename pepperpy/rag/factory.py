"""Factory for creating RAG pipelines.

This module provides a factory for creating RAG pipelines from configuration.
"""

from pepperpy.core.logging import get_logger
from pepperpy.rag.base import RagPipeline
from pepperpy.rag.generation import GenerationManager
from pepperpy.rag.generation.providers import get_generation_provider
from pepperpy.rag.indexing import IndexingManager
from pepperpy.rag.indexing.providers import get_indexing_provider
from pepperpy.rag.registry import rag_registry
from pepperpy.rag.retrieval import RetrievalManager
from pepperpy.rag.retrieval.providers import get_retrieval_provider
from pepperpy.rag.types import RagConfig

logger = get_logger(__name__)


class RagPipelineFactory:
    """Factory for creating RAG pipelines."""

    @staticmethod
    def create_pipeline(config: RagConfig) -> RagPipeline:
        """Create a RAG pipeline from configuration.

        Args:
            config: The configuration for the pipeline

        Returns:
            The created pipeline

        """
        logger.info(f"Creating RAG pipeline: {config.name}")

        # Create the pipeline
        pipeline = RagPipeline(
            component_id=config.id,
            name=config.name,
            description=config.description,
        )

        # Create and add the indexing manager
        indexing_manager = RagPipelineFactory._create_indexing_manager(config)
        pipeline.add_component(indexing_manager)

        # Create and add the retrieval manager
        retrieval_manager = RagPipelineFactory._create_retrieval_manager(config)
        pipeline.add_component(retrieval_manager)

        # Create and add the generation manager
        generation_manager = RagPipelineFactory._create_generation_manager(config)
        pipeline.add_component(generation_manager)

        # Register the pipeline
        rag_registry.register(pipeline)

        return pipeline

    @staticmethod
    def _create_indexing_manager(config: RagConfig) -> IndexingManager:
        """Create an indexing manager from configuration.

        Args:
            config: The configuration for the pipeline

        Returns:
            The created indexing manager

        """
        logger.debug("Creating indexing manager")

        indexing_manager = IndexingManager(
            component_id=f"{config.id}_indexing_manager",
            name=f"{config.name} Indexing Manager",
            description="Manager for indexing operations",
        )

        # Add indexers from configuration
        for indexer_config in config.indexers:
            indexer_id = indexer_config.get("id")
            if not indexer_id:
                logger.warning("Skipping indexer with no ID")
                continue

            try:
                indexer = get_indexing_provider(indexer_id)
                indexing_manager.add_indexer(indexer)
                logger.debug(f"Added indexer: {indexer_id}")
            except ValueError as e:
                logger.warning(f"Failed to add indexer {indexer_id}: {e}")

        # Register the indexing manager
        rag_registry.register(indexing_manager)

        return indexing_manager

    @staticmethod
    def _create_retrieval_manager(config: RagConfig) -> RetrievalManager:
        """Create a retrieval manager from configuration.

        Args:
            config: The configuration for the pipeline

        Returns:
            The created retrieval manager

        """
        logger.debug("Creating retrieval manager")

        retrieval_manager = RetrievalManager(
            component_id=f"{config.id}_retrieval_manager",
            name=f"{config.name} Retrieval Manager",
            description="Manager for retrieval operations",
        )

        # Add retrievers from configuration
        default_retriever = config.default_retriever

        for retriever_config in config.retrievers:
            retriever_id = retriever_config.get("id")
            if not retriever_id:
                logger.warning("Skipping retriever with no ID")
                continue

            try:
                retriever = get_retrieval_provider(retriever_id)
                set_as_default = retriever_id == default_retriever
                retrieval_manager.add_retriever(retriever, set_as_default)
                logger.debug(f"Added retriever: {retriever_id}")
            except ValueError as e:
                logger.warning(f"Failed to add retriever {retriever_id}: {e}")

        # Register the retrieval manager
        rag_registry.register(retrieval_manager)

        return retrieval_manager

    @staticmethod
    def _create_generation_manager(config: RagConfig) -> GenerationManager:
        """Create a generation manager from configuration.

        Args:
            config: The configuration for the pipeline

        Returns:
            The created generation manager

        """
        logger.debug("Creating generation manager")

        generation_manager = GenerationManager(
            component_id=f"{config.id}_generation_manager",
            name=f"{config.name} Generation Manager",
            description="Manager for generation operations",
        )

        # Add generators from configuration
        default_generator = config.default_generator

        for generator_config in config.generators:
            generator_id = generator_config.get("id")
            if not generator_id:
                logger.warning("Skipping generator with no ID")
                continue

            try:
                generator = get_generation_provider(generator_id)
                set_as_default = generator_id == default_generator
                generation_manager.add_generator(generator, set_as_default)
                logger.debug(f"Added generator: {generator_id}")
            except ValueError as e:
                logger.warning(f"Failed to add generator {generator_id}: {e}")

        # Register the generation manager
        rag_registry.register(generation_manager)

        return generation_manager
