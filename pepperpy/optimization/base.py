"""Core interfaces for optimization components."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Protocol, TypeVar, runtime_checkable

T = TypeVar("T")


@runtime_checkable
class OptimizationComponent(Protocol):
    """Base protocol for all optimization components."""

    @property
    def name(self) -> str:
        """Get component name."""
        ...

    @property
    def enabled(self) -> bool:
        """Check if component is enabled."""
        ...

    @property
    def metrics(self) -> Dict[str, Any]:
        """Get component metrics."""
        ...


class BaseOptimizer(ABC):
    """Base class for optimization components."""

    def __init__(self, name: str):
        self._name = name
        self._enabled = True
        self._metrics: Dict[str, Any] = {}

    @property
    def name(self) -> str:
        """Get optimizer name."""
        return self._name

    @property
    def enabled(self) -> bool:
        """Check if optimizer is enabled."""
        return self._enabled

    @property
    def metrics(self) -> Dict[str, Any]:
        """Get optimizer metrics."""
        return self._metrics

    def enable(self):
        """Enable the optimizer."""
        self._enabled = True

    def disable(self):
        """Disable the optimizer."""
        self._enabled = False

    def update_metrics(self, metrics: Dict[str, Any]):
        """Update optimizer metrics."""
        self._metrics.update(metrics)


class Batcher(BaseOptimizer):
    """Base class for request batching."""

    @abstractmethod
    async def add(self, item: T) -> str:
        """Add an item to the batch.

        Returns:
            Batch ID
        """
        raise NotImplementedError

    @abstractmethod
    async def get_batch(self, batch_id: str) -> List[T]:
        """Get items in a batch."""
        raise NotImplementedError

    @abstractmethod
    async def process_batch(self, batch_id: str) -> Dict[str, Any]:
        """Process a batch of items."""
        raise NotImplementedError


class Cache(BaseOptimizer):
    """Base class for caching."""

    @abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        raise NotImplementedError

    @abstractmethod
    async def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """Set value in cache with optional TTL in seconds."""
        raise NotImplementedError

    @abstractmethod
    async def delete(self, key: str):
        """Delete value from cache."""
        raise NotImplementedError

    @abstractmethod
    async def clear(self):
        """Clear all values from cache."""
        raise NotImplementedError


class TokenManager(BaseOptimizer):
    """Base class for token management."""

    @abstractmethod
    async def get_budget(self, user_id: str) -> int:
        """Get remaining token budget for user."""
        raise NotImplementedError

    @abstractmethod
    async def use_tokens(self, user_id: str, amount: int) -> bool:
        """Use tokens from user's budget.

        Returns:
            True if tokens were successfully used, False if insufficient
        """
        raise NotImplementedError

    @abstractmethod
    async def refund_tokens(self, user_id: str, amount: int):
        """Refund tokens to user's budget."""
        raise NotImplementedError


class Router(BaseOptimizer):
    """Base class for request routing."""

    @abstractmethod
    async def select_route(self, request: Any) -> str:
        """Select appropriate route for request.

        Returns:
            Route identifier
        """
        raise NotImplementedError

    @abstractmethod
    async def get_route_info(self, route_id: str) -> Dict[str, Any]:
        """Get information about a route."""
        raise NotImplementedError
