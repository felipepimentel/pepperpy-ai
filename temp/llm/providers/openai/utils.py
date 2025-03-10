"""Utility functions for the OpenAI provider.

This module provides utility functions specific to the OpenAI provider.
"""

from typing import Any, Dict, List

from pepperpy.llm.errors import (
    LLMAPIError,
    LLMAuthenticationError,
    LLMContextLengthError,
    LLMError,
    LLMInvalidRequestError,
    LLMRateLimitError,
    LLMTimeoutError,
)
from pepperpy.llm.utils import Message, Prompt
from pepperpy.utils.logging import get_logger

# Logger for this module
logger = get_logger(__name__)


def convert_messages_to_openai_format(messages: List[Message]) -> List[Dict[str, Any]]:
    """Convert PepperPy messages to OpenAI format.

    Args:
        messages: The messages to convert

    Returns:
        The messages in OpenAI format
    """
    return [
        {
            "role": message.role,
            "content": message.content,
            **({"name": message.name} if message.name else {}),
        }
        for message in messages
    ]


def convert_prompt_to_openai_params(prompt: Prompt) -> Dict[str, Any]:
    """Convert a PepperPy prompt to OpenAI API parameters.

    Args:
        prompt: The prompt to convert

    Returns:
        The OpenAI API parameters
    """
    params = {
        "messages": convert_messages_to_openai_format(prompt.messages),
        "temperature": prompt.temperature,
    }

    if prompt.max_tokens is not None:
        params["max_tokens"] = prompt.max_tokens

    if prompt.stop is not None:
        params["stop"] = prompt.stop

    return params


def handle_openai_error(error: Exception) -> None:
    """Handle an OpenAI API error.

    Args:
        error: The error to handle

    Raises:
        LLMError: A PepperPy LLM error
    """
    error_str = str(error)

    # Check if the error has a response attribute
    response = getattr(error, "response", None)
    status_code = getattr(response, "status_code", None)

    # Try to extract error details from the response
    error_details = {}
    if response is not None:
        try:
            error_json = response.json()
            error_details = error_json.get("error", {})
        except (ValueError, AttributeError):
            pass

    # Handle different error types
    if status_code == 401:
        raise LLMAuthenticationError(
            "Authentication error with OpenAI API: " + error_str,
            provider="openai",
            details=error_details,
        )
    elif status_code == 429:
        retry_after = response.headers.get("Retry-After") if response else None
        retry_after = (
            int(retry_after) if retry_after and retry_after.isdigit() else None
        )

        raise LLMRateLimitError(
            "Rate limit exceeded with OpenAI API: " + error_str,
            provider="openai",
            retry_after=retry_after,
            details=error_details,
        )
    elif status_code == 400:
        # Check for context length error
        if "maximum context length" in error_str.lower():
            raise LLMContextLengthError(
                "Context length exceeded with OpenAI API: " + error_str,
                provider="openai",
                details=error_details,
            )
        else:
            raise LLMInvalidRequestError(
                "Invalid request to OpenAI API: " + error_str,
                provider="openai",
                details=error_details,
            )
    elif status_code:
        raise LLMAPIError(
            f"OpenAI API error (status {status_code}): " + error_str,
            provider="openai",
            status_code=status_code,
            details=error_details,
        )
    else:
        # Handle timeout errors
        if "timeout" in error_str.lower():
            raise LLMTimeoutError(
                "Timeout error with OpenAI API: " + error_str,
                provider="openai",
                details=error_details,
            )

        # Generic error
        raise LLMError(
            "Error with OpenAI API: " + error_str,
            provider="openai",
            details=error_details,
        )
