"""PepperPy: A Python framework for building AI-powered applications.

This module provides a high-level interface for building AI applications
with support for:
- Content processing (documents, images, audio, video)
- Large Language Models (LLMs)
- Retrieval Augmented Generation (RAG)
- Workflows and pipelines
- Multi-agent systems
"""

from pepperpy.content_processing.base import (
    ContentProcessor,
    ContentType,
)
from pepperpy.content_processing.errors import (
    ContentProcessingError,
    ProviderNotFoundError,
)
from pepperpy.content_processing.lazy import (
    AVAILABLE_PROCESSORS,
    DEFAULT_PROCESSORS,
)
from pepperpy.core.base import PepperpyError
from pepperpy.core.config import Config
from pepperpy.llm import (
    GenerationResult,
    LLMProvider,
    Message,
    MessageRole,
)
from pepperpy.llm import (
    create_provider as create_llm_provider,
)
from pepperpy.pepperpy import PepperPy
from pepperpy.rag import (
    RAGProvider,
)
from pepperpy.rag import (
    create_provider as create_rag_provider,
)
from pepperpy.workflow import (
    WorkflowProvider,
)
from pepperpy.workflow import (
    create_provider as create_workflow_provider,
)

__version__ = "0.1.0"

__all__ = [
    # Core
    "PepperPy",
    "Config",
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
    "Message",
    "MessageRole",
    "GenerationResult",
    "create_llm_provider",
    # RAG
    "RAGProvider",
    "create_rag_provider",
    # Workflow
    "WorkflowProvider",
    "create_workflow_provider",
]
