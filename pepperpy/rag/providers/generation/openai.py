"""OpenAI generation provider implementation.

This module provides generation functionality using OpenAI's models.
"""

from typing import Any, List, Optional

from openai import AsyncOpenAI
from openai.types.chat import ChatCompletionMessageParam
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from pepperpy.rag.errors import GenerationError
from pepperpy.rag.providers.generation.base import BaseGenerationProvider
from pepperpy.utils.logging import get_logger

# Logger for this module
logger = get_logger(__name__)

# Default model for generation
DEFAULT_MODEL = "gpt-3.5-turbo"

# Default system message
DEFAULT_SYSTEM_MESSAGE = (
    "You are a helpful AI assistant. Your task is to answer questions "
    "accurately based on the provided context. If the context doesn't "
    "contain enough information to answer the question, say so."
)

# Retry configuration
MAX_RETRIES = 3
MIN_WAIT = 1
MAX_WAIT = 10


class OpenAIGenerationProvider(BaseGenerationProvider):
    """OpenAI generation provider.

    This provider uses OpenAI's models to generate responses.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: str = DEFAULT_MODEL,
        system_message: str = DEFAULT_SYSTEM_MESSAGE,
        default_prompt_template: Optional[str] = None,
    ):
        """Initialize OpenAI generation provider.

        Args:
            api_key: OpenAI API key (if None, uses environment variable)
            model_name: Name of the model to use
            system_message: System message for chat models
            default_prompt_template: Optional default template for prompts
        """
        super().__init__(
            model_name=model_name,
            default_prompt_template=default_prompt_template,
        )
        self.client = AsyncOpenAI(api_key=api_key)
        self.system_message = system_message

    @retry(
        retry=retry_if_exception_type(Exception),
        stop=stop_after_attempt(MAX_RETRIES),
        wait=wait_exponential(multiplier=MIN_WAIT, max=MAX_WAIT),
        reraise=True,
    )
    async def _generate_text(
        self,
        prompt: str,
        max_tokens: Optional[int] = None,
        temperature: float = 0.7,
        top_p: float = 0.9,
        **kwargs: Any,
    ) -> str:
        """Generate text using OpenAI's models.

        Args:
            prompt: The formatted prompt string
            max_tokens: Maximum number of tokens to generate
            temperature: Temperature for generation (0-1)
            top_p: Top-p sampling parameter (0-1)
            **kwargs: Additional model-specific arguments

        Returns:
            Generated text

        Raises:
            GenerationError: If there is an error during generation
        """
        try:
            # Prepare messages for chat models
            messages: List[ChatCompletionMessageParam] = [
                {"role": "system", "content": self.system_message},
                {"role": "user", "content": prompt},
            ]

            # Generate response
            response = await self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
                top_p=top_p,
                **kwargs,
            )

            # Extract generated text
            if not response.choices:
                raise GenerationError("No response generated")

            return response.choices[0].message.content or ""

        except Exception as e:
            raise GenerationError(f"Error generating text with OpenAI: {e}")
