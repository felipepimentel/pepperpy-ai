"""Core functionality for RAG pipelines.

This module provides the core functionality for RAG pipelines,
including pipeline stages, pipeline execution, and query processing.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union

from pepperpy.rag.errors import PipelineError, PipelineStageError
from pepperpy.rag.storage.core import ScoredChunk
from pepperpy.utils.logging import get_logger

# Logger for this module
logger = get_logger(__name__)


@dataclass
class Query:
    """A query for RAG.

    Attributes:
        text: The text of the query
        metadata: Additional metadata for the query
    """

    text: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class QueryResult:
    """A result for a RAG query.

    Attributes:
        query: The query that produced this result
        chunks: The document chunks that were retrieved
        answer: The generated answer
        metadata: Additional metadata for the result
    """

    query: Query
    chunks: List[ScoredChunk]
    answer: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class PipelineStage(ABC):
    """Base class for pipeline stages.

    Pipeline stages are responsible for processing queries and results in a RAG
    pipeline, such as query expansion, retrieval, reranking, or generation.
    """

    @abstractmethod
    async def process(self, query: Query, context: Dict[str, Any]) -> Dict[str, Any]:
        """Process a query and context.

        Args:
            query: The query to process
            context: The context to process

        Returns:
            The updated context

        Raises:
            PipelineStageError: If there is an error processing the query
        """
        pass


class QueryExpansionStage(PipelineStage):
    """Base class for query expansion stages.

    Query expansion stages are responsible for expanding queries to improve
    retrieval, such as by adding synonyms, related terms, or context.
    """

    @abstractmethod
    async def expand_query(self, query: Query) -> List[Query]:
        """Expand a query.

        Args:
            query: The query to expand

        Returns:
            The expanded queries

        Raises:
            PipelineStageError: If there is an error expanding the query
        """
        pass

    async def process(self, query: Query, context: Dict[str, Any]) -> Dict[str, Any]:
        """Process a query and context.

        Args:
            query: The query to process
            context: The context to process

        Returns:
            The updated context

        Raises:
            PipelineStageError: If there is an error processing the query
        """
        try:
            # Expand the query
            expanded_queries = await self.expand_query(query)

            # Update the context
            context["expanded_queries"] = expanded_queries

            return context
        except Exception as e:
            raise PipelineStageError(
                f"Error expanding query: {e}",
                stage_name=self.__class__.__name__,
            )


class RetrievalStage(PipelineStage):
    """Base class for retrieval stages.

    Retrieval stages are responsible for retrieving document chunks for a query,
    such as by using vector search, keyword search, or hybrid search.
    """

    @abstractmethod
    async def retrieve(self, query: Query, limit: int = 10) -> List[ScoredChunk]:
        """Retrieve document chunks for a query.

        Args:
            query: The query to retrieve document chunks for
            limit: The maximum number of document chunks to retrieve

        Returns:
            The retrieved document chunks

        Raises:
            PipelineStageError: If there is an error retrieving document chunks
        """
        pass

    async def process(self, query: Query, context: Dict[str, Any]) -> Dict[str, Any]:
        """Process a query and context.

        Args:
            query: The query to process
            context: The context to process

        Returns:
            The updated context

        Raises:
            PipelineStageError: If there is an error processing the query
        """
        try:
            # Get the limit from the context or use the default
            limit = context.get("limit", 10)

            # Check if there are expanded queries
            expanded_queries = context.get("expanded_queries", [])

            if expanded_queries:
                # Retrieve document chunks for each expanded query
                all_chunks: List[ScoredChunk] = []

                for expanded_query in expanded_queries:
                    chunks = await self.retrieve(expanded_query, limit)
                    all_chunks.extend(chunks)

                # Deduplicate chunks by ID
                seen_ids = set()
                unique_chunks = []

                for chunk in all_chunks:
                    if chunk.chunk.id not in seen_ids:
                        seen_ids.add(chunk.chunk.id)
                        unique_chunks.append(chunk)

                # Sort by score
                unique_chunks.sort(key=lambda x: x.score, reverse=True)

                # Limit the number of chunks
                chunks = unique_chunks[:limit]
            else:
                # Retrieve document chunks for the original query
                chunks = await self.retrieve(query, limit)

            # Update the context
            context["chunks"] = chunks

            return context
        except Exception as e:
            raise PipelineStageError(
                f"Error retrieving document chunks: {e}",
                stage_name=self.__class__.__name__,
            )


class RerankingStage(PipelineStage):
    """Base class for reranking stages.

    Reranking stages are responsible for reranking document chunks for a query,
    such as by using a more sophisticated relevance model or cross-encoder.
    """

    @abstractmethod
    async def rerank(
        self, query: Query, chunks: List[ScoredChunk], limit: int = 10
    ) -> List[ScoredChunk]:
        """Rerank document chunks for a query.

        Args:
            query: The query to rerank document chunks for
            chunks: The document chunks to rerank
            limit: The maximum number of document chunks to return

        Returns:
            The reranked document chunks

        Raises:
            PipelineStageError: If there is an error reranking document chunks
        """
        pass

    async def process(self, query: Query, context: Dict[str, Any]) -> Dict[str, Any]:
        """Process a query and context.

        Args:
            query: The query to process
            context: The context to process

        Returns:
            The updated context

        Raises:
            PipelineStageError: If there is an error processing the query
        """
        try:
            # Get the chunks from the context
            chunks = context.get("chunks", [])

            if not chunks:
                return context

            # Get the limit from the context or use the default
            limit = context.get("limit", 10)

            # Rerank the chunks
            reranked_chunks = await self.rerank(query, chunks, limit)

            # Update the context
            context["chunks"] = reranked_chunks

            return context
        except Exception as e:
            raise PipelineStageError(
                f"Error reranking document chunks: {e}",
                stage_name=self.__class__.__name__,
            )


class GenerationStage(PipelineStage):
    """Base class for generation stages.

    Generation stages are responsible for generating answers for a query and
    retrieved document chunks, such as by using a language model.
    """

    @abstractmethod
    async def generate(self, query: Query, chunks: List[ScoredChunk]) -> str:
        """Generate an answer for a query and retrieved document chunks.

        Args:
            query: The query to generate an answer for
            chunks: The retrieved document chunks

        Returns:
            The generated answer

        Raises:
            PipelineStageError: If there is an error generating an answer
        """
        pass

    async def process(self, query: Query, context: Dict[str, Any]) -> Dict[str, Any]:
        """Process a query and context.

        Args:
            query: The query to process
            context: The context to process

        Returns:
            The updated context

        Raises:
            PipelineStageError: If there is an error processing the query
        """
        try:
            # Get the chunks from the context
            chunks = context.get("chunks", [])

            if not chunks:
                # No chunks, so no answer
                context["answer"] = None
                return context

            # Generate an answer
            answer = await self.generate(query, chunks)

            # Update the context
            context["answer"] = answer

            return context
        except Exception as e:
            raise PipelineStageError(
                f"Error generating answer: {e}",
                stage_name=self.__class__.__name__,
            )


class Pipeline:
    """A pipeline for RAG.

    A pipeline consists of a sequence of stages that process a query and context,
    such as query expansion, retrieval, reranking, and generation.
    """

    def __init__(self, stages: List[PipelineStage] = None):
        """Initialize a pipeline.

        Args:
            stages: The stages of the pipeline
        """
        self.stages = stages or []

    def add_stage(self, stage: PipelineStage) -> None:
        """Add a stage to the pipeline.

        Args:
            stage: The stage to add
        """
        self.stages.append(stage)

    async def run(
        self, query: Query, context: Optional[Dict[str, Any]] = None
    ) -> QueryResult:
        """Run the pipeline.

        Args:
            query: The query to run the pipeline on
            context: The initial context, or None to use an empty context

        Returns:
            The query result

        Raises:
            PipelineError: If there is an error running the pipeline
        """
        # Initialize the context
        context = context or {}

        try:
            # Run each stage
            for stage in self.stages:
                context = await stage.process(query, context)

            # Create the query result
            return QueryResult(
                query=query,
                chunks=context.get("chunks", []),
                answer=context.get("answer"),
                metadata=context,
            )
        except PipelineStageError as e:
            # Re-raise pipeline stage errors
            raise PipelineError(f"Error in pipeline stage: {e}")
        except Exception as e:
            # Wrap other errors
            raise PipelineError(f"Error running pipeline: {e}")


class PipelineManager:
    """Manager for RAG pipelines.

    The pipeline manager provides a unified interface for working with different
    RAG pipelines.
    """

    def __init__(self):
        """Initialize the pipeline manager."""
        self._pipelines: Dict[str, Pipeline] = {}
        self._default_pipeline: Optional[str] = None

    def register_pipeline(
        self, name: str, pipeline: Pipeline, default: bool = False
    ) -> None:
        """Register a pipeline.

        Args:
            name: The name of the pipeline
            pipeline: The pipeline to register
            default: Whether to set this pipeline as the default

        Raises:
            PipelineError: If a pipeline with the same name is already registered
        """
        if name in self._pipelines:
            raise PipelineError(f"Pipeline '{name}' is already registered")

        self._pipelines[name] = pipeline

        if default or self._default_pipeline is None:
            self._default_pipeline = name

    def unregister_pipeline(self, name: str) -> None:
        """Unregister a pipeline.

        Args:
            name: The name of the pipeline to unregister

        Raises:
            PipelineError: If the pipeline is not registered
        """
        if name not in self._pipelines:
            raise PipelineError(f"Pipeline '{name}' is not registered")

        del self._pipelines[name]

        if self._default_pipeline == name:
            self._default_pipeline = (
                next(iter(self._pipelines)) if self._pipelines else None
            )

    def get_pipeline(self, name: Optional[str] = None) -> Pipeline:
        """Get a pipeline.

        Args:
            name: The name of the pipeline to get, or None to get the default pipeline

        Returns:
            The pipeline

        Raises:
            PipelineError: If the pipeline is not registered or no default pipeline is set
        """
        if name is None:
            if self._default_pipeline is None:
                raise PipelineError("No default pipeline is set")

            name = self._default_pipeline

        if name not in self._pipelines:
            raise PipelineError(f"Pipeline '{name}' is not registered")

        return self._pipelines[name]

    def set_default_pipeline(self, name: str) -> None:
        """Set the default pipeline.

        Args:
            name: The name of the pipeline to set as the default

        Raises:
            PipelineError: If the pipeline is not registered
        """
        if name not in self._pipelines:
            raise PipelineError(f"Pipeline '{name}' is not registered")

        self._default_pipeline = name

    def get_default_pipeline(self) -> Optional[str]:
        """Get the name of the default pipeline.

        Returns:
            The name of the default pipeline, or None if no default pipeline is set
        """
        return self._default_pipeline

    def get_pipelines(self) -> Dict[str, Pipeline]:
        """Get all registered pipelines.

        Returns:
            A dictionary of pipeline names to pipelines
        """
        return self._pipelines.copy()

    async def run(
        self,
        query: Union[str, Query],
        pipeline: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> QueryResult:
        """Run a pipeline.

        Args:
            query: The query to run the pipeline on
            pipeline: The name of the pipeline to run, or None to use the default pipeline
            context: The initial context, or None to use an empty context

        Returns:
            The query result

        Raises:
            PipelineError: If there is an error running the pipeline
        """
        # Convert the query to a Query object if it's a string
        if isinstance(query, str):
            query = Query(text=query)

        # Get the pipeline
        pipeline_obj = self.get_pipeline(pipeline)

        # Run the pipeline
        return await pipeline_obj.run(query, context)


# Global pipeline manager
_pipeline_manager = PipelineManager()


def get_pipeline_manager() -> PipelineManager:
    """Get the global pipeline manager.

    Returns:
        The global pipeline manager
    """
    return _pipeline_manager
