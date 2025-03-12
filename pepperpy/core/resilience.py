"""Provider fallback and circuit breaker patterns for PepperPy.

This module provides resilience patterns for PepperPy providers, including
fallback mechanisms and circuit breakers. These patterns help ensure that
the system remains operational even when providers experience failures.
"""

import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from functools import wraps
from typing import Any, Callable, Dict, List, Optional, Type, TypeVar, cast

from pepperpy.core.telemetry import get_provider_telemetry

T = TypeVar("T")
F = TypeVar("F", bound=Callable[..., Any])

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    """States for the circuit breaker."""

    CLOSED = "closed"  # Normal operation, requests are allowed
    OPEN = "open"  # Failure threshold exceeded, requests are blocked
    HALF_OPEN = "half_open"  # Testing if the service has recovered


@dataclass
class CircuitBreakerConfig:
    """Configuration for a circuit breaker.

    This class defines the configuration for a circuit breaker, including
    failure thresholds, recovery timeouts, and retry policies.
    """

    # Number of failures required to open the circuit
    failure_threshold: int = 5
    # Time to wait before transitioning from OPEN to HALF_OPEN
    recovery_timeout: timedelta = timedelta(seconds=60)
    # Number of successful requests required to close the circuit
    success_threshold: int = 3
    # Maximum number of retries for a request
    max_retries: int = 3
    # Time to wait between retries
    retry_delay: timedelta = timedelta(seconds=1)
    # Whether to use exponential backoff for retries
    exponential_backoff: bool = True
    # Maximum delay between retries
    max_retry_delay: timedelta = timedelta(seconds=30)
    # Types of exceptions to consider as failures
    failure_exceptions: List[Type[Exception]] = field(default_factory=list)


class CircuitBreaker:
    """Circuit breaker for provider operations.

    This class implements the circuit breaker pattern, which prevents
    repeated calls to a failing service and allows it to recover.

    Example:
        ```python
        # Create a circuit breaker
        breaker = CircuitBreaker("openai")

        # Use the circuit breaker
        try:
            result = breaker.execute(lambda: make_api_call())
        except CircuitBreakerError:
            # Handle the error
            result = fallback_value
        ```
    """

    def __init__(self, provider_id: str, config: Optional[CircuitBreakerConfig] = None):
        """Initialize the circuit breaker.

        Args:
            provider_id: The ID of the provider.
            config: Optional configuration for the circuit breaker.
        """
        self.provider_id = provider_id
        self.config = config or CircuitBreakerConfig()
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.telemetry = get_provider_telemetry(provider_id)

    def execute(self, func: Callable[..., T], *args: Any, **kwargs: Any) -> T:
        """Execute a function with circuit breaker protection.

        This method executes a function with circuit breaker protection,
        preventing calls to the function if the circuit is open.

        Args:
            func: The function to execute.
            *args: Positional arguments to pass to the function.
            **kwargs: Keyword arguments to pass to the function.

        Returns:
            The result of the function.

        Raises:
            CircuitBreakerError: If the circuit is open or the function fails.
        """
        self._check_state()

        retries = 0
        while True:
            try:
                with self.telemetry.time("circuit_breaker.execution"):
                    result = func(*args, **kwargs)

                # If we get here, the function succeeded
                self._on_success()
                return result

            except Exception as e:
                # Check if this is a failure exception
                is_failure = not self.config.failure_exceptions or any(
                    isinstance(e, exc_type)
                    for exc_type in self.config.failure_exceptions
                )

                if is_failure:
                    self._on_failure(e)

                    # Check if we should retry
                    retries += 1
                    if retries <= self.config.max_retries:
                        # Calculate retry delay
                        delay = self._calculate_retry_delay(retries)
                        self.telemetry.info(
                            "circuit_breaker.retry",
                            f"Retrying after failure ({retries}/{self.config.max_retries})",
                            {"exception": str(e), "delay": delay.total_seconds()},
                        )
                        time.sleep(delay.total_seconds())
                        continue

                    # If we've exhausted retries, raise a circuit breaker error
                    raise CircuitBreakerError(
                        f"Circuit breaker for provider '{self.provider_id}' tripped: {e}"
                    ) from e
                else:
                    # If it's not a failure exception, re-raise it
                    raise

    def _check_state(self) -> None:
        """Check the current state of the circuit breaker.

        This method checks the current state of the circuit breaker and
        transitions between states as needed.

        Raises:
            CircuitBreakerError: If the circuit is open.
        """
        now = datetime.now()

        if self.state == CircuitState.OPEN:
            # Check if the recovery timeout has elapsed
            if (
                self.last_failure_time is not None
                and now - self.last_failure_time >= self.config.recovery_timeout
            ):
                self.state = CircuitState.HALF_OPEN
                self.telemetry.info(
                    "circuit_breaker.state_change",
                    f"Circuit breaker for provider '{self.provider_id}' transitioned from OPEN to HALF_OPEN",
                )
            else:
                # Circuit is still open, reject the request
                self.telemetry.warning(
                    "circuit_breaker.rejected",
                    f"Circuit breaker for provider '{self.provider_id}' rejected request (circuit OPEN)",
                )
                raise CircuitBreakerError(
                    f"Circuit breaker for provider '{self.provider_id}' is OPEN"
                )
        elif self.state == CircuitState.HALF_OPEN:
            # In HALF_OPEN state, we allow a limited number of requests through
            # to test if the service has recovered
            pass

    def _on_success(self) -> None:
        """Handle a successful operation.

        This method updates the circuit breaker state after a successful operation.
        """
        if self.state == CircuitState.HALF_OPEN:
            # In HALF_OPEN state, we're testing if the service has recovered
            self.success_count += 1
            if self.success_count >= self.config.success_threshold:
                # Service has recovered, close the circuit
                self.state = CircuitState.CLOSED
                self.failure_count = 0
                self.success_count = 0
                self.telemetry.info(
                    "circuit_breaker.state_change",
                    f"Circuit breaker for provider '{self.provider_id}' transitioned from HALF_OPEN to CLOSED",
                )
        elif self.state == CircuitState.CLOSED:
            # Reset failure count on success
            self.failure_count = 0

    def _on_failure(self, exception: Exception) -> None:
        """Handle a failed operation.

        This method updates the circuit breaker state after a failed operation.

        Args:
            exception: The exception that caused the failure.
        """
        now = datetime.now()
        self.last_failure_time = now

        if self.state == CircuitState.CLOSED:
            # In CLOSED state, we're tracking failures
            self.failure_count += 1
            if self.failure_count >= self.config.failure_threshold:
                # Failure threshold exceeded, open the circuit
                self.state = CircuitState.OPEN
                self.telemetry.error(
                    "circuit_breaker.state_change",
                    f"Circuit breaker for provider '{self.provider_id}' transitioned from CLOSED to OPEN",
                    {"exception": str(exception)},
                )
        elif self.state == CircuitState.HALF_OPEN:
            # In HALF_OPEN state, any failure opens the circuit again
            self.state = CircuitState.OPEN
            self.success_count = 0
            self.telemetry.error(
                "circuit_breaker.state_change",
                f"Circuit breaker for provider '{self.provider_id}' transitioned from HALF_OPEN to OPEN",
                {"exception": str(exception)},
            )

    def _calculate_retry_delay(self, retry_count: int) -> timedelta:
        """Calculate the delay before the next retry.

        Args:
            retry_count: The current retry count.

        Returns:
            The delay before the next retry.
        """
        if self.config.exponential_backoff:
            # Use exponential backoff
            delay_seconds = self.config.retry_delay.total_seconds() * (
                2 ** (retry_count - 1)
            )
            # Add jitter to avoid thundering herd problem
            delay_seconds = delay_seconds * (
                0.5 + 0.5 * (hash(str(time.time())) % 1000) / 1000
            )
            # Cap at max retry delay
            delay_seconds = min(
                delay_seconds, self.config.max_retry_delay.total_seconds()
            )
            return timedelta(seconds=delay_seconds)
        else:
            # Use fixed delay
            return self.config.retry_delay

    def reset(self) -> None:
        """Reset the circuit breaker to its initial state."""
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None
        self.telemetry.info(
            "circuit_breaker.reset",
            f"Circuit breaker for provider '{self.provider_id}' reset to initial state",
        )


class CircuitBreakerError(Exception):
    """Exception raised when a circuit breaker prevents an operation."""

    pass


class ProviderFallback:
    """Fallback mechanism for provider operations.

    This class implements a fallback mechanism for provider operations,
    allowing operations to be retried with alternative providers if the
    primary provider fails.

    Example:
        ```python
        # Create a fallback mechanism
        fallback = ProviderFallback("openai", ["anthropic", "cohere"])

        # Use the fallback mechanism
        result = fallback.execute(lambda provider: make_api_call(provider))
        ```
    """

    def __init__(
        self,
        primary_provider_id: str,
        fallback_provider_ids: List[str],
        circuit_breaker_config: Optional[CircuitBreakerConfig] = None,
    ):
        """Initialize the fallback mechanism.

        Args:
            primary_provider_id: The ID of the primary provider.
            fallback_provider_ids: The IDs of the fallback providers, in order of preference.
            circuit_breaker_config: Optional configuration for circuit breakers.
        """
        self.primary_provider_id = primary_provider_id
        self.fallback_provider_ids = fallback_provider_ids
        self.circuit_breaker_config = circuit_breaker_config or CircuitBreakerConfig()
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        self.telemetry = get_provider_telemetry(primary_provider_id)

        # Create circuit breakers for all providers
        self._create_circuit_breaker(primary_provider_id)
        for provider_id in fallback_provider_ids:
            self._create_circuit_breaker(provider_id)

    def _create_circuit_breaker(self, provider_id: str) -> CircuitBreaker:
        """Create a circuit breaker for a provider.

        Args:
            provider_id: The ID of the provider.

        Returns:
            The circuit breaker for the provider.
        """
        if provider_id not in self.circuit_breakers:
            self.circuit_breakers[provider_id] = CircuitBreaker(
                provider_id, self.circuit_breaker_config
            )
        return self.circuit_breakers[provider_id]

    def execute(
        self, func: Callable[[str], T], fallback_func: Optional[Callable[[], T]] = None
    ) -> T:
        """Execute a function with fallback protection.

        This method executes a function with the primary provider, falling back
        to alternative providers if the primary provider fails.

        Args:
            func: The function to execute, which takes a provider ID as its argument.
            fallback_func: Optional function to call if all providers fail.

        Returns:
            The result of the function.

        Raises:
            ProviderFallbackError: If all providers fail and no fallback function is provided.
        """
        # Try the primary provider first
        primary_provider_id = self.primary_provider_id
        primary_breaker = self.circuit_breakers[primary_provider_id]

        try:
            with self.telemetry.time("fallback.primary_execution"):
                return primary_breaker.execute(func, primary_provider_id)
        except CircuitBreakerError as e:
            self.telemetry.warning(
                "fallback.primary_failure",
                f"Primary provider '{primary_provider_id}' failed, trying fallbacks",
                {"exception": str(e)},
            )

            # Try fallback providers in order
            for provider_id in self.fallback_provider_ids:
                breaker = self.circuit_breakers[provider_id]
                try:
                    with self.telemetry.time(f"fallback.{provider_id}_execution"):
                        result = breaker.execute(func, provider_id)
                    self.telemetry.info(
                        "fallback.success",
                        f"Fallback to provider '{provider_id}' succeeded",
                    )
                    return result
                except CircuitBreakerError as e:
                    self.telemetry.warning(
                        "fallback.failure",
                        f"Fallback to provider '{provider_id}' failed",
                        {"exception": str(e)},
                    )
                    continue

            # If we get here, all providers failed
            if fallback_func is not None:
                self.telemetry.warning(
                    "fallback.using_fallback_function",
                    "All providers failed, using fallback function",
                )
                return fallback_func()
            else:
                self.telemetry.error(
                    "fallback.all_failed",
                    "All providers failed and no fallback function provided",
                )
                raise ProviderFallbackError(
                    f"All providers failed: primary={primary_provider_id}, fallbacks={self.fallback_provider_ids}"
                )


class ProviderFallbackError(Exception):
    """Exception raised when all providers in a fallback chain fail."""

    pass


def with_circuit_breaker(
    provider_id: str, config: Optional[CircuitBreakerConfig] = None
) -> Callable[[F], F]:
    """Decorator for applying circuit breaker protection to a function.

    This decorator applies circuit breaker protection to a function,
    preventing calls to the function if the circuit is open.

    Example:
        ```python
        @with_circuit_breaker("openai")
        def make_api_call():
            # Make API call
            return response
        ```

    Args:
        provider_id: The ID of the provider.
        config: Optional configuration for the circuit breaker.

    Returns:
        A decorator that applies circuit breaker protection to a function.
    """
    breaker = CircuitBreaker(provider_id, config)

    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            return breaker.execute(func, *args, **kwargs)

        return cast(F, wrapper)

    return decorator


def with_fallback(
    primary_provider_id: str,
    fallback_provider_ids: List[str],
    circuit_breaker_config: Optional[CircuitBreakerConfig] = None,
) -> Callable[[Callable[[str], T]], Callable[[], T]]:
    """Decorator for applying fallback protection to a function.

    This decorator applies fallback protection to a function, retrying
    the function with alternative providers if the primary provider fails.

    Example:
        ```python
        @with_fallback("openai", ["anthropic", "cohere"])
        def make_api_call(provider_id):
            # Make API call using the specified provider
            return response
        ```

    Args:
        primary_provider_id: The ID of the primary provider.
        fallback_provider_ids: The IDs of the fallback providers, in order of preference.
        circuit_breaker_config: Optional configuration for circuit breakers.

    Returns:
        A decorator that applies fallback protection to a function.
    """
    fallback = ProviderFallback(
        primary_provider_id, fallback_provider_ids, circuit_breaker_config
    )

    def decorator(func: Callable[[str], T]) -> Callable[[], T]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            return fallback.execute(func)

        return cast(Callable[[], T], wrapper)

    return decorator


# Registry for circuit breakers
_circuit_breakers: Dict[str, CircuitBreaker] = {}


def get_circuit_breaker(
    provider_id: str, config: Optional[CircuitBreakerConfig] = None
) -> CircuitBreaker:
    """Get a circuit breaker for a provider.

    This function returns a circuit breaker for the specified provider,
    creating one if it doesn't exist.

    Args:
        provider_id: The ID of the provider.
        config: Optional configuration for the circuit breaker.

    Returns:
        A circuit breaker for the provider.
    """
    if provider_id not in _circuit_breakers:
        _circuit_breakers[provider_id] = CircuitBreaker(provider_id, config)
    return _circuit_breakers[provider_id]


def reset_circuit_breaker(provider_id: str) -> None:
    """Reset a circuit breaker for a provider.

    This function resets the circuit breaker for the specified provider,
    returning it to its initial state.

    Args:
        provider_id: The ID of the provider.
    """
    if provider_id in _circuit_breakers:
        _circuit_breakers[provider_id].reset()


def reset_all_circuit_breakers() -> None:
    """Reset all circuit breakers.

    This function resets all circuit breakers, returning them to their
    initial state.
    """
    for breaker in _circuit_breakers.values():
        breaker.reset()


# Registry for fallback mechanisms
_fallbacks: Dict[str, ProviderFallback] = {}


def get_fallback(
    primary_provider_id: str,
    fallback_provider_ids: List[str],
    circuit_breaker_config: Optional[CircuitBreakerConfig] = None,
) -> ProviderFallback:
    """Get a fallback mechanism for a provider.

    This function returns a fallback mechanism for the specified provider,
    creating one if it doesn't exist.

    Args:
        primary_provider_id: The ID of the primary provider.
        fallback_provider_ids: The IDs of the fallback providers, in order of preference.
        circuit_breaker_config: Optional configuration for circuit breakers.

    Returns:
        A fallback mechanism for the provider.
    """
    key = f"{primary_provider_id}:{','.join(fallback_provider_ids)}"
    if key not in _fallbacks:
        _fallbacks[key] = ProviderFallback(
            primary_provider_id, fallback_provider_ids, circuit_breaker_config
        )
    return _fallbacks[key]
