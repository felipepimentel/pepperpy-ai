"""Pepperpy - A modular and extensible framework for scalable AI systems."""

from .providers import ProviderRegistry
from .providers.llm.base import BaseLLMProvider
from .providers.vector_store.base import BaseVectorStoreProvider
from .providers.embeddings.base import BaseEmbeddingProvider
from .agents.base import BaseAgent
from .agents.factory import AgentBuilder
from .memory.interfaces import BaseMemory, ShortTermMemory, LongTermMemory

__version__ = "0.1.0"

__all__ = [
    "ProviderRegistry",
    "BaseLLMProvider",
    "BaseVectorStoreProvider",
    "BaseEmbeddingProvider",
    "BaseAgent",
    "AgentBuilder",
    "BaseMemory",
    "ShortTermMemory",
    "LongTermMemory",
]
