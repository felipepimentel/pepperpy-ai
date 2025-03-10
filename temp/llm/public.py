"""Public API for the LLM module.

This module provides the public API for working with Large Language Models,
including model management, provider registration, and a unified interface for
generating completions and embeddings.
"""

from pepperpy.llm.core import (
    LLMManager,
    complete,
    count_tokens,
    embed,
    get_llm_manager,
    stream_complete,
    tokenize,
)
from pepperpy.llm.errors import (
    LLMAPIError,
    LLMAuthenticationError,
    LLMConfigError,
    LLMContextLengthError,
    LLMError,
    LLMInvalidRequestError,
    LLMRateLimitError,
    LLMTimeoutError,
)
from pepperpy.llm.providers.base import LLMProvider, Response, StreamingResponse
from pepperpy.llm.utils import Message, Prompt, RateLimiter, retry, validate_prompt

# Define public API
__all__ = [
    # Core
    "LLMManager",
    "get_llm_manager",
    "complete",
    "stream_complete",
    "embed",
    "tokenize",
    "count_tokens",
    # Errors
    "LLMError",
    "LLMConfigError",
    "LLMAuthenticationError",
    "LLMRateLimitError",
    "LLMContextLengthError",
    "LLMInvalidRequestError",
    "LLMAPIError",
    "LLMTimeoutError",
    # Providers
    "LLMProvider",
    # Types
    "Message",
    "Prompt",
    "Response",
    "StreamingResponse",
    # Utils
    "RateLimiter",
    "retry",
    "validate_prompt",
]
