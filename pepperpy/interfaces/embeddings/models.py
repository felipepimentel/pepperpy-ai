"""
Embedding models interface.

This module provides the public interface for embedding models.
"""

from typing import Dict, List, Optional


class EmbeddingModel:
    """Base class for embedding models.

    This class defines the interface that all embedding models must implement.
    """

    def __init__(self, model_name: str, dimension: int):
        """Initialize embedding model.

        Args:
            model_name: Name of the model
            dimension: Embedding dimension
        """
        self.model_name = model_name
        self.dimension = dimension

    async def embed(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for a list of texts.

        Args:
            texts: List of texts to embed

        Returns:
            List of embedding vectors

        Raises:
            NotImplementedError: If not implemented by subclass
        """
        raise NotImplementedError("Embedding model must implement embed method")


class OpenAIEmbeddingModel(EmbeddingModel):
    """OpenAI embedding model.

    This class provides access to OpenAI's text embedding models.
    """

    def __init__(
        self,
        model_name: str = "text-embedding-ada-002",
        dimension: int = 1536,
        api_key: Optional[str] = None,
    ):
        """Initialize OpenAI embedding model.

        Args:
            model_name: OpenAI model name
            dimension: Embedding dimension
            api_key: OpenAI API key (uses env var if None)
        """
        super().__init__(model_name, dimension)
        self.api_key = api_key


class HuggingFaceEmbeddingModel(EmbeddingModel):
    """HuggingFace embedding model.

    This class provides access to HuggingFace's text embedding models.
    """

    def __init__(
        self,
        model_name: str,
        dimension: int,
        api_key: Optional[str] = None,
    ):
        """Initialize HuggingFace embedding model.

        Args:
            model_name: HuggingFace model name or path
            dimension: Embedding dimension
            api_key: HuggingFace API key (uses env var if None)
        """
        super().__init__(model_name, dimension)
        self.api_key = api_key


class SentenceTransformerModel(EmbeddingModel):
    """Sentence Transformer embedding model.

    This class provides access to Sentence Transformer models.
    """

    def __init__(
        self,
        model_name: str = "all-MiniLM-L6-v2",
        dimension: Optional[int] = None,
    ):
        """Initialize Sentence Transformer model.

        Args:
            model_name: Model name or path
            dimension: Embedding dimension (auto-detected if None)
        """
        # Default dimension will be set after loading the model
        super().__init__(model_name, dimension or 384)


class ModelRegistry:
    """Registry for embedding models.

    This class provides a centralized registry for embedding models
    and utilities for model selection and management.
    """

    _models: Dict[str, EmbeddingModel] = {}

    @classmethod
    def list_models(cls) -> List[str]:
        """List available embedding models.

        Returns:
            List of model identifiers
        """
        return list(cls._models.keys())

    @classmethod
    def get_model(cls, model_name: str) -> EmbeddingModel:
        """Get an embedding model by name.

        Args:
            model_name: Model identifier

        Returns:
            Embedding model instance

        Raises:
            ValueError: If model doesn't exist
        """
        if model_name not in cls._models:
            raise ValueError(f"Model '{model_name}' not found in registry")
        return cls._models[model_name]

    @classmethod
    def register_model(cls, model_name: str, model: EmbeddingModel) -> None:
        """Register a custom embedding model.

        Args:
            model_name: Model identifier
            model: Embedding model instance

        Raises:
            ValueError: If model already exists
        """
        if model_name in cls._models:
            raise ValueError(f"Model '{model_name}' already exists in registry")
        cls._models[model_name] = model
