"""Local embeddings provider implementation using sentence-transformers."""

from typing import Any, Dict, List, Union

from pepperpy.core.utils import import_provider, lazy_provider_class
from pepperpy.embeddings.base import EmbeddingProvider


@lazy_provider_class("embeddings", "local")
class LocalProvider(EmbeddingProvider):
    """Local implementation of embeddings provider using sentence-transformers.

    This provider runs completely offline without requiring any API keys.
    It uses the sentence-transformers library which provides high quality
    multilingual embeddings.
    """

    name = "local"

    def __init__(
        self,
        model: str = "all-MiniLM-L6-v2",
        device: str = "cpu",
        **kwargs: Any,
    ) -> None:
        """Initialize local embeddings provider.

        Args:
            model: Model name from sentence-transformers to use
                  See https://www.sbert.net/docs/pretrained_models.html
            device: Device to run model on ('cpu' or 'cuda')
            **kwargs: Additional configuration options
        """
        super().__init__(**kwargs)
        self.model_name = model
        self.device = device
        self._model = None
        self._embedding_function = None

    async def initialize(self) -> None:
        """Initialize the provider by loading the model."""
        sentence_transformers = import_provider(
            "sentence_transformers", "embeddings", "local"
        )
        self._model = sentence_transformers.SentenceTransformer(
            self.model_name, device=self.device
        )
        self._embedding_function = self._get_embedding_function()

    def _get_embedding_function(self) -> Any:
        """Create an embedding function compatible with vector stores."""

        def embed_texts(texts: List[str]) -> List[List[float]]:
            return self._model.encode(
                texts, convert_to_numpy=True, normalize_embeddings=True
            ).tolist()

        return embed_texts

    async def embed_text(self, text: Union[str, List[str]]) -> List[List[float]]:
        """Generate embeddings for the given text.

        Args:
            text: Text or list of texts to embed

        Returns:
            List of embeddings vectors
        """
        if isinstance(text, str):
            text = [text]
        return self._embedding_function(text)

    async def embed_query(self, text: str) -> List[float]:
        """Generate embeddings for a query.

        Args:
            text: Query text to embed

        Returns:
            Embedding vector
        """
        return (await self.embed_text(text))[0]

    def get_embedding_function(self) -> Any:
        """Get a function that can be used by vector stores.

        Returns:
            A callable that generates embeddings
        """
        return self._embedding_function

    async def get_dimensions(self) -> int:
        """Get the dimensionality of the embeddings.

        Returns:
            The number of dimensions in the embeddings
        """
        if not self._model:
            await self.initialize()
        return self._model.get_sentence_embedding_dimension()

    def get_config(self) -> Dict[str, Any]:
        """Get the provider configuration.

        Returns:
            The provider configuration
        """
        return {
            "model": self.model_name,
            "device": self.device,
        }

    def get_capabilities(self) -> Dict[str, Any]:
        """Get the provider capabilities.

        Returns:
            A dictionary of provider capabilities
        """
        return {
            "supports_batching": True,
            "supports_multilingual": True,
            "requires_gpu": False,
            "is_local": True,
            "max_sequence_length": 512,
        }
