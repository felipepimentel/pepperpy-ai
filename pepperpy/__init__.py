"""PepperPy: A framework for AI-powered applications.

PepperPy simplifies the development of AI applications by providing a unified
API for working with language models, embeddings, RAG, text-to-speech, and more.

Example:
    >>> import pepperpy
    >>> instance = pepperpy.PepperPy()
    >>> instance.with_llm().with_rag()
    >>> async with instance:
    ...     await instance.ask("What is PepperPy?")
"""

__version__ = "0.1.0"

from pepperpy.core import Component, PepperpyError, ValidationError

# Comment out problematic imports while we're fixing document_processing
# from pepperpy.document_processing import (
#     DocumentContent,
#     DocumentMetadata,
#     DocumentProcessingProvider,
#     DocumentType,
# )
# from pepperpy.document_processing import (
#     create_provider as create_document_processing_provider,
# )
from pepperpy.embeddings import EmbeddingProvider, EmbeddingsProvider
from pepperpy.embeddings import create_provider as create_embeddings_provider
from pepperpy.llm import GenerationResult, LLMProvider, Message, MessageRole
from pepperpy.llm import create_provider as create_llm_provider
from pepperpy.pepperpy import PepperPy
from pepperpy.rag import Document, Query, RAGProvider
from pepperpy.rag import create_provider as create_rag_provider
from pepperpy.storage import StorageProvider
from pepperpy.storage import create_provider as create_storage_provider
from pepperpy.tts import TTSProvider
from pepperpy.tts import create_provider as create_tts_provider

__all__ = [
    # Core
    "PepperpyError",
    "ValidationError",
    "Component",
    # Main class
    "PepperPy",
    # Document Processing
    # "DocumentContent",
    # "DocumentMetadata",
    # "DocumentProcessingProvider",
    # "DocumentType",
    # "create_document_processing_provider",
    # Embeddings
    "EmbeddingProvider",
    "EmbeddingsProvider",
    "create_embeddings_provider",
    # LLM
    "LLMProvider",
    "Message",
    "MessageRole",
    "GenerationResult",
    "create_llm_provider",
    # RAG
    "Document",
    "Query",
    "RAGProvider",
    "create_rag_provider",
    # Storage
    "StorageProvider",
    "create_storage_provider",
    # TTS
    "TTSProvider",
    "create_tts_provider",
    # Version
    "__version__",
]
