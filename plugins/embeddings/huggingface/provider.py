"""HuggingFace embeddings provider implementation."""

from typing import Any, Dict, List, Union

from pepperpy.core.utils import import_provider, lazy_provider_class
from pepperpy.embeddings.base import EmbeddingProvider


@lazy_provider_class("embeddings", "huggingface")
class HuggingFaceEmbeddingProvider(EmbeddingProvider):
    """HuggingFace implementation of embeddings provider.

    This provider uses HuggingFace's transformers library to generate embeddings.
    It supports a wide range of models from the HuggingFace Hub.
    """

    

    # Attributes auto-bound from plugin.yaml com valores padrão como fallback
    api_key: str
    model: str = "default-model"
    base_url: str
    temperature: float = 0.7
    max_tokens: int = 1024
    user_id: str
    client: Optional[Any]

    def __init__(
        self,
        model: str = "sentence-transformers/all-MiniLM-L6-v2",
        device: str = "cpu",
        **kwargs: Any,
    ) -> None:
        """Initialize HuggingFace embeddings provider.

        Args:
            model: Model name from HuggingFace Hub
            device: Device to run model on ('cpu' or 'cuda')
            **kwargs: Additional configuration options
        """
        super().__init__(**kwargs)
        self.model_name = model
        self.device = device
        self._model = None
        self._tokenizer = None
        self._embedding_function = None

    async def initialize(self) -> None:
        """Initialize the provider by loading the model."""
        transformers = import_provider("transformers", "embeddings", "huggingface")

        # Load tokenizer and model
        self._tokenizer = transformers.AutoTokenizer.from_pretrained(self.model_name)
        self._model = transformers.AutoModel.from_pretrained(self.model_name)
        self._model.to(self.device)

        # Set model to evaluation mode
        self._model.eval()

        self._embedding_function = self._get_embedding_function()

    def _get_embedding_function(self) -> Any:
        """Create an embedding function compatible with vector stores."""
        import torch

        def mean_pooling(model_output: Any, attention_mask: Any) -> Any:
            """Mean pooling to get sentence embeddings."""
            token_embeddings = model_output[0]
            input_mask_expanded = (
                attention_mask.unsqueeze(-1).expand(token_embeddings.size()).float()
            )
            return torch.sum(token_embeddings * input_mask_expanded, 1) / torch.clamp(
                input_mask_expanded.sum(1), min=1e-9
            )

        def embed_texts(texts: List[str]) -> List[List[float]]:
            # Tokenize texts
            encoded_input = self._tokenizer(
                texts,
                padding=True,
                truncation=True,
                max_length=512,
                return_tensors="pt",
            )
            encoded_input = {k: v.to(self.device) for k, v in encoded_input.items()}

            # Compute token embeddings
            with torch.no_grad():
                model_output = self._model(**encoded_input)

            # Perform pooling
            embeddings = mean_pooling(model_output, encoded_input["attention_mask"])

            # Normalize embeddings
            embeddings = torch.nn.functional.normalize(embeddings, p=2, dim=1)

            return embeddings.cpu().tolist()

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
        return self._model.config.hidden_size

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
