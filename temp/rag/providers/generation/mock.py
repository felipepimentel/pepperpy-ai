"""Mock generation provider implementation.

This module provides a mock generation provider for testing purposes.
"""

import hashlib
from typing import Any, Optional

from pepperpy.rag.errors import GenerationError
from pepperpy.rag.providers.generation.base import BaseGenerationProvider
from pepperpy.utils.logging import get_logger

# Logger for this module
logger = get_logger(__name__)


class MockGenerationProvider(BaseGenerationProvider):
    """Mock generation provider for testing.

    This provider generates deterministic responses based on input hashing.
    """

    def __init__(
        self,
        model_name: Optional[str] = None,
        default_prompt_template: Optional[str] = None,
    ):
        """Initialize mock generation provider.

        Args:
            model_name: Optional name for the mock model
            default_prompt_template: Optional default template for prompts
        """
        super().__init__(
            model_name=model_name or "mock-generator",
            default_prompt_template=default_prompt_template,
        )

    def _text_to_hash(self, text: str) -> int:
        """Convert text to a deterministic hash value.

        Args:
            text: Input text

        Returns:
            Hash value
        """
        # Get hash of text
        text_hash = hashlib.sha256(text.encode()).hexdigest()
        # Convert first 8 bytes to integer
        return int(text_hash[:16], 16)

    def _generate_deterministic_response(
        self,
        prompt: str,
        max_tokens: Optional[int] = None,
    ) -> str:
        """Generate a deterministic response based on prompt.

        Args:
            prompt: Input prompt
            max_tokens: Optional maximum length of response

        Returns:
            Generated response
        """
        # Get hash value for prompt
        hash_value = self._text_to_hash(prompt)

        # List of possible response templates
        templates = [
            "Based on the provided context, {subject} {verb} {object}.",
            "The answer is that {subject} {verb} {object}.",
            "According to the context, {subject} {verb} {object}.",
            "From the information provided, {subject} {verb} {object}.",
        ]

        # List of possible subjects, verbs, and objects
        subjects = [
            "the system",
            "the process",
            "the model",
            "the algorithm",
            "the implementation",
        ]
        verbs = [
            "processes",
            "analyzes",
            "computes",
            "generates",
            "evaluates",
        ]
        objects = [
            "the data",
            "the input",
            "the results",
            "the information",
            "the output",
        ]

        # Use hash to deterministically select components
        template = templates[hash_value % len(templates)]
        subject = subjects[(hash_value // 16) % len(subjects)]
        verb = verbs[(hash_value // 256) % len(verbs)]
        object_ = objects[(hash_value // 4096) % len(objects)]

        # Generate response
        response = template.format(
            subject=subject,
            verb=verb,
            object=object_,
        )

        # Truncate if max_tokens specified (assuming ~4 chars per token)
        if max_tokens:
            max_chars = max_tokens * 4
            response = response[:max_chars]

        return response

    async def _generate_text(
        self,
        prompt: str,
        max_tokens: Optional[int] = None,
        **kwargs: Any,
    ) -> str:
        """Generate mock text response.

        Args:
            prompt: The formatted prompt string
            max_tokens: Maximum number of tokens to generate
            **kwargs: Additional arguments (ignored)

        Returns:
            Generated text

        Raises:
            GenerationError: If there is an error during generation
        """
        try:
            return self._generate_deterministic_response(
                prompt=prompt,
                max_tokens=max_tokens,
            )
        except Exception as e:
            raise GenerationError(f"Error in mock generation provider: {e}")
