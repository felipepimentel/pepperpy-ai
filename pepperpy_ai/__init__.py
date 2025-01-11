"""PepperPy AI - A flexible AI library with modular provider support."""

from pepperpy_ai.capabilities.base import BaseCapability, CapabilityConfig
from pepperpy_ai.capabilities.chat.base import BaseChat, ChatConfig
from pepperpy_ai.capabilities.rag.base import BaseRAG, Document, RAGConfig
from pepperpy_ai.exceptions import (
    CapabilityError,
    ConfigurationError,
    DependencyError,
    PepperPyAIError,
    ProviderError,
    ValidationError,
)
from pepperpy_ai.providers.base import BaseProvider
from pepperpy_ai.responses import AIResponse
from pepperpy_ai.types import Message, MessageRole
from pepperpy_ai.utils import (
    check_dependency,
    format_exception,
    get_missing_dependencies,
    merge_configs,
    safe_import,
    verify_dependencies,
)

__version__ = "0.1.0"

__all__ = [
    # Base classes
    "BaseCapability",
    "BaseChat",
    "BaseProvider",
    "BaseRAG",
    # Configuration classes
    "CapabilityConfig",
    "ChatConfig",
    "RAGConfig",
    # Data classes
    "AIResponse",
    "Document",
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
try:
    from pepperpy_ai.capabilities.embeddings.base import BaseEmbedding, EmbeddingConfig
    from pepperpy_ai.capabilities.embeddings.simple import SimpleEmbedding
    from pepperpy_ai.capabilities.rag.simple import SimpleRAG
    __all__.extend([
        "BaseEmbedding",
        "EmbeddingConfig",
        "SimpleEmbedding",
        "SimpleRAG",
    ])
except ImportError:
    pass
