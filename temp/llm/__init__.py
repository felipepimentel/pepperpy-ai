"""LLM module for PepperPy.

This module provides integration with various Large Language Models (LLMs),
including OpenAI, Anthropic, and local models. It includes functionality for
prompt management, response handling, and error handling.
"""

# Import public API
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
from pepperpy.llm.utils import Message, Prompt, RateLimiter, retry, validate_prompt

# Define public API
__all__ = [
    # Errors
    "LLMError",
    "LLMConfigError",
    "LLMAuthenticationError",
    "LLMRateLimitError",
    "LLMContextLengthError",
    "LLMInvalidRequestError",
    "LLMAPIError",
    "LLMTimeoutError",
    # Utils
    "Message",
    "Prompt",
    "RateLimiter",
    "retry",
    "validate_prompt",
]
