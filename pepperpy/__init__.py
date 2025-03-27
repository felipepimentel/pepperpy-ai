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

from pepperpy.core import PepperpyError, ValidationError, Component
from pepperpy.embeddings import EmbeddingProvider, EmbeddingsProvider, create_provider as create_embeddings_provider
from pepperpy.llm import GenerationResult, LLMProvider, Message, MessageRole, create_provider as create_llm_provider
from pepperpy.pepperpy import PepperPy
from pepperpy.rag import Document, Query, RAGProvider, create_provider as create_rag_provider
from pepperpy.storage import StorageProvider, create_provider as create_storage_provider
from pepperpy.tts import TTSProvider, create_provider as create_tts_provider

__all__ = [
    # Core
    "PepperpyError",
    "ValidationError",
    "Component",
    
    # Main class
    "PepperPy",
    
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
