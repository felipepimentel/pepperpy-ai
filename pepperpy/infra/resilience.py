"""Provider fallback and circuit breaker patterns for PepperPy.

This module provides resilience patterns for PepperPy providers, including
fallback mechanisms and circuit breakers. These patterns help ensure that
the system remains operational even when providers experience failures.
"""

import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from functools import wraps
from typing import Any, Callable, Dict, List, Optional, Type, TypeVar, cast

from pepperpy.infra.logging import get_logger
from pepperpy.infra.telemetry import EventLevel, get_provider_telemetry

T = TypeVar("T")
F = TypeVar("F", bound=Callable[..., Any])

logger = get_logger(__name__)


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


# Registry of circuit breakers
_circuit_breakers: Dict[str, "CircuitBreaker"] = {}
# Registry of provider fallbacks
_provider_fallbacks: Dict[str, "ProviderFallback"] = {}


class CircuitBreaker:
    """Circuit breaker for provider resilience.

    This class implements the circuit breaker pattern, which helps prevent
    cascading failures by stopping requests to a failing service until it
    recovers. It also provides retry functionality with exponential backoff.

    The circuit breaker has three states:
    - CLOSED: Normal operation, requests are allowed
    - OPEN: Failure threshold exceeded, requests are blocked
    - HALF_OPEN: Testing if the service has recovered

    Typical usage:
        breaker = CircuitBreaker("my_provider")
        try:
            result = breaker.execute(my_function, arg1, arg2, kwarg1=value1)
        except CircuitBreakerError:
            # Handle circuit breaker error
    """

    def __init__(self, provider_id: str, config: Optional[CircuitBreakerConfig] = None):
        """Initialize the circuit breaker.

        Args:
            provider_id: The ID of the provider
            config: The circuit breaker configuration
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

        This method executes the provided function with circuit breaker
        protection, including state checking and retry logic.

        Args:
            func: The function to execute
            *args: Positional arguments for the function
            **kwargs: Keyword arguments for the function

        Returns:
            The result of the function

        Raises:
            CircuitBreakerError: If the circuit is open or the function fails
                after all retries
        """
        self._check_state()

        if self.state == CircuitState.OPEN:
            self.telemetry.report_event(
                name="circuit_breaker_open",
                message=f"Circuit breaker for {self.provider_id} is open",
                level=EventLevel.WARNING,
            )
            raise CircuitBreakerError(f"Circuit breaker for {self.provider_id} is open")

        retry_count = 0
        last_exception: Optional[Exception] = None

        while retry_count <= self.config.max_retries:
            try:
                result = func(*args, **kwargs)
                self._on_success()
                return result
            except Exception as e:
                last_exception = e
                if self.config.failure_exceptions and not any(
                    isinstance(e, exc_type)
                    for exc_type in self.config.failure_exceptions
                ):
                    # If the exception is not in the list of failure exceptions, re-raise it
                    raise

                self._on_failure(e)
                retry_count += 1

                if retry_count <= self.config.max_retries:
                    retry_delay = self._calculate_retry_delay(retry_count)
                    logger.warning(
                        f"Request to {self.provider_id} failed, retrying in {retry_delay.total_seconds()} seconds "
                        f"(retry {retry_count}/{self.config.max_retries})"
                    )
                    time.sleep(retry_delay.total_seconds())

        if last_exception:
            raise CircuitBreakerError(
                f"Circuit breaker for {self.provider_id} failed after {retry_count} retries"
            ) from last_exception

        # This should never happen, but added to satisfy the type checker
        raise CircuitBreakerError(
            f"Circuit breaker for {self.provider_id} failed unexpectedly"
        )

    def _check_state(self) -> None:
        """Check and potentially update the circuit breaker state.

        This method checks the current state of the circuit breaker and
        updates it if necessary, based on the recovery timeout.
        """
        if self.state == CircuitState.OPEN and self.last_failure_time:
            # Check if recovery timeout has elapsed
            elapsed = datetime.now() - self.last_failure_time
            if elapsed >= self.config.recovery_timeout:
                logger.info(
                    f"Circuit breaker for {self.provider_id} transitioning from OPEN to HALF_OPEN "
                    f"after {elapsed.total_seconds()} seconds"
                )
                self.state = CircuitState.HALF_OPEN
                self.success_count = 0
                self.telemetry.report_event(
                    name="circuit_breaker_half_open",
                    message=f"Circuit breaker for {self.provider_id} is half open",
                    level=EventLevel.INFO,
                )

    def _on_success(self) -> None:
        """Handle a successful request.

        This method updates the circuit breaker state after a successful request.
        """
        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= self.config.success_threshold:
                logger.info(
                    f"Circuit breaker for {self.provider_id} transitioning from HALF_OPEN to CLOSED "
                    f"after {self.success_count} successful requests"
                )
                self.state = CircuitState.CLOSED
                self.failure_count = 0
                self.telemetry.report_event(
                    name="circuit_breaker_closed",
                    message=f"Circuit breaker for {self.provider_id} is closed",
                    level=EventLevel.INFO,
                )
        elif self.state == CircuitState.CLOSED:
            # Reset failure count on success
            self.failure_count = 0

    def _on_failure(self, exception: Exception) -> None:
        """Handle a failed request.

        This method updates the circuit breaker state after a failed request.

        Args:
            exception: The exception that caused the failure
        """
        self.last_failure_time = datetime.now()

        if self.state == CircuitState.CLOSED:
            self.failure_count += 1
            if self.failure_count >= self.config.failure_threshold:
                logger.warning(
                    f"Circuit breaker for {self.provider_id} transitioning from CLOSED to OPEN "
                    f"after {self.failure_count} failures"
                )
                self.state = CircuitState.OPEN
                self.telemetry.report_event(
                    name="circuit_breaker_open",
                    message=f"Circuit breaker for {self.provider_id} is open",
                    level=EventLevel.WARNING,
                    tags={"exception": str(exception)},
                )
        elif self.state == CircuitState.HALF_OPEN:
            logger.warning(
                f"Circuit breaker for {self.provider_id} transitioning from HALF_OPEN to OPEN "
                f"after a failure"
            )
            self.state = CircuitState.OPEN
            self.telemetry.report_event(
                name="circuit_breaker_open",
                message=f"Circuit breaker for {self.provider_id} is open",
                level=EventLevel.WARNING,
                tags={"exception": str(exception)},
            )

    def _calculate_retry_delay(self, retry_count: int) -> timedelta:
        """Calculate the delay before the next retry.

        This method calculates the delay before the next retry, using
        exponential backoff if configured.

        Args:
            retry_count: The current retry count

        Returns:
            The delay before the next retry
        """
        if not self.config.exponential_backoff:
            return self.config.retry_delay

        # Calculate exponential backoff
        delay_seconds = self.config.retry_delay.total_seconds() * (
            2 ** (retry_count - 1)
        )
        # Apply jitter (±10%)
        jitter = delay_seconds * 0.1 * (2 * (time.time() % 1) - 1)
        delay_seconds = delay_seconds + jitter
        # Cap at max_retry_delay
        max_delay_seconds = self.config.max_retry_delay.total_seconds()
        delay_seconds = min(delay_seconds, max_delay_seconds)

        return timedelta(seconds=delay_seconds)

    def reset(self) -> None:
        """Reset the circuit breaker to its initial state.

        This method resets the circuit breaker to its initial state,
        clearing all failure and success counts.
        """
        logger.info(f"Resetting circuit breaker for {self.provider_id}")
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None


class CircuitBreakerError(Exception):
    """Exception raised when a circuit breaker prevents a request."""

    pass


class ProviderFallback:
    """Provider fallback mechanism.

    This class implements a fallback mechanism for providers, allowing
    requests to be redirected to fallback providers when the primary
    provider fails.

    Typical usage:
        fallback = ProviderFallback("primary_provider", ["fallback1", "fallback2"])
        result = fallback.execute(lambda provider_id: make_request(provider_id))
    """

    def __init__(
        self,
        primary_provider_id: str,
        fallback_provider_ids: List[str],
        circuit_breaker_config: Optional[CircuitBreakerConfig] = None,
    ):
        """Initialize the provider fallback.

        Args:
            primary_provider_id: The ID of the primary provider
            fallback_provider_ids: The IDs of the fallback providers
            circuit_breaker_config: The circuit breaker configuration
        """
        self.primary_provider_id = primary_provider_id
        self.fallback_provider_ids = fallback_provider_ids
        self.circuit_breaker_config = circuit_breaker_config
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}

        # Create circuit breakers for all providers
        self.circuit_breakers[primary_provider_id] = self._create_circuit_breaker(
            primary_provider_id
        )
        for provider_id in fallback_provider_ids:
            self.circuit_breakers[provider_id] = self._create_circuit_breaker(
                provider_id
            )

    def _create_circuit_breaker(self, provider_id: str) -> CircuitBreaker:
        """Create a circuit breaker for a provider.

        Args:
            provider_id: The ID of the provider

        Returns:
            The circuit breaker for the provider
        """
        # Check if a circuit breaker already exists for this provider
        if provider_id in _circuit_breakers:
            return _circuit_breakers[provider_id]

        # Create a new circuit breaker
        breaker = CircuitBreaker(provider_id, self.circuit_breaker_config)
        _circuit_breakers[provider_id] = breaker
        return breaker

    def execute(
        self, func: Callable[[str], T], fallback_func: Optional[Callable[[], T]] = None
    ) -> T:
        """Execute a function with fallback providers.

        This method executes the provided function with the primary provider,
        falling back to the fallback providers if the primary provider fails.

        Args:
            func: The function to execute, which takes a provider ID as its argument
            fallback_func: A function to execute if all providers fail

        Returns:
            The result of the function

        Raises:
            ProviderFallbackError: If all providers fail and no fallback function is provided
        """
        # Try the primary provider first
        primary_breaker = self.circuit_breakers[self.primary_provider_id]
        try:
            return primary_breaker.execute(func, self.primary_provider_id)
        except CircuitBreakerError as e:
            logger.warning(
                f"Primary provider {self.primary_provider_id} failed: {str(e)}"
            )

        # Try fallback providers
        for provider_id in self.fallback_provider_ids:
            breaker = self.circuit_breakers[provider_id]
            try:
                result = breaker.execute(func, provider_id)
                logger.info(
                    f"Successfully fell back to provider {provider_id} after primary provider failure"
                )
                return result
            except CircuitBreakerError as e:
                logger.warning(f"Fallback provider {provider_id} failed: {str(e)}")

        # If all providers failed and a fallback function is provided, use it
        if fallback_func:
            logger.warning("All providers failed, using fallback function")
            return fallback_func()

        # If all providers failed and no fallback function is provided, raise an error
        raise ProviderFallbackError(
            f"All providers failed: primary={self.primary_provider_id}, "
            f"fallbacks={self.fallback_provider_ids}"
        )


class ProviderFallbackError(Exception):
    """Exception raised when all providers in a fallback chain fail."""

    pass


def with_circuit_breaker(
    provider_id: str, config: Optional[CircuitBreakerConfig] = None
) -> Callable[[F], F]:
    """Decorator for applying circuit breaker to a function.

    This decorator applies a circuit breaker to a function, providing
    resilience against failures.

    Args:
        provider_id: The ID of the provider
        config: The circuit breaker configuration

    Returns:
        A decorator function
    """
    breaker = get_circuit_breaker(provider_id, config)

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
    """Decorator for applying provider fallback to a function.

    This decorator applies provider fallback to a function, allowing
    requests to be redirected to fallback providers when the primary
    provider fails.

    Args:
        primary_provider_id: The ID of the primary provider
        fallback_provider_ids: The IDs of the fallback providers
        circuit_breaker_config: The circuit breaker configuration

    Returns:
        A decorator function
    """
    fallback = get_fallback(
        primary_provider_id, fallback_provider_ids, circuit_breaker_config
    )

    def decorator(func: Callable[[str], T]) -> Callable[[], T]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            return fallback.execute(
                lambda provider_id: func(provider_id, *args, **kwargs)
            )

        return cast(Callable[[], T], wrapper)

    return decorator


def get_circuit_breaker(
    provider_id: str, config: Optional[CircuitBreakerConfig] = None
) -> CircuitBreaker:
    """Get or create a circuit breaker for a provider.

    This function gets an existing circuit breaker for a provider or
    creates a new one if none exists.

    Args:
        provider_id: The ID of the provider
        config: The circuit breaker configuration

    Returns:
        The circuit breaker for the provider
    """
    if provider_id in _circuit_breakers:
        return _circuit_breakers[provider_id]

    breaker = CircuitBreaker(provider_id, config)
    _circuit_breakers[provider_id] = breaker
    return breaker


def reset_circuit_breaker(provider_id: str) -> None:
    """Reset a circuit breaker for a provider.

    This function resets a circuit breaker for a provider to its initial state.

    Args:
        provider_id: The ID of the provider
    """
    if provider_id in _circuit_breakers:
        _circuit_breakers[provider_id].reset()


def reset_all_circuit_breakers() -> None:
    """Reset all circuit breakers.

    This function resets all circuit breakers to their initial state.
    """
    for breaker in _circuit_breakers.values():
        breaker.reset()


def get_fallback(
    primary_provider_id: str,
    fallback_provider_ids: List[str],
    circuit_breaker_config: Optional[CircuitBreakerConfig] = None,
) -> ProviderFallback:
    """Get or create a provider fallback.

    This function gets an existing provider fallback or creates a new one
    if none exists.

    Args:
        primary_provider_id: The ID of the primary provider
        fallback_provider_ids: The IDs of the fallback providers
        circuit_breaker_config: The circuit breaker configuration

    Returns:
        The provider fallback
    """
    key = f"{primary_provider_id}:{','.join(fallback_provider_ids)}"
    if key in _provider_fallbacks:
        return _provider_fallbacks[key]

    fallback = ProviderFallback(
        primary_provider_id, fallback_provider_ids, circuit_breaker_config
    )
    _provider_fallbacks[key] = fallback
    return fallback
