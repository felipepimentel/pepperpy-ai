"""Circuit breaker implementation for LLM providers."""

from datetime import datetime, timedelta
from typing import Any, Dict, Optional


class CircuitBreakerState:
    """Circuit breaker state."""

    def __init__(
        self,
        failure_threshold: int = 3,
        reset_timeout: int = 60,
        half_open_timeout: int = 30,
    ) -> None:
        """Initialize circuit breaker state.
        
        Args:
            failure_threshold: Number of failures before opening circuit
            reset_timeout: Seconds to wait before attempting reset
            half_open_timeout: Seconds to wait in half-open state
        """
        self.failure_count: int = 0
        self.last_failure_time: Optional[datetime] = None
        self.last_success_time: Optional[datetime] = None
        self.is_open: bool = False
        self.failure_threshold = failure_threshold
        self.reset_timeout = reset_timeout
        self.half_open_timeout = half_open_timeout

    def record_failure(self) -> None:
        """Record a failure and update state."""
        self.failure_count += 1
        self.last_failure_time = datetime.now()
        
        if self.failure_count >= self.failure_threshold:
            self.is_open = True

    def record_success(self) -> None:
        """Record a success and update state."""
        self.failure_count = 0
        self.last_success_time = datetime.now()
        self.is_open = False

    def should_allow_request(self) -> bool:
        """Check if request should be allowed.
        
        Returns:
            True if request should be allowed
        """
        if not self.is_open:
            return True

        # Check if enough time has passed to try again
        if self.last_failure_time:
            elapsed = datetime.now() - self.last_failure_time
            if elapsed > timedelta(seconds=self.reset_timeout):
                # Enter half-open state
                return True

        return False


class CircuitBreaker:
    """Circuit breaker for LLM providers."""

    def __init__(self) -> None:
        """Initialize circuit breaker."""
        self.states: Dict[str, CircuitBreakerState] = {}

    def get_state(self, provider: str) -> CircuitBreakerState:
        """Get circuit breaker state for provider.
        
        Args:
            provider: Provider name
            
        Returns:
            Circuit breaker state
        """
        if provider not in self.states:
            self.states[provider] = CircuitBreakerState()
        return self.states[provider]

    def record_failure(self, provider: str) -> None:
        """Record provider failure.
        
        Args:
            provider: Provider name
        """
        state = self.get_state(provider)
        state.record_failure()

    def record_success(self, provider: str) -> None:
        """Record provider success.
        
        Args:
            provider: Provider name
        """
        state = self.get_state(provider)
        state.record_success()

    def should_allow_request(self, provider: str) -> bool:
        """Check if request should be allowed for provider.
        
        Args:
            provider: Provider name
            
        Returns:
            True if request should be allowed
        """
        state = self.get_state(provider)
        return state.should_allow_request() 