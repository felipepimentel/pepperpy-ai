"""PepperPy AI - A flexible AI library with modular provider support."""

from typing import TYPE_CHECKING

from .capabilities.base import BaseCapability, CapabilityConfig
from .exceptions import (
    CapabilityError,
    ConfigurationError,
    DependencyError,
    PepperPyAIError,
    ProviderError,
    ValidationError,
)
from .providers.base import BaseProvider
from .responses import AIResponse
from .types import Message, MessageRole
from .utils import (
    check_dependency,
    format_exception,
    get_missing_dependencies,
    merge_configs,
    safe_import,
    verify_dependencies,
)

if TYPE_CHECKING:
    from .capabilities.chat.base import ChatCapability, ChatConfig
    from .capabilities.rag.base import RAGCapability, Document, RAGConfig
    from .capabilities.embeddings.base import BaseEmbeddingsCapability
    from .embeddings.base import EmbeddingsConfig

__version__ = "0.1.0"

__all__ = [
    # Base classes
    "BaseCapability",
    "BaseProvider",
    # Configuration classes
    "CapabilityConfig",
    # Data classes
    "AIResponse",
    "Message",
    # Enums
    "MessageRole",
    # Exceptions
    "CapabilityError",
    "ConfigurationError",
    "DependencyError",
    "PepperPyAIError",
    "ProviderError",
    "ValidationError",
    # Utilities
    "check_dependency",
    "format_exception",
    "get_missing_dependencies",
    "merge_configs",
    "safe_import",
    "verify_dependencies",
]

# Optional implementations
if check_dependency("sentence_transformers"):
    from .capabilities.chat.base import ChatCapability, ChatConfig
    from .capabilities.rag.base import RAGCapability, Document, RAGConfig
    from .capabilities.embeddings.base import BaseEmbeddingsCapability
    from .embeddings.base import EmbeddingsConfig
    __all__.extend([
        "ChatCapability",
        "ChatConfig",
        "RAGCapability",
        "RAGConfig",
        "Document",
        "BaseEmbeddingsCapability",
        "EmbeddingsConfig",
    ])
