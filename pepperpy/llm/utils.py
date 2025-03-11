"""Utility functions for LLM module.

This module provides utility functions for working with LLMs, including token
manipulation, prompt formatting, and response processing.
"""

import asyncio
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Coroutine, Dict, List, Optional, TypeVar, Union

from pepperpy.errors import PepperpyError
from pepperpy.errors.core import PepperPyError
from pepperpy.utils.logging import get_logger

# Logger for this module
logger = get_logger(__name__)

T = TypeVar("T")


class RateLimiter:
    """Rate limiter for API calls."""

    def __init__(self, requests_per_minute: int = 60):
        """Initialize the rate limiter.

        Args:
            requests_per_minute: Maximum number of requests per minute
        """
        self.requests_per_minute = requests_per_minute
        self.interval = 60.0 / requests_per_minute
        self.last_request = 0.0
        self._lock = asyncio.Lock()

    async def acquire(self):
        """Acquire a rate limit token."""
        async with self._lock:
            now = time.time()
            time_since_last = now - self.last_request
            if time_since_last < self.interval:
                wait_time = self.interval - time_since_last
                await asyncio.sleep(wait_time)
            self.last_request = time.time()

    async def __aenter__(self):
        """Enter the context manager."""
        await self.acquire()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit the context manager."""
        pass


def retry(
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exceptions: tuple = (PepperpyError,),
) -> Callable[
    [Callable[..., Coroutine[Any, Any, T]]], Callable[..., Coroutine[Any, Any, T]]
]:
    """Retry decorator with exponential backoff.

    Args:
        max_retries: Maximum number of retries
        base_delay: Base delay between retries in seconds
        max_delay: Maximum delay between retries in seconds
        exceptions: Tuple of exceptions to catch

    Returns:
        Decorated function
    """

    def decorator(
        func: Callable[..., Coroutine[Any, Any, T]],
    ) -> Callable[..., Coroutine[Any, Any, T]]:
        async def wrapper(*args: Any, **kwargs: Any) -> T:
            last_exception = None
            for attempt in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt == max_retries:
                        raise
                    delay = min(base_delay * (2**attempt), max_delay)
                    await asyncio.sleep(delay)
            raise last_exception  # type: ignore

        return wrapper

    return decorator


@dataclass
class Message:
    """A message in a conversation.

    Attributes:
        role: The role of the message sender (system, user, assistant)
        content: The content of the message
        name: Optional name of the message sender
    """

    role: str
    content: str
    name: Optional[str] = None


@dataclass
class Prompt:
    """A prompt to be sent to an LLM.

    Attributes:
        messages: The messages in the conversation
        temperature: Controls randomness in the response (0.0 to 2.0)
        max_tokens: Maximum number of tokens to generate
        stop: Optional list of strings that will stop generation
        metadata: Additional metadata about the prompt
    """

    messages: List[Message]
    temperature: float = 1.0
    max_tokens: Optional[int] = None
    stop: Optional[List[str]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Response:
    """A response from an LLM.

    Attributes:
        text: The generated text
        usage: Token usage information
        metadata: Additional metadata about the response
    """

    text: str
    usage: Dict[str, int]
    metadata: Dict[str, Any] = field(default_factory=dict)


def validate_prompt(prompt: Union[str, Prompt]) -> Prompt:
    """Validate and normalize a prompt.

    Args:
        prompt: The prompt to validate

    Returns:
        The validated and normalized prompt

    Raises:
        PepperPyError: If the prompt is invalid
    """
    if isinstance(prompt, str):
        # Convert string to Prompt object
        return Prompt(messages=[Message(role="user", content=prompt)])
    elif isinstance(prompt, Prompt):
        # Validate the prompt object
        if not prompt.messages:
            raise PepperPyError("Prompt must have at least one message")

        # Validate temperature
        if not 0.0 <= prompt.temperature <= 2.0:
            raise PepperPyError("Temperature must be between 0.0 and 2.0")

        # Validate max_tokens
        if prompt.max_tokens is not None and prompt.max_tokens <= 0:
            raise PepperPyError("Max tokens must be positive")

        return prompt
    else:
        raise PepperPyError(f"Invalid prompt type: {type(prompt)}")


def get_system_message(messages: List[Message]) -> Optional[str]:
    """Get the system message from a list of messages.

    Args:
        messages: The messages to search

    Returns:
        The system message content, or None if not found
    """
    for message in messages:
        if message.role == "system":
            return message.content
    return None


def convert_messages_to_text(messages: List[Message], format: str = "default") -> str:
    """Convert messages to a text format.

    Args:
        messages: The messages to convert
        format: The format to use (default, chat, minimal)

    Returns:
        The messages as formatted text
    """
    if format == "chat":
        # Chat format with role labels
        prompt_text = ""
        for message in messages:
            role = message.role.capitalize()
            if message.name:
                role = f"{role} ({message.name})"
            prompt_text += f"{role}: {message.content}\n"
        return prompt_text.strip()

    elif format == "minimal":
        # Minimal format without roles
        return "\n".join(message.content for message in messages)

    else:
        # Default format with role markers
        prompt_text = ""
        for message in messages:
            role = message.role
            content = message.content

            if role == "system":
                prompt_text += f"<|system|>\n{content}\n"
            elif role == "user":
                prompt_text += f"<|user|>\n{content}\n"
            elif role == "assistant":
                prompt_text += f"<|assistant|>\n{content}\n"
            else:
                # Skip unknown roles
                logger.warning(f"Skipping message with unknown role: {role}")
                continue

        # Add the final assistant prompt if needed
        if not prompt_text.endswith("<|assistant|>\n"):
            prompt_text += "<|assistant|>\n"

        return prompt_text


def format_prompt_for_provider(prompt: Prompt, provider: str) -> Dict[str, Any]:
    """Format a prompt for a specific provider.

    Args:
        prompt: The prompt to format
        provider: The provider to format for (openai, anthropic, local)

    Returns:
        The formatted prompt parameters

    Raises:
        PepperPyError: If the provider is not supported
    """
    if provider == "openai":
        # OpenAI format
        params = {
            "messages": [
                {
                    "role": message.role,
                    "content": message.content,
                    **({"name": message.name} if message.name else {}),
                }
                for message in prompt.messages
            ],
            "temperature": prompt.temperature,
        }

    elif provider == "anthropic":
        # Anthropic format
        params = {
            "messages": [
                {
                    "role": "user" if message.role == "user" else "assistant",
                    "content": message.content,
                }
                for message in prompt.messages
                if message.role != "system"
            ],
            "temperature": prompt.temperature,
        }

        # Add system message if present
        system_message = get_system_message(prompt.messages)
        if system_message:
            params["system"] = system_message

    elif provider == "local":
        # Local format (text-based)
        params = {
            "prompt": convert_messages_to_text(prompt.messages),
            "temperature": prompt.temperature,
        }

    else:
        raise PepperPyError(f"Unsupported provider: {provider}")

    # Add common optional parameters
    if prompt.max_tokens is not None:
        params["max_tokens"] = prompt.max_tokens

    if prompt.stop is not None:
        if provider == "anthropic":
            params["stop_sequences"] = prompt.stop
        else:
            params["stop"] = prompt.stop

    return params


def calculate_token_usage(
    prompt_text: str,
    completion_text: str,
    provider: str,
    model: str,
) -> Dict[str, int]:
    """Calculate token usage for a prompt and completion.

    Args:
        prompt_text: The prompt text
        completion_text: The completion text
        provider: The provider name
        model: The model name

    Returns:
        A dictionary with token usage information

    Raises:
        PepperPyError: If token counting fails
    """
    try:
        if provider == "openai":
            import tiktoken

            # Get the encoding for the model
            encoding = tiktoken.encoding_for_model(model)

            # Count tokens
            prompt_tokens = len(encoding.encode(prompt_text))
            completion_tokens = len(encoding.encode(completion_text))

        elif provider == "anthropic":
            # Use Anthropic's token counting endpoint
            # This should be implemented by the provider
            raise PepperPyError("Token counting not implemented for Anthropic")

        elif provider == "local":
            # Use the local model's tokenizer
            # This should be implemented by the provider
            raise PepperPyError("Token counting not implemented for local models")

        else:
            raise PepperPyError(f"Unsupported provider: {provider}")

        return {
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": prompt_tokens + completion_tokens,
        }

    except Exception as e:
        raise PepperPyError(f"Error calculating token usage: {e}")


def truncate_prompt(
    prompt: Prompt,
    max_tokens: int,
    provider: str,
    model: str,
    keep_system_message: bool = True,
) -> Prompt:
    """Truncate a prompt to fit within a token limit.

    Args:
        prompt: The prompt to truncate
        max_tokens: The maximum number of tokens allowed
        provider: The provider name
        model: The model name
        keep_system_message: Whether to preserve system messages during truncation

    Returns:
        The truncated prompt

    Raises:
        PepperPyError: If truncation fails
    """
    try:
        # Convert prompt to text
        prompt_text = convert_messages_to_text(prompt.messages)

        # Calculate current token count
        usage = calculate_token_usage(prompt_text, "", provider, model)
        current_tokens = usage["prompt_tokens"]

        if current_tokens <= max_tokens:
            return prompt

        # Truncate messages from oldest to newest
        truncated_messages = []
        remaining_tokens = max_tokens

        # If keeping system messages, calculate their tokens first
        system_messages = []
        if keep_system_message:
            for message in prompt.messages:
                if message.role == "system":
                    message_usage = calculate_token_usage(
                        message.content, "", provider, model
                    )
                    message_tokens = message_usage["prompt_tokens"]
                    if message_tokens <= remaining_tokens:
                        system_messages.append(message)
                        remaining_tokens -= message_tokens

        # Add non-system messages
        for message in reversed(prompt.messages):
            # Skip system messages if we're keeping them
            if keep_system_message and message.role == "system":
                continue

            # Calculate tokens for this message
            message_usage = calculate_token_usage(message.content, "", provider, model)
            message_tokens = message_usage["prompt_tokens"]

            if message_tokens <= remaining_tokens:
                truncated_messages.insert(0, message)
                remaining_tokens -= message_tokens
            else:
                # Skip if we can't fit at least a small part of the message
                if remaining_tokens < 10:
                    continue

                # Truncate the message content
                if provider == "openai":
                    import tiktoken

                    encoding = tiktoken.encoding_for_model(model)
                    tokens = encoding.encode(message.content)[:remaining_tokens]
                    content = encoding.decode(tokens)
                else:
                    # Simple character-based truncation as fallback
                    ratio = remaining_tokens / message_tokens
                    content = message.content[: int(len(message.content) * ratio)]

                truncated_messages.insert(
                    0,
                    Message(
                        role=message.role,
                        content=content,
                        name=message.name,
                    ),
                )
                break

        # Combine system messages and truncated messages
        final_messages = system_messages + truncated_messages

        return Prompt(
            messages=final_messages,
            temperature=prompt.temperature,
            max_tokens=prompt.max_tokens,
            stop=prompt.stop,
            metadata={**prompt.metadata, "truncated": True},
        )

    except Exception as e:
        raise PepperPyError(f"Error truncating prompt: {e}")


# Export all classes and functions
__all__ = [
    "Message",
    "Prompt",
    "Response",
    "RateLimiter",
    "retry",
    "validate_prompt",
    "get_system_message",
    "convert_messages_to_text",
    "format_prompt_for_provider",
    "calculate_token_usage",
    "truncate_prompt",
]
