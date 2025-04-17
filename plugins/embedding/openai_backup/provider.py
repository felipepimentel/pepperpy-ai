"""
OpenAI Embeddings provider for PepperPy

This provider implements text embedding capabilities using OpenAI's embedding models.
"""

from typing import Any, Dict, List, Optional

from openai import AsyncOpenAI
from openai.types.create_embedding_response import CreateEmbeddingResponse

from pepperpy.embedding.base import EmbeddingError, EmbeddingProvider
from pepperpy.plugin.provider import BasePluginProvider


class OpenAIEmbeddingsProvider(EmbeddingProvider, BasePluginProvider):
    """
    OpenAI embeddings provider for generating text embeddings.

    This provider connects to OpenAI's API to generate vector embeddings
    for text using models like text-embedding-3-small.
    """

    def __init__(self, **kwargs: Any) -> None:
        """Initialize the provider."""
        super().__init__(**kwargs)
        self.client: Optional[AsyncOpenAI] = None

    async def initialize(self) -> None:
        """Initialize the OpenAI client.

        This method is called automatically when the provider is first used.
        """
        # Call the base class implementation first
        await super().initialize()

        try:
            # Get configuration values
            api_key = self.config.get("api_key")

            if not api_key:
                raise EmbeddingError("OpenAI API key not provided")

            # Initialize OpenAI client
            self.client = AsyncOpenAI(api_key=api_key)

            model = self.config.get("model", "text-embedding-3-small")
            dimensions = self.config.get("dimensions", 256)
            self.logger.debug(
                f"Initialized with model={model}, dimensions={dimensions}"
            )
        except Exception as e:
            raise EmbeddingError(
                f"Failed to initialize OpenAI embeddings provider: {e}"
            ) from e

    async def cleanup(self) -> None:
        """Clean up resources.

        This method is called automatically when the context manager exits.
        """
        if hasattr(self, "client") and self.client:
            # Close the client if it has a close method
            if hasattr(self.client, "close"):
                await self.client.close()

            self.client = None

        # Call the base class cleanup
        await super().cleanup()

    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a task based on input data.

        Args:
            input_data: Input data containing task and parameters

        Returns:
            Task execution result
        """
        # Get task type from input
        task_type = input_data.get("task")

        if not task_type:
            return {"status": "error", "error": "No task specified"}

        try:
            # Handle embed task for single text
            if task_type == "embed":
                text = input_data.get("text")
                if not text:
                    return {"status": "error", "error": "No text provided"}

                # Get config from input
                config = input_data.get("config", {})

                # Generate embedding
                embedding = await self.embed_query(text, **config)

                return {
                    "status": "success",
                    "embedding": embedding,
                    "dimensions": len(embedding),
                }

            # Handle batch embedding
            elif task_type == "embed_batch":
                texts = input_data.get("texts", [])
                if not texts:
                    return {"status": "error", "error": "No texts provided"}

                # Get config from input
                config = input_data.get("config", {})

                # Generate embeddings
                embeddings = await self.embed_documents(texts, **config)

                return {
                    "status": "success",
                    "embeddings": embeddings,
                    "count": len(embeddings),
                }
            else:
                return {"status": "error", "error": f"Unknown task type: {task_type}"}

        except Exception as e:
            self.logger.error(f"Error executing task '{task_type}': {e}")
            return {"status": "error", "error": str(e)}

    async def embed_query(self, text: str, **kwargs: Any) -> List[float]:
        """Embed a single query text.

        Args:
            text: Text to embed
            **kwargs: Additional parameters

        Returns:
            List of floats representing the embedding

        Raises:
            EmbeddingError: If embedding generation fails
        """
        embeddings = await self.embed_documents([text], **kwargs)
        return embeddings[0]

    async def embed_documents(
        self, texts: List[str], **kwargs: Any
    ) -> List[List[float]]:
        """Embed multiple documents.

        Args:
            texts: List of texts to embed
            **kwargs: Additional parameters

        Returns:
            List of embeddings

        Raises:
            EmbeddingError: If embedding generation fails
        """
        if not self.initialized:
            await self.initialize()

        if not self.client:
            raise EmbeddingError("OpenAI client not initialized")

        try:
            # Get parameters from config with potential overrides
            model = kwargs.get(
                "model", self.config.get("model", "text-embedding-3-small")
            )
            dimensions = kwargs.get("dimensions", self.config.get("dimensions", 256))
            batch_size = self.config.get("batch_size", 100)

            all_embeddings: List[List[float]] = []

            # Process in batches if needed
            for i in range(0, len(texts), batch_size):
                batch = texts[i : i + batch_size]

                response: CreateEmbeddingResponse = await self.client.embeddings.create(
                    model=model,
                    input=batch,
                    dimensions=dimensions,
                )

                # Extract embeddings from response
                batch_embeddings = [data.embedding for data in response.data]
                all_embeddings.extend(batch_embeddings)

            return all_embeddings

        except Exception as e:
            raise EmbeddingError(f"Failed to generate embeddings: {e}") from e

    async def get_embedding_dimensions(self) -> int:
        """Get the dimensionality of embeddings.

        Returns:
            Number of dimensions in the embeddings
        """
        return self.config.get("dimensions", 256)
