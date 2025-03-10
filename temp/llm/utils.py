"""Utility functions for the LLM module.

This module provides utility functions for working with LLMs, including
tokenization, rate limiting, retry logic, and validation.
"""

import asyncio
import time
from functools import wraps
from typing import Any, Awaitable, Callable, Dict, List, Optional, TypeVar, Union

from pepperpy.llm.errors import (
    LLMError,
    LLMRateLimitError,
    LLMTimeoutError,
)
from pepperpy.utils.logging import get_logger

# Logger for this module
logger = get_logger(__name__)

# Type variable for retry decorator
T = TypeVar("T")
R = TypeVar("R")


class RateLimiter:
    """Rate limiter for LLM API calls.

    This class implements a token bucket algorithm for rate limiting.
    """

    def __init__(self, rate: float, burst: int):
        """Initialize a rate limiter.

        Args:
            rate: The rate at which tokens are added to the bucket (tokens/second)
            burst: The maximum number of tokens that can be stored
        """
        self.rate = rate
        self.burst = burst
        self.tokens = burst
        self.last_update = time.monotonic()
        self._lock = asyncio.Lock()

    async def acquire(self, tokens: int = 1) -> None:
        """Acquire tokens from the bucket.

        Args:
            tokens: The number of tokens to acquire

        Raises:
            LLMRateLimitError: If there are not enough tokens available
        """
        async with self._lock:
            # Update the number of tokens
            now = time.monotonic()
            elapsed = now - self.last_update
            self.tokens = min(self.burst, self.tokens + elapsed * self.rate)
            self.last_update = now

            # Check if there are enough tokens
            if tokens > self.tokens:
                wait_time = (tokens - self.tokens) / self.rate
                raise LLMRateLimitError(
                    "Rate limit exceeded",
                    retry_after=int(wait_time),
                )

            # Consume tokens
            self.tokens -= tokens


def retry(
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exceptions: tuple = (LLMError,),
) -> Callable[[Callable[..., Awaitable[T]]], Callable[..., Awaitable[T]]]:
    """Decorator for retrying failed LLM API calls.

    Args:
        max_retries: Maximum number of retries
        base_delay: Base delay between retries (seconds)
        max_delay: Maximum delay between retries (seconds)
        exceptions: Tuple of exceptions to catch

    Returns:
        A decorator function
    """

    def decorator(func: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T]]:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> T:
            last_error = None

            for attempt in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_error = e

                    # Don't retry if we've reached the maximum
                    if attempt == max_retries:
                        break

                    # Calculate delay with exponential backoff
                    delay = min(base_delay * (2**attempt), max_delay)

                    # If it's a rate limit error with retry_after, use that
                    if isinstance(e, LLMRateLimitError) and e.retry_after is not None:
                        delay = e.retry_after

                    # Log the error and wait
                    logger.warning(
                        f"Attempt {attempt + 1}/{max_retries + 1} failed: {e}. "
                        f"Retrying in {delay:.1f} seconds..."
                    )

                    await asyncio.sleep(delay)

            # If we get here, we've exhausted our retries
            raise last_error or LLMError("Maximum retries exceeded")

        return wrapper

    return decorator


# Define Message and Prompt classes here to avoid circular imports
class Message:
    """A message in a conversation with an LLM.

    Attributes:
        role: The role of the message sender (e.g., "system", "user", "assistant")
        content: The content of the message
        name: Optional name of the sender
        metadata: Additional metadata about the message
    """

    def __init__(
        self,
        role: str,
        content: str,
        name: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        self.role = role
        self.content = content
        self.name = name
        self.metadata = metadata or {}


class Prompt:
    """A prompt to be sent to an LLM.

    Attributes:
        messages: The messages in the conversation
        temperature: Controls randomness in the response (0.0 to 2.0)
        max_tokens: Maximum number of tokens to generate
        stop: Optional list of strings that will stop generation
        metadata: Additional metadata about the prompt
    """

    def __init__(
        self,
        messages: List[Message],
        temperature: float = 1.0,
        max_tokens: Optional[int] = None,
        stop: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        self.messages = messages
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.stop = stop
        self.metadata = metadata or {}


def validate_prompt(prompt: Union[str, Prompt]) -> Prompt:
    """Validate and normalize a prompt.

    Args:
        prompt: The prompt to validate

    Returns:
        A normalized Prompt object

    Raises:
        ValueError: If the prompt is invalid
    """
    if isinstance(prompt, str):
        return Prompt(messages=[Message(role="user", content=prompt)])

    if not prompt.messages:
        raise ValueError("Prompt must have at least one message")

    return prompt


def validate_temperature(temperature: float) -> None:
    """Validate a temperature value.

    Args:
        temperature: The temperature value to validate

    Raises:
        ValueError: If the temperature is invalid
    """
    if not 0.0 <= temperature <= 2.0:
        raise ValueError("Temperature must be between 0.0 and 2.0")


def validate_max_tokens(max_tokens: Optional[int]) -> None:
    """Validate a max_tokens value.

    Args:
        max_tokens: The max_tokens value to validate

    Raises:
        ValueError: If max_tokens is invalid
    """
    if max_tokens is not None and max_tokens <= 0:
        raise ValueError("max_tokens must be positive")


def validate_stop_sequences(stop: Optional[List[str]]) -> None:
    """Validate stop sequences.

    Args:
        stop: The stop sequences to validate

    Raises:
        ValueError: If any stop sequence is invalid
    """
    if stop is not None:
        if not all(isinstance(s, str) and s for s in stop):
            raise ValueError("Stop sequences must be non-empty strings")


def validate_metadata(metadata: Dict[str, Any]) -> None:
    """Validate metadata.

    Args:
        metadata: The metadata to validate

    Raises:
        ValueError: If the metadata is invalid
    """
    if not isinstance(metadata, dict):
        raise ValueError("Metadata must be a dictionary")

    # Ensure all keys are strings
    if not all(isinstance(k, str) for k in metadata):
        raise ValueError("Metadata keys must be strings")


async def with_timeout(
    coro: Callable[..., Awaitable[R]],
    timeout: float,
    *args: Any,
    **kwargs: Any,
) -> R:
    """Run a coroutine with a timeout.

    Args:
        coro: The coroutine to run
        timeout: The timeout in seconds
        *args: Positional arguments for the coroutine
        **kwargs: Keyword arguments for the coroutine

    Returns:
        The result of the coroutine

    Raises:
        LLMTimeoutError: If the coroutine times out
    """
    try:
        return await asyncio.wait_for(coro(*args, **kwargs), timeout=timeout)
    except asyncio.TimeoutError:
        raise LLMTimeoutError(
            f"Operation timed out after {timeout} seconds",
            timeout=timeout,
        )
