"""Base classes for LLM models.

This module provides a stable public interface for LLM model abstractions.
It exposes the core model classes and interfaces that are considered
part of the public API.

Classes:
    ModelInfo: Information about an LLM model
    ModelCapability: Enumeration of model capabilities
    ModelRegistry: Registry of available models
"""

from enum import Enum, auto
from typing import Dict, List, Optional, Set


class ModelCapability(Enum):
    """Capabilities that an LLM model may support."""

    TEXT_GENERATION = auto()
    CHAT = auto()
    EMBEDDINGS = auto()
    CODE_GENERATION = auto()
    FUNCTION_CALLING = auto()
    IMAGE_UNDERSTANDING = auto()
    AUDIO_UNDERSTANDING = auto()
    MULTILINGUAL = auto()


class ModelInfo:
    """Information about an LLM model.

    Attributes:
        model_id: Unique identifier for the model
        provider: The provider of the model
        name: Human-readable name for the model
        capabilities: Set of capabilities supported by the model
        context_window: Maximum context window size in tokens
        max_output_tokens: Maximum number of tokens in the output
        description: Description of the model
    """

    def __init__(
        self,
        model_id: str,
        provider: str,
        name: str,
        capabilities: Set[ModelCapability],
        context_window: int,
        max_output_tokens: Optional[int] = None,
        description: str = "",
    ):
        """Initialize model information.

        Args:
            model_id: Unique identifier for the model
            provider: The provider of the model
            name: Human-readable name for the model
            capabilities: Set of capabilities supported by the model
            context_window: Maximum context window size in tokens
            max_output_tokens: Maximum number of tokens in the output
            description: Description of the model
        """
        self.model_id = model_id
        self.provider = provider
        self.name = name
        self.capabilities = capabilities
        self.context_window = context_window
        self.max_output_tokens = max_output_tokens or context_window
        self.description = description

    def supports_capability(self, capability: ModelCapability) -> bool:
        """Check if the model supports a specific capability.

        Args:
            capability: The capability to check

        Returns:
            True if the model supports the capability, False otherwise
        """
        return capability in self.capabilities

    def to_dict(self) -> Dict:
        """Convert to a dictionary representation.

        Returns:
            Dictionary representation of the model information
        """
        return {
            "model_id": self.model_id,
            "provider": self.provider,
            "name": self.name,
            "capabilities": [cap.name for cap in self.capabilities],
            "context_window": self.context_window,
            "max_output_tokens": self.max_output_tokens,
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "ModelInfo":
        """Create a ModelInfo instance from a dictionary.

        Args:
            data: Dictionary representation of model information

        Returns:
            A ModelInfo instance
        """
        capabilities = {ModelCapability[cap] for cap in data.get("capabilities", [])}
        return cls(
            model_id=data["model_id"],
            provider=data["provider"],
            name=data["name"],
            capabilities=capabilities,
            context_window=data["context_window"],
            max_output_tokens=data.get("max_output_tokens"),
            description=data.get("description", ""),
        )


class ModelRegistry:
    """Registry of available LLM models.

    This class provides a centralized registry for LLM models,
    allowing discovery and selection of models based on capabilities
    and other criteria.

    Attributes:
        models: Dictionary of registered models, keyed by model ID
    """

    def __init__(self):
        """Initialize the model registry."""
        self.models: Dict[str, ModelInfo] = {}

    def register_model(self, model_info: ModelInfo) -> None:
        """Register a model with the registry.

        Args:
            model_info: Information about the model to register
        """
        self.models[model_info.model_id] = model_info

    def get_model(self, model_id: str) -> Optional[ModelInfo]:
        """Get a model by ID.

        Args:
            model_id: The ID of the model to get

        Returns:
            The model information if found, None otherwise
        """
        return self.models.get(model_id)

    def list_models(self) -> List[ModelInfo]:
        """List all registered models.

        Returns:
            List of all registered models
        """
        return list(self.models.values())

    def find_models_by_provider(self, provider: str) -> List[ModelInfo]:
        """Find models by provider.

        Args:
            provider: The provider to filter by

        Returns:
            List of models from the specified provider
        """
        return [model for model in self.models.values() if model.provider == provider]

    def find_models_by_capability(self, capability: ModelCapability) -> List[ModelInfo]:
        """Find models that support a specific capability.

        Args:
            capability: The capability to filter by

        Returns:
            List of models that support the specified capability
        """
        return [
            model
            for model in self.models.values()
            if model.supports_capability(capability)
        ]

    def find_models_by_context_window(self, min_size: int) -> List[ModelInfo]:
        """Find models with a context window of at least the specified size.

        Args:
            min_size: The minimum context window size in tokens

        Returns:
            List of models with a context window of at least the specified size
        """
        return [
            model for model in self.models.values() if model.context_window >= min_size
        ]


# Export public classes
__all__ = [
    "ModelCapability",
    "ModelInfo",
    "ModelRegistry",
]
