"""Base LLM interface and abstract class."""

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class LLMConfig:
    """Configuration for LLM instances.

    Attributes:
        model_name: Name/version of the model
        temperature: Sampling temperature (0-2)
        max_tokens: Maximum tokens to generate
        stop_sequences: Sequences to stop generation
        model_kwargs: Additional model parameters
    """

    model_name: str
    temperature: float = 0.7
    max_tokens: int = 1000
    stop_sequences: list[str] = field(default_factory=list)
    model_kwargs: dict[str, Any] = field(default_factory=dict)


@dataclass
class LLMResponse:
    """Response from an LLM.

    Attributes:
        text: Generated text
        tokens_used: Number of tokens used
        finish_reason: Why generation stopped
        model_name: Model that generated response
        timestamp: When response was generated
        metadata: Additional response metadata
    """

    text: str
    tokens_used: int
    finish_reason: str
    model_name: str
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: dict[str, Any] = field(default_factory=dict)


class BaseLLM(ABC):
    """Abstract base class for LLM implementations.

    Defines the core interface that all LLMs must implement:
    1. Initialization and cleanup
    2. Text generation (sync and streaming)
    3. Configuration management
    """

    def __init__(self, config: LLMConfig) -> None:
        """Initialize base LLM.

        Args:
            config: LLM configuration
        """
        self.config = config
        self.is_initialized = False

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize LLM resources.

        This method should:
        1. Set up API clients/connections
        2. Load any required models/data
        3. Validate configuration

        Raises:
            Exception: If initialization fails
        """
        pass

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        stop: list[str] | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> LLMResponse:
        """Generate text from prompt.

        This method should:
        1. Validate input parameters
        2. Generate text using model
        3. Format and return response

        Args:
            prompt: Input prompt
            stop: Optional stop sequences
            temperature: Optional temperature override
            max_tokens: Optional max tokens override
            **kwargs: Additional model parameters

        Returns:
            Generated response

        Raises:
            Exception: If generation fails
        """
        pass

    @abstractmethod
    def generate_stream(
        self,
        prompt: str,
        stop: list[str] | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> AsyncIterator[str]:
        """Stream generated text from prompt.

        This method should:
        1. Validate input parameters
        2. Generate text using model
        3. Stream chunks as they're generated

        Args:
            prompt: Input prompt
            stop: Optional stop sequences
            temperature: Optional temperature override
            max_tokens: Optional max tokens override
            **kwargs: Additional model parameters

        Returns:
            Async iterator of text chunks

        Raises:
            Exception: If generation fails
        """
        pass

    @abstractmethod
    async def cleanup(self) -> None:
        """Clean up LLM resources.

        This method should:
        1. Close connections/clients
        2. Free model resources
        3. Reset internal state

        Raises:
            Exception: If cleanup fails
        """
        pass

    @abstractmethod
    async def embed(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for texts.

        This method should:
        1. Validate input texts
        2. Generate embeddings using model
        3. Format and return embeddings

        Args:
            texts: List of texts to embed

        Returns:
            List of embeddings (one per text)

        Raises:
            Exception: If embedding generation fails
        """
        pass

    def validate_config(self) -> None:
        """Validate LLM configuration.

        This method should:
        1. Check required fields
        2. Validate field types/values
        3. Set defaults for optional fields

        Raises:
            ValueError: If configuration is invalid
        """
        # Check required fields
        if not self.config.model_name:
            raise ValueError("model_name is required")

        # Validate field values
        if not isinstance(self.config.temperature, int | float):
            raise ValueError("temperature must be a number")
        if self.config.temperature < 0 or self.config.temperature > 2:
            raise ValueError("temperature must be between 0 and 2")

        if not isinstance(self.config.max_tokens, int):
            raise ValueError("max_tokens must be an integer")
        if self.config.max_tokens < 1:
            raise ValueError("max_tokens must be positive")

        if not isinstance(self.config.stop_sequences, list):
            raise ValueError("stop_sequences must be a list")
        if not all(isinstance(s, str) for s in self.config.stop_sequences):
            raise ValueError("stop_sequences must contain only strings")

        if not isinstance(self.config.model_kwargs, dict):
            raise ValueError("model_kwargs must be a dictionary")

    def get_config(self, key: str, default: Any = None) -> Any:
        """Get configuration value.

        Args:
            key: Configuration key
            default: Default value if key not found

        Returns:
            Configuration value
        """
        if hasattr(self.config, key):
            return getattr(self.config, key)
        if hasattr(self.config, "model_kwargs"):
            return self.config.model_kwargs.get(key, default)
        return default

    def update_config(self, updates: dict[str, Any]) -> None:
        """Update configuration values.

        Args:
            updates: Configuration updates

        Raises:
            ValueError: If updates are invalid
        """
        # Update direct attributes
        for key, value in updates.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)
            else:
                self.config.model_kwargs[key] = value

        # Revalidate
        self.validate_config()

    async def __aenter__(self) -> "BaseLLM":
        """Async context manager entry.

        Returns:
            Self instance

        Raises:
            Exception: If initialization fails
        """
        if not self.is_initialized:
            await self.initialize()
            self.is_initialized = True
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Async context manager exit.

        Args:
            exc_type: Exception type if error occurred
            exc_val: Exception value if error occurred
            exc_tb: Exception traceback if error occurred
        """
        await self.cleanup()
        self.is_initialized = False
