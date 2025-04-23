"""
OpenAI Embeddings provider for PepperPy

This provider implements a embedding plugin for the PepperPy framework.
"""

import random
from typing import Any

from pepperpy.embedding.base import EmbeddingError, EmbeddingProvider
from pepperpy.plugin import BasePluginProvider, ProviderPlugin


class OpenAIEmbeddingsProvider(EmbeddingProvider, BasePluginProvider, ProviderPlugin):
    """Embedding OpenAI provider.

    This provider implements OpenAI embedding functionality for the PepperPy embedding framework.
    """

    # Type annotations for config attributes
    api_key: str
    model: str = "text-embedding-3-small"
    dimensions: int = 256
    batch_size: int = 100

    async def initialize(self) -> None:
        """Initialize the provider.

        This method is called automatically when the provider is first used.
        """
        # Skip if already initialized
        initialized = self.initialized
        if initialized:
            return

        # Initialize resources
        # TODO: Add initialization code

        self.initialized = True
        self.logger.debug(
            f"Initialized with model={self.model}, dimensions={self.dimensions}"
        )

    async def cleanup(self) -> None:
        """Clean up provider resources.

        This method is called automatically when the context manager exits.
        """
        if not self.initialized:
            return

        # Clean up resources
        # TODO: Add cleanup code for any resources created during initialization

        try:
            # Clean up resources using the instance method inherited from ResourceMixin
            await self.cleanup_resources()
        except Exception as e:
            self.logger.error(f"Error cleaning up resources: {e}")

        self.initialized = False
        self.logger.debug("Provider resources cleaned up")

    async def execute(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """Execute a task based on input data.

        Args:
            input_data: Input data containing task and parameters

        Returns:
            Task execution result with status and result/message
        """
        # Get task type from input
        task_type = input_data.get("task")

        if not task_type:
            return {"status": "error", "message": "No task specified"}

        try:
            # Handle different task types
            if task_type == "embed_text":
                text = input_data.get("text")
                if not text:
                    return {
                        "status": "error",
                        "message": "No text provided for embedding",
                    }

                embedding = await self.embed(text)
                return {"status": "success", "result": embedding}
            elif task_type == "example_task":
                # TODO: Implement task
                return {"status": "success", "result": "Task executed successfully"}
            else:
                return {"status": "error", "message": f"Unknown task type: {task_type}"}

        except Exception as e:
            self.logger.error(f"Error executing task '{task_type}': {e}")
            return {"status": "error", "message": str(e)}

    async def embed(self, text: str, **kwargs: Any) -> list[float]:
        """Generate embeddings for text.

        Args:
            text: Text to embed
            **kwargs: Additional parameters for embedding

        Returns:
            Embedding vector
        """
        if not self.initialized:
            await self.initialize()

        # Get dimensions from kwargs or use default
        dims = kwargs.get("dimensions", self.dimensions)

        try:
            # Use OpenAI embeddings API
            try:
                from openai import AsyncOpenAI

                # Initialize client
                client = AsyncOpenAI(api_key=self.api_key)

                # Call OpenAI API
                response = await client.embeddings.create(
                    model=self.model, input=text, dimensions=dims
                )

                # Extract embedding
                return response.data[0].embedding
            except (ImportError, ModuleNotFoundError):
                self.logger.warning(
                    "OpenAI package not installed or API unavailable. Using fallback for testing. "
                    "Install with: pip install openai>=1.0.0"
                )
                # Fallback for testing - return random vector
                return [random.random() for _ in range(dims)]

        except Exception as e:
            self.logger.error(f"Error generating embedding: {e}")
            raise EmbeddingError(f"Failed to generate embedding: {e}") from e
