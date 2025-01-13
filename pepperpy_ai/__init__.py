"""PepperPy AI package."""

from pepperpy_core.types import BaseConfig

from .ai_types import MessageRole
from .capabilities.base import BaseCapability
from .capabilities.config import CapabilityConfig
from .capabilities.embeddings.config import EmbeddingsConfig
from .responses import AIResponse
from .types import Message

__all__ = [
    "AIResponse",
    "BaseCapability",
    "BaseConfig",
    "CapabilityConfig",
    "EmbeddingsConfig",
    "Message",
    "MessageRole",
]
