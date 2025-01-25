"""Circuit breaker implementation.

This module provides functionality for implementing the circuit breaker pattern,
including failure detection, state transitions, and automatic recovery.
"""

from datetime import datetime, timedelta
from enum import Enum, auto
from typing import Any, Dict, Optional, TypeVar

from ..core.errors import PepperpyError
from ..core.events import Event, EventBus
from ..monitoring import Monitor
from ..interfaces import BaseProvider

T = TypeVar("T")


class CircuitState(Enum):
    """Circuit breaker states."""
    
    CLOSED = auto()
    """Circuit is closed (normal operation)."""
    
    OPEN = auto()
    """Circuit is open (failing)."""
    
    HALF_OPEN = auto()
    """Circuit is half-open (testing recovery)."""


class CircuitError(PepperpyError):
    """Circuit breaker error."""
    pass


class CircuitBreaker(BaseProvider):
    """Circuit breaker implementation."""
    
    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        event_bus: Optional[EventBus] = None,
        monitor: Optional[Monitor] = None,
        config: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize breaker.
        
        Args:
            name: Breaker name
            failure_threshold: Number of failures before opening
            recovery_timeout: Seconds to wait before recovery attempt
            event_bus: Optional event bus
            monitor: Optional monitor
            config: Optional configuration
        """
        super().__init__(
            name=name,
            config=config,
            event_bus=event_bus,
            monitor=monitor,
        )
        self._failure_threshold = failure_threshold
        self._recovery_timeout = timedelta(seconds=recovery_timeout)
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._last_failure_time: Optional[datetime] = None
        self._last_success_time: Optional[datetime] = None
        
    @property
    def state(self) -> CircuitState:
        """Get circuit state.
        
        Returns:
            Circuit state
        """
        return self._state
        
    @property
    def failure_count(self) -> int:
        """Get failure count.
        
        Returns:
            Failure count
        """
        return self._failure_count
        
    async def execute(self, func: Any, *args: Any, **kwargs: Any) -> T:
        """Execute function with circuit breaker.
        
        Args:
            func: Function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            Function result
            
        Raises:
            CircuitError: If circuit is open
        """
        # Check circuit state
        if self._state == CircuitState.OPEN:
            if self._should_attempt_recovery():
                self._state = CircuitState.HALF_OPEN
                await self._publish_state_change()
            else:
                raise CircuitError("Circuit is open")
                
        # Execute function
        try:
            result = await func(*args, **kwargs)
            await self._handle_success()
            return result
        except Exception as e:
            await self._handle_failure(e)
            raise
            
    def _should_attempt_recovery(self) -> bool:
        """Check if recovery should be attempted.
        
        Returns:
            True if recovery should be attempted
        """
        if not self._last_failure_time:
            return False
            
        elapsed = datetime.now() - self._last_failure_time
        return elapsed >= self._recovery_timeout
        
    async def _handle_success(self) -> None:
        """Handle successful execution."""
        self._last_success_time = datetime.now()
        
        if self._state == CircuitState.HALF_OPEN:
            self._state = CircuitState.CLOSED
            self._failure_count = 0
            await self._publish_state_change()
            
    async def _handle_failure(self, error: Exception) -> None:
        """Handle failed execution.
        
        Args:
            error: Execution error
        """
        self._last_failure_time = datetime.now()
        self._failure_count += 1
        
        if (
            self._state == CircuitState.CLOSED
            and self._failure_count >= self._failure_threshold
        ):
            self._state = CircuitState.OPEN
            await self._publish_state_change()
        elif self._state == CircuitState.HALF_OPEN:
            self._state = CircuitState.OPEN
            await self._publish_state_change()
            
    async def _publish_state_change(self) -> None:
        """Publish state change event."""
        if self.event_bus:
            await self.event_bus.publish(
                Event(
                    type="circuit_state_changed",
                    source=self.name,
                    timestamp=datetime.now(),
                    data={
                        "state": self._state.name,
                        "failure_count": self._failure_count,
                    },
                )
            )
            
    async def _initialize_impl(self) -> None:
        """Initialize breaker."""
        pass
            
    async def _cleanup_impl(self) -> None:
        """Clean up breaker."""
        pass
            
    async def _validate_impl(self) -> None:
        """Validate breaker state."""
        if not self.name:
            raise CircuitError("Empty breaker name")
            
        if self._failure_threshold < 1:
            raise CircuitError("Invalid failure threshold")
            
        if self._recovery_timeout.total_seconds() <= 0:
            raise CircuitError("Invalid recovery timeout") 