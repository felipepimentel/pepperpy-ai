"""LLM module for PepperPy.

This module provides functionality for language model operations, including
text generation and embeddings. It supports various language model providers
and offers consistent interfaces for working with them.

Example:
    >>> import pepperpy as pp
    >>> response = await pp.llm.generate("Tell me a joke about AI")
    >>> print(response)
    Why did the AI go to art school? Because it wanted to learn how to draw conclusions!
"""

from pepperpy.llm.embedding import (
    EmbeddingError,
    EmbeddingOptions,
    EmbeddingProvider,
    EmbeddingResult,
    embed,
    embed_batch,
)
from pepperpy.llm.embedding import (
    get_provider as get_embedding_provider,
)
from pepperpy.llm.embedding import (
    list_providers as list_embedding_providers,
)
from pepperpy.llm.embedding import (
    register_provider as register_embedding_provider,
)
from pepperpy.llm.interfaces import (
    LLMError,
    LLMProvider,
    Message,
    MessageRole,
    Response,
    StreamingResponse,
)
from pepperpy.llm.registry import (
    create_model,
    get_model,
    list_models,
    register_model,
)

__all__ = [
    # Core LLM interfaces
    "LLMProvider",
    "LLMError",
    "Message",
    "MessageRole",
    "Response",
    "StreamingResponse",
    # LLM Registry
    "create_model",
    "get_model",
    "list_models",
    "register_model",
    # Embedding functionality
    "embed",
    "embed_batch",
    "EmbeddingProvider",
    "EmbeddingOptions",
    "EmbeddingResult",
    "EmbeddingError",
    "get_embedding_provider",
    "list_embedding_providers",
    "register_embedding_provider",
]
