"""Base embedding provider implementation."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from ..config.base import BaseConfigData, JsonDict


@dataclass
class EmbeddingConfig(BaseConfigData):
    """Embedding configuration."""

    # Required fields first (no defaults)
    name: str
    model: str
    dimension: int

    # Optional fields (with defaults)
    metadata: JsonDict = field(default_factory=dict)
    settings: JsonDict = field(default_factory=dict)


class EmbeddingProvider(ABC):
    """Base embedding provider."""

    def __init__(self, config: EmbeddingConfig) -> None:
        """Initialize provider."""
        self.config = config
        self._initialized = False

    @property
    def is_initialized(self) -> bool:
        """Check if provider is initialized."""
        return self._initialized

    async def initialize(self) -> None:
        """Initialize provider."""
        await self._setup()
        self._initialized = True

    async def cleanup(self) -> None:
        """Cleanup provider resources."""
        await self._teardown()
        self._initialized = False

    @abstractmethod
    async def _setup(self) -> None:
        """Setup provider resources."""
        pass

    @abstractmethod
    async def _teardown(self) -> None:
        """Teardown provider resources."""
        pass

    @abstractmethod
    async def embed(self, text: str) -> list[float]:
        """Generate embedding for text.

        Args:
            text: Text to embed

        Returns:
            Embedding vector
        """
        pass

    @abstractmethod
    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for multiple texts.

        Args:
            texts: Texts to embed

        Returns:
            List of embedding vectors
        """
        pass
