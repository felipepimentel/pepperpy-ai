"""Retry mechanisms for workflow operations."""

from typing import TypeVar, Callable, Any, Optional, Type
import asyncio
from functools import wraps
import logging

T = TypeVar("T")
logger = logging.getLogger(__name__)

class RetryConfig:
    """Configuration for retry behavior."""
    
    def __init__(
        self,
        max_attempts: int = 3,
        initial_delay: float = 1.0,
        max_delay: float = 10.0,
        backoff_factor: float = 2.0,
        retry_exceptions: tuple[Type[Exception], ...] = (Exception,),
    ):
        self.max_attempts = max_attempts
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.backoff_factor = backoff_factor
        self.retry_exceptions = retry_exceptions

def with_retry(config: Optional[RetryConfig] = None) -> Callable:
    """Decorator for adding retry logic to async functions."""
    
    if config is None:
        config = RetryConfig()
    
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            attempt = 1
            delay = config.initial_delay
            
            while attempt <= config.max_attempts:
                try:
                    return await func(*args, **kwargs)
                except config.retry_exceptions as e:
                    if attempt == config.max_attempts:
                        logger.error(
                            f"Final retry attempt {attempt} failed for {func.__name__}: {e}"
                        )
                        raise
                    
                    logger.warning(
                        f"Attempt {attempt} failed for {func.__name__}, "
                        f"retrying in {delay:.1f}s: {e}"
                    )
                    
                    await asyncio.sleep(delay)
                    delay = min(delay * config.backoff_factor, config.max_delay)
                    attempt += 1
            
            raise RuntimeError("Should not reach here")  # pragma: no cover
        
        return wrapper
    
    return decorator

# Example usage:
"""
@with_retry(RetryConfig(
    max_attempts=3,
    retry_exceptions=(ConnectionError, TimeoutError)
))
async def fetch_data(url: str) -> dict:
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            return await response.json()
""" 