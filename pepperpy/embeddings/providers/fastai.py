"""FastAI embeddings provider implementation."""

from typing import Any, Dict, List, Union

from pepperpy.core.utils import import_provider, lazy_provider_class
from pepperpy.embeddings.base import EmbeddingProvider


@lazy_provider_class("embeddings", "fastai")
class FastAIEmbeddingProvider(EmbeddingProvider):
    """FastAI implementation of embeddings provider.

    This provider uses FastAI's AWD-LSTM model to generate embeddings.
    It's particularly good for text classification and sentiment analysis.
    """

    name = "fastai"

    def __init__(
        self,
        model: str = "english",  # Options: english, french, german, etc.
        device: str = "cpu",
        **kwargs: Any,
    ) -> None:
        """Initialize FastAI embeddings provider.

        Args:
            model: Language model to use
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
        fastai = import_provider("fastai", "embeddings", "fastai")
        fastai_text = import_provider("fastai.text", "embeddings", "fastai")

        # Load the language model
        self._model = fastai_text.language_model_learner(
            fastai.DataLoaders(),
            arch=fastai_text.AWD_LSTM,
            pretrained=True,
            drop_mult=0.3,
        )

        # Move to device
        self._model.model.to(self.device)

        # Set to eval mode
        self._model.model.eval()

        self._embedding_function = self._get_embedding_function()

    def _get_embedding_function(self) -> Any:
        """Create an embedding function compatible with vector stores."""
        import torch

        def embed_texts(texts: List[str]) -> List[List[float]]:
            # Process each text
            embeddings = []
            for text in texts:
                # Tokenize and numericalize
                tokens = self._model.dls.vocab(text)
                tensor = torch.tensor(tokens).unsqueeze(0).to(self.device)

                # Get embeddings from encoder
                with torch.no_grad():
                    raw_embeddings = self._model.model.encoder(tensor)

                # Mean pooling over sequence length
                embedding = raw_embeddings.mean(dim=1)

                # Normalize
                embedding = torch.nn.functional.normalize(embedding, p=2, dim=1)

                embeddings.append(embedding.cpu().squeeze().tolist())

            return embeddings

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
        return self._model.model.encoder.emb_sz

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
            "max_sequence_length": 1024,
        }
