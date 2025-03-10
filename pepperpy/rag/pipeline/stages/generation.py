"""Generation stage implementation.

This module provides functionality for generating responses based on retrieved documents.
"""

from typing import Any, Dict, List, Optional, Union

from pepperpy.rag.errors import PipelineStageError
from pepperpy.rag.pipeline.base import BasePipelineStage
from pepperpy.rag.providers.generation.base import BaseGenerationProvider
from pepperpy.rag.storage.types import SearchResult

# Type alias for generation providers
GenerationProvider = BaseGenerationProvider


# Configuration for generation stage
class GenerationStageConfig:
    """Configuration for generation stage."""

    def __init__(
        self,
        max_input_tokens: Optional[int] = None,
        max_output_tokens: Optional[int] = None,
        temperature: float = 0.7,
        top_p: float = 0.9,
    ):
        """Initialize generation stage configuration.

        Args:
            max_input_tokens: Maximum number of input tokens to use.
            max_output_tokens: Maximum number of output tokens to generate.
            temperature: Sampling temperature (0-1, lower is more focused).
            top_p: Nucleus sampling parameter (0-1).
        """
        self.max_input_tokens = max_input_tokens
        self.max_output_tokens = max_output_tokens
        self.temperature = temperature
        self.top_p = top_p


class GenerationStage(BasePipelineStage):
    """Generation stage for producing responses.

    This stage takes a query and relevant documents to generate a response
    using a language model. The response is grounded in the provided documents
    to ensure accuracy and relevance.
    """

    def __init__(
        self,
        generation_provider: BaseGenerationProvider,
        max_input_tokens: Optional[int] = None,
        max_output_tokens: Optional[int] = None,
        temperature: float = 0.7,
        top_p: float = 0.9,
        **kwargs: Any,
    ) -> None:
        """Initialize the generation stage.

        Args:
            generation_provider: Provider for generating responses.
            max_input_tokens: Maximum number of input tokens to use.
            max_output_tokens: Maximum number of output tokens to generate.
            temperature: Sampling temperature (0-1, lower is more focused).
            top_p: Nucleus sampling parameter (0-1).
            **kwargs: Additional keyword arguments.
        """
        super().__init__(**kwargs)
        self.generation_provider = generation_provider
        self.max_input_tokens = max_input_tokens
        self.max_output_tokens = max_output_tokens
        self.temperature = temperature
        self.top_p = top_p

    def _format_context(
        self,
        documents: List[SearchResult],
        include_metadata: bool = False,
    ) -> str:
        """Format documents into a context string.

        Args:
            documents: List of search results to format.
            include_metadata: Whether to include document metadata.

        Returns:
            Formatted context string.
        """
        context_parts = []
        for i, result in enumerate(documents, 1):
            # Format document content
            content = "\n".join(chunk.content for chunk in result.document.chunks)

            # Add metadata if requested
            if include_metadata and result.document.metadata:
                metadata_str = "\n".join(
                    f"{k}: {v}" for k, v in result.document.metadata.items()
                )
                content = f"{metadata_str}\n\n{content}"

            # Add document to context with score
            context_parts.append(
                f"Document {i} (Score: {result.score:.3f}):\n{content}\n"
            )

        return "\n\n".join(context_parts)

    async def process(
        self,
        query: str,
        documents: Union[SearchResult, List[SearchResult]],
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Process a query and documents to generate a response.

        Args:
            query: Query text to respond to.
            documents: Document or list of documents to use as context.
            **kwargs: Additional arguments passed to the generation provider.

        Returns:
            Dictionary containing the generated response and metadata.

        Raises:
            PipelineStageError: If generation fails.
        """
        try:
            # Convert single document to list
            if isinstance(documents, SearchResult):
                documents = [documents]

            # Format context from documents
            include_metadata = kwargs.pop("include_metadata", False)
            context = self._format_context(documents, include_metadata)

            # Generate response
            response = await self.generation_provider.generate(
                query=query,
                context=context,
                max_input_tokens=kwargs.pop("max_input_tokens", self.max_input_tokens),
                max_output_tokens=kwargs.pop(
                    "max_output_tokens", self.max_output_tokens
                ),
                temperature=kwargs.pop("temperature", self.temperature),
                top_p=kwargs.pop("top_p", self.top_p),
                **kwargs,
            )

            # Return response with metadata
            return {
                "response": response.text,
                "usage": response.usage,
                "metadata": {
                    "model": response.model,
                    "finish_reason": response.finish_reason,
                    "num_documents": len(documents),
                    "document_scores": [result.score for result in documents],
                },
            }

        except Exception as e:
            raise PipelineStageError(f"Error generating response: {str(e)}") from e
