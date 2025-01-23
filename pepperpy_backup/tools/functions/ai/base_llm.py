"""Base LLM interface and abstract class."""

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from pepperpy.llms.types import ProviderStats, LLMResponse, ProviderConfig


@dataclass
class LLMConfig:
    """Configuration for LLM instances.

    Attributes:
        model_name: Name/version of the model
        temperature: Sampling temperature (0-2)
        max_tokens: Maximum tokens to generate
        stop_sequences: Sequences to stop generation
        model_kwargs: Additional model parameters
        type: Provider type (e.g., "huggingface", "openai")
        api_key: API key for the provider
        is_fallback: Whether this is a fallback provider
        priority: Priority for fallback selection (higher = more preferred)
    """

    model_name: str
    type: str = "huggingface"
    api_key: str = ""
    temperature: float = 0.7
    max_tokens: int = 1000
    stop_sequences: List[str] = field(default_factory=list)
    model_kwargs: Dict[str, Any] = field(default_factory=dict)
    is_fallback: bool = False
    priority: int = 100


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
    metadata: Dict[str, Any] = field(default_factory=dict)


class BaseLLM(ABC):
    """Abstract base class for LLM providers."""
    
    def __init__(self, config: ProviderConfig) -> None:
        """Initialize LLM provider.
        
        Args:
            config: Provider configuration.
        """
        self.config = config
        self.stats = ProviderStats()
        self.is_initialized = False
    
    @abstractmethod
    async def initialize(self) -> None:
        """Initialize provider resources.
        
        This method should:
        1. Set up API clients/connections
        2. Load any required models/data
        3. Validate configuration
        
        Raises:
            Exception: If initialization fails
        """
        pass
    
    @abstractmethod
    async def cleanup(self) -> None:
        """Clean up provider resources.
        
        This method should:
        1. Close connections/clients
        2. Free model resources
        3. Reset internal state
        
        Raises:
            Exception: If cleanup fails
        """
        pass
    
    @abstractmethod
    async def generate(self, prompt: str) -> LLMResponse:
        """Generate text from prompt.
        
        Args:
            prompt: Input prompt.
            
        Returns:
            Generated text response.
        """
        pass
    
    @abstractmethod
    async def generate_stream(self, prompt: str) -> AsyncIterator[str]:
        """Generate text from prompt in streaming mode.
        
        Args:
            prompt: Input prompt.
            
        Returns:
            Iterator of generated text chunks.
        """
        pass
    
    @abstractmethod
    async def get_embedding(self, text: str) -> List[float]:
        """Get embedding vector for text.
        
        Args:
            text: Input text.
            
        Returns:
            Embedding vector as list of floats.
        """
        pass
    
    def validate_config(self) -> None:
        """Validate LLM configuration.
        
        Raises:
            ValueError: If configuration is invalid.
        """
        if not self.config.api_key:
            raise ValueError("API key is required")
        if not self.config.model_name:
            raise ValueError("Model name is required")

    def get_config(self, key: str, default: Any = None) -> Any:
        """Get configuration value.

        Args:
            key: Configuration key
            default: Default value if key not found

        Returns:
            Configuration value
        """
        return self.config.model_kwargs.get(key, default)

    def update_config(self, updates: Dict[str, Any]) -> None:
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
