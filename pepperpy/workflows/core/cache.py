"""Workflow caching system.

This module provides caching functionality for workflows, allowing for
efficient execution by caching step results and workflow states.
"""

import hashlib
import json
from datetime import timedelta
from typing import Any, Dict, Optional, Union

from pepperpy.caching.base import Cache, CacheBackend
from pepperpy.caching.memory import MemoryCache
from pepperpy.workflows.base import WorkflowStep


class WorkflowCache:
    """Cache system for workflow execution results.

    This class provides caching functionality for workflow steps and results,
    improving performance by avoiding redundant computations.
    """

    def __init__(
        self,
        backend: Optional[CacheBackend] = None,
        namespace: str = "workflow",
        default_ttl: int = 3600,  # 1 hour in seconds
    ):
        """Initialize workflow cache.

        Args:
            backend: Cache backend (uses MemoryCache if None)
            namespace: Cache namespace
            default_ttl: Default TTL in seconds
        """
        self.backend = backend or MemoryCache()
        self.cache = Cache(backend=self.backend, namespace=namespace)
        self.default_ttl = default_ttl

    def _generate_key(self, step: WorkflowStep, params: Dict[str, Any]) -> str:
        """Generate a cache key for a workflow step.

        Args:
            step: Workflow step
            params: Step parameters

        Returns:
            Cache key
        """
        # Convert parameters to a stable string representation
        params_str = json.dumps(params, sort_keys=True)
        key_data = f"{step.name}:{step.action}:{params_str}"
        return hashlib.md5(key_data.encode()).hexdigest()

    async def get_step_result(
        self, step: WorkflowStep, params: Dict[str, Any]
    ) -> Optional[Any]:
        """Get cached result for a workflow step.

        Args:
            step: Workflow step
            params: Step parameters

        Returns:
            Cached result or None if not found
        """
        key = self._generate_key(step, params)
        if await self.cache.contains(key):
            return await self.cache.get(key)
        return None

    async def set_step_result(
        self,
        step: WorkflowStep,
        params: Dict[str, Any],
        result: Any,
        ttl: Optional[Union[int, timedelta]] = None,
    ) -> None:
        """Cache result for a workflow step.

        Args:
            step: Workflow step
            params: Step parameters
            result: Step result
            ttl: Optional TTL (uses default if None)
        """
        key = self._generate_key(step, params)
        await self.cache.set(key, result, ttl=ttl or self.default_ttl)

    async def invalidate_step(self, step: WorkflowStep, params: Dict[str, Any]) -> None:
        """Invalidate cached result for a workflow step.

        Args:
            step: Workflow step
            params: Step parameters
        """
        key = self._generate_key(step, params)
        await self.cache.delete(key)

    async def invalidate_workflow(self, workflow_id: str) -> None:
        """Invalidate all cached results for a workflow.

        Args:
            workflow_id: Workflow ID
        """
        # This would require a more sophisticated implementation
        # with backend-specific prefix scanning capabilities
        # For now, we'll just clear the entire cache
        await self.cache.clear()

    async def clear(self) -> None:
        """Clear all cached workflow results."""
        await self.cache.clear()
