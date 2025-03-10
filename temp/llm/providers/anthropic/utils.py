"""Utility functions for the Anthropic provider.

This module provides utility functions specific to the Anthropic provider.
"""

from typing import Any, Dict, List, Optional

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


def convert_messages_to_anthropic_format(
    messages: List[Message],
) -> List[Dict[str, Any]]:
    """Convert PepperPy messages to Anthropic format.

    Args:
        messages: The messages to convert

    Returns:
        The messages in Anthropic format
    """
    anthropic_messages = []

    for message in messages:
        # Map PepperPy roles to Anthropic roles
        role = message.role
        if role == "user":
            role = "user"
        elif role == "assistant":
            role = "assistant"
        elif role == "system":
            # System messages are handled differently in Anthropic
            continue
        else:
            # Skip unknown roles
            logger.warning(f"Skipping message with unknown role: {role}")
            continue

        anthropic_messages.append({
            "role": role,
            "content": message.content,
        })

    return anthropic_messages


def get_system_message(messages: List[Message]) -> Optional[str]:
    """Extract the system message from a list of messages.

    Args:
        messages: The messages to extract from

    Returns:
        The system message, or None if there is no system message
    """
    for message in messages:
        if message.role == "system":
            return message.content

    return None


def convert_prompt_to_anthropic_params(prompt: Prompt) -> Dict[str, Any]:
    """Convert a PepperPy prompt to Anthropic API parameters.

    Args:
        prompt: The prompt to convert

    Returns:
        The Anthropic API parameters
    """
    params = {
        "messages": convert_messages_to_anthropic_format(prompt.messages),
        "temperature": prompt.temperature,
    }

    # Add system message if present
    system_message = get_system_message(prompt.messages)
    if system_message:
        params["system"] = system_message

    if prompt.max_tokens is not None:
        params["max_tokens"] = prompt.max_tokens

    if prompt.stop is not None:
        params["stop_sequences"] = prompt.stop

    return params


def handle_anthropic_error(error: Exception) -> None:
    """Handle an Anthropic API error.

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
            "Authentication error with Anthropic API: " + error_str,
            provider="anthropic",
            details=error_details,
        )
    elif status_code == 429:
        retry_after = response.headers.get("Retry-After") if response else None
        retry_after = (
            int(retry_after) if retry_after and retry_after.isdigit() else None
        )

        raise LLMRateLimitError(
            "Rate limit exceeded with Anthropic API: " + error_str,
            provider="anthropic",
            retry_after=retry_after,
            details=error_details,
        )
    elif status_code == 400:
        # Check for context length error
        if (
            "maximum context length" in error_str.lower()
            or "token limit" in error_str.lower()
        ):
            raise LLMContextLengthError(
                "Context length exceeded with Anthropic API: " + error_str,
                provider="anthropic",
                details=error_details,
            )
        else:
            raise LLMInvalidRequestError(
                "Invalid request to Anthropic API: " + error_str,
                provider="anthropic",
                details=error_details,
            )
    elif status_code:
        raise LLMAPIError(
            f"Anthropic API error (status {status_code}): " + error_str,
            provider="anthropic",
            status_code=status_code,
            details=error_details,
        )
    else:
        # Handle timeout errors
        if "timeout" in error_str.lower():
            raise LLMTimeoutError(
                "Timeout error with Anthropic API: " + error_str,
                provider="anthropic",
                details=error_details,
            )

        # Generic error
        raise LLMError(
            "Error with Anthropic API: " + error_str,
            provider="anthropic",
            details=error_details,
        )
