"""Runtime agent orchestration.

This module provides orchestration for runtime agents, handling coordination,
resource scheduling, and performance optimization.
"""

from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any
from uuid import UUID

from pepperpy.core.errors import OrchestratorError
from pepperpy.core.types import ResourceId
from pepperpy.monitoring.logger import get_logger
from pepperpy.runtime.lifecycle import LifecycleManager

logger = get_logger(__name__)


@dataclass
class ResourceAllocation:
    """Resource allocation information.

    Attributes:
        resource_id: The ID of the resource
        agent_id: The ID of the agent using the resource
        allocation_time: Optional allocation timestamp
        metadata: Additional allocation metadata
    """

    resource_id: ResourceId
    agent_id: UUID
    allocation_time: float | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


class Orchestrator:
    """Orchestrates runtime agents and resources.

    Handles agent coordination, resource scheduling, error handling,
    and performance optimization.
    """

    def __init__(self, lifecycle_manager: LifecycleManager) -> None:
        """Initialize the orchestrator.

        Args:
            lifecycle_manager: The lifecycle manager to use
        """
        self._lifecycle = lifecycle_manager
        self._agent_groups: dict[str, set[UUID]] = defaultdict(set)
        self._resource_allocations: dict[ResourceId, ResourceAllocation] = {}
        self._agent_dependencies: dict[UUID, set[UUID]] = defaultdict(set)
        self._performance_metrics: dict[UUID, dict[str, float]] = defaultdict(dict)

    def register_agent_group(self, group_id: str, agent_ids: list[UUID]) -> None:
        """Register a group of related agents.

        Args:
            group_id: The ID for the agent group
            agent_ids: The UUIDs of agents in the group

        Raises:
            OrchestratorError: If any agent is already in a group
        """
        for agent_id in agent_ids:
            for group in self._agent_groups.values():
                if agent_id in group:
                    raise OrchestratorError(f"Agent {agent_id} is already in a group")

            self._agent_groups[group_id].add(agent_id)

        logger.info(f"Registered agent group {group_id} with {len(agent_ids)} agents")

    def set_agent_dependencies(
        self, agent_id: UUID, dependency_ids: list[UUID]
    ) -> None:
        """Set dependencies between agents.

        Args:
            agent_id: The UUID of the dependent agent
            dependency_ids: The UUIDs of agents it depends on

        Raises:
            OrchestratorError: If a circular dependency is detected
        """
        # Check for circular dependencies
        for dep_id in dependency_ids:
            if self._would_create_cycle(agent_id, dep_id):
                raise OrchestratorError(
                    f"Circular dependency detected between {agent_id} and {dep_id}"
                )

        self._agent_dependencies[agent_id] = set(dependency_ids)
        logger.info(f"Set {len(dependency_ids)} dependencies for agent {agent_id}")

    def allocate_resource(
        self, resource_id: ResourceId, agent_id: UUID, **metadata: Any
    ) -> None:
        """Allocate a resource to an agent.

        Args:
            resource_id: The ID of the resource to allocate
            agent_id: The UUID of the agent to allocate to
            **metadata: Additional allocation metadata

        Raises:
            OrchestratorError: If the resource is already allocated
        """
        if resource_id in self._resource_allocations:
            raise OrchestratorError(f"Resource {resource_id} is already allocated")

        allocation = ResourceAllocation(
            resource_id=resource_id, agent_id=agent_id, metadata=metadata
        )
        self._resource_allocations[resource_id] = allocation

        logger.info(f"Allocated resource {resource_id} to agent {agent_id}")

    def deallocate_resource(self, resource_id: ResourceId) -> None:
        """Deallocate a resource.

        Args:
            resource_id: The ID of the resource to deallocate

        Raises:
            OrchestratorError: If the resource is not allocated
        """
        if resource_id not in self._resource_allocations:
            raise OrchestratorError(f"Resource {resource_id} is not allocated")

        allocation = self._resource_allocations.pop(resource_id)
        logger.info(
            f"Deallocated resource {resource_id} from agent {allocation.agent_id}"
        )

    def update_performance_metrics(
        self, agent_id: UUID, metrics: dict[str, float]
    ) -> None:
        """Update performance metrics for an agent.

        Args:
            agent_id: The UUID of the agent
            metrics: The metrics to update
        """
        self._performance_metrics[agent_id].update(metrics)
        logger.debug(f"Updated performance metrics for agent {agent_id}")

    def get_agent_group(self, agent_id: UUID) -> str | None:
        """Get the group ID for an agent.

        Args:
            agent_id: The UUID of the agent

        Returns:
            The group ID if found, None otherwise
        """
        for group_id, agents in self._agent_groups.items():
            if agent_id in agents:
                return group_id
        return None

    def get_agent_dependencies(self, agent_id: UUID) -> set[UUID]:
        """Get the dependencies for an agent.

        Args:
            agent_id: The UUID of the agent

        Returns:
            The set of agent UUIDs this agent depends on
        """
        return self._agent_dependencies.get(agent_id, set())

    def get_resource_allocation(
        self, resource_id: ResourceId
    ) -> ResourceAllocation | None:
        """Get the allocation information for a resource.

        Args:
            resource_id: The ID of the resource

        Returns:
            The allocation information if found, None otherwise
        """
        return self._resource_allocations.get(resource_id)

    def get_performance_metrics(self, agent_id: UUID) -> dict[str, float]:
        """Get performance metrics for an agent.

        Args:
            agent_id: The UUID of the agent

        Returns:
            The agent's performance metrics
        """
        return self._performance_metrics.get(agent_id, {})

    def _would_create_cycle(self, agent_id: UUID, dependency_id: UUID) -> bool:
        """Check if adding a dependency would create a cycle.

        Args:
            agent_id: The UUID of the dependent agent
            dependency_id: The UUID of the dependency

        Returns:
            True if a cycle would be created
        """
        visited = set()

        def has_path(start: UUID, target: UUID) -> bool:
            if start == target:
                return True

            if start in visited:
                return False

            visited.add(start)
            return any(
                has_path(dep, target)
                for dep in self._agent_dependencies.get(start, set())
            )

        return has_path(dependency_id, agent_id)
