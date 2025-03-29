"""PepperPy: A Python framework for building AI-powered applications.

This module provides a high-level interface for building AI applications
with support for:
- Content processing (documents, images, audio, video)
- Large Language Models (LLMs)
- Retrieval Augmented Generation (RAG)
- Workflows and pipelines
- Multi-agent systems
"""

from pepperpy.core.base import PepperpyError
from pepperpy.core.config import PepperpyConfig
from pepperpy.core.pepperpy import PepperPy

from pepperpy.content_processing.base import (
    ContentProcessor,
    ContentType,
)
from pepperpy.content_processing.errors import (
    ContentProcessingError,
    ProviderNotFoundError,
)
from pepperpy.content_processing.lazy import (
    DEFAULT_PROCESSORS,
    AVAILABLE_PROCESSORS,
)

from pepperpy.llm import (
    LLMProvider,
    OpenAIProvider,
    AnthropicProvider,
    create_provider as create_llm_provider,
)

from pepperpy.rag import (
    RAGProvider,
    ChromaProvider,
    create_provider as create_rag_provider,
)

from pepperpy.workflow import (
    WorkflowProvider,
    create_provider as create_workflow_provider,
)

__version__ = "0.1.0"

__all__ = [
    # Core
    "PepperPy",
    "PepperpyConfig",
    "PepperpyError",
    # Content Processing
    "ContentProcessor",
    "ContentType",
    "ContentProcessingError",
    "ProviderNotFoundError",
    "DEFAULT_PROCESSORS",
    "AVAILABLE_PROCESSORS",
    # LLM
    "LLMProvider",
    "OpenAIProvider",
    "AnthropicProvider",
    "create_llm_provider",
    # RAG
    "RAGProvider",
    "ChromaProvider",
    "create_rag_provider",
    # Workflow
    "WorkflowProvider",
    "create_workflow_provider",
]
