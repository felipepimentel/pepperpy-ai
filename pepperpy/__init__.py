"""PepperPy Framework.

A modular framework for building AI-powered applications.

Example:
    >>> from pepperpy import PepperPy
    >>> async with PepperPy() as pepperpy:
    ...     response = await pepperpy.send("What is Python?")
"""

from typing import Any, Dict, List, Optional, Type, Union

# Core exports
from pepperpy.core.base import (
    BaseProvider,
    ConfigType,
    ConfigurationError,
    ConnectionError,
    HeadersType,
    HTTPError,
    JsonDict,
    JsonType,
    JsonValue,
    Metadata,
    PepperpyError,
    QueryParamsType,
    RequestError,
    ResponseError,
    SearchResult,
    TimeoutError,
    ValidationError,
    WorkflowProvider,
)
from pepperpy.core.config import Config
from pepperpy.core.http import HTTPClient, HTTPResponse

# Provider interfaces
from pepperpy.embeddings.base import EmbeddingProvider
from pepperpy.llm.base import GenerationResult, LLMProvider, Message, MessageRole

# Main class
from pepperpy.pepperpy import PepperPy
from pepperpy.rag.base import Document, RAGProvider
from pepperpy.rag.types import Query
from pepperpy.storage.base import StorageProvider
from pepperpy.tts.base import TTSProvider

__version__ = "0.1.0"
__all__ = [
    # Main class
    "PepperPy",
    # Core
    "Config",
    "BaseProvider",
    "HTTPClient",
    "HTTPResponse",
    # Errors
    "PepperpyError",
    "ValidationError",
    "ConfigurationError",
    "HTTPError",
    "RequestError",
    "ResponseError",
    "ConnectionError",
    "TimeoutError",
    # Provider interfaces
    "LLMProvider",
    "RAGProvider",
    "StorageProvider",
    "EmbeddingProvider",
    "WorkflowProvider",
    "TTSProvider",
    # Common types
    "Document",
    "SearchResult",
    "GenerationResult",
    "Message",
    "MessageRole",
    "Query",
    "Metadata",
    "JsonValue",
    "JsonDict",
    "JsonType",
    "ConfigType",
    "HeadersType",
    "QueryParamsType",
]
