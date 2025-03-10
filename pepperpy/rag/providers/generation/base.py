"""Base generation provider implementation.

This module provides the base class for generation providers.
"""

from abc import ABC, abstractmethod
from typing import Any, List, Optional

from pepperpy.rag.errors import GenerationError
from pepperpy.utils.logging import get_logger

# Logger for this module
logger = get_logger(__name__)


class BaseGenerationProvider(ABC):
    """Base class for generation providers.

    This class defines the interface that all generation providers must implement.
    """

    def __init__(
        self,
        model_name: Optional[str] = None,
        default_prompt_template: Optional[str] = None,
    ):
        """Initialize base generation provider.

        Args:
            model_name: Optional name of the model to use
            default_prompt_template: Optional default template for prompts
        """
        self.model_name = model_name
        self.default_prompt_template = default_prompt_template

    def _format_prompt(
        self,
        query: str,
        documents: List[str],
        prompt_template: Optional[str] = None,
    ) -> str:
        """Format prompt using template.

        Args:
            query: The query string
            documents: List of documents to use as context
            prompt_template: Optional template for generation prompt

        Returns:
            Formatted prompt string
        """
        template = (
            prompt_template
            or self.default_prompt_template
            or (
                "Answer the following question using the provided context.\n\n"
                "Context:\n{context}\n\n"
                "Question: {query}\n\n"
                "Answer:"
            )
        )

        # Format context by joining documents with newlines
        context = "\n\n".join(documents)

        return template.format(query=query, context=context)

    @abstractmethod
    async def _generate_text(
        self,
        prompt: str,
        **kwargs: Any,
    ) -> str:
        """Internal method to generate text.

        Args:
            prompt: The formatted prompt string
            **kwargs: Additional provider-specific arguments

        Returns:
            Generated text

        Raises:
            GenerationError: If there is an error during generation
        """
        ...

    async def generate(
        self,
        query: str,
        documents: List[str],
        prompt_template: Optional[str] = None,
        **kwargs: Any,
    ) -> str:
        """Generate a response based on query and documents.

        Args:
            query: The query string
            documents: List of documents to use as context
            prompt_template: Optional template for generation prompt
            **kwargs: Additional provider-specific arguments

        Returns:
            Generated response text

        Raises:
            GenerationError: If there is an error during generation
        """
        try:
            # Format prompt
            prompt = self._format_prompt(
                query=query,
                documents=documents,
                prompt_template=prompt_template,
            )

            # Generate response
            return await self._generate_text(prompt=prompt, **kwargs)

        except Exception as e:
            raise GenerationError(f"Error in generation: {e}")

    def __repr__(self) -> str:
        """Get string representation of provider.

        Returns:
            String representation
        """
        return f"{self.__class__.__name__}(model_name={self.model_name})"
