"""Sharding support for runtime components.

This module provides functionality for managing distributed agents across multiple
shards, including shard management, rebalancing, and failover handling.
"""

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from functools import wraps
from typing import ParamSpec, TypeVar
from uuid import UUID

from pydantic import BaseModel

from pepperpy.core.errors import ShardingError
from pepperpy.monitoring import logger, tracer

T = TypeVar("T")
P = ParamSpec("P")


def trace(name: str) -> Callable[[Callable[P, T]], Callable[P, T]]:
    """Decorator to trace function execution.

    Args:
        name: Name of the trace.

    Returns:
        Decorated function.
    """

    def decorator(func: Callable[P, T]) -> Callable[P, T]:
        @wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            with tracer.start_trace(name):
                return func(*args, **kwargs)

        return wrapper

    return decorator


class ShardConfig(BaseModel):
    """Configuration for a shard."""

    shard_id: str
    capacity: int = 100  # Maximum number of agents per shard
    min_free_capacity: int = 10  # Minimum free capacity before rebalancing
    rebalance_threshold: float = 0.2  # Rebalance when imbalance exceeds 20%
    heartbeat_interval: int = 5  # Seconds between heartbeats


@dataclass
class ShardInfo:
    """Information about a shard."""

    config: ShardConfig
    agents: set[UUID]
    last_heartbeat: datetime
    metrics: dict[str, float]


class ShardManager:
    """Manager for distributed shards."""

    def __init__(self) -> None:
        """Initialize the shard manager."""
        self._shards: dict[str, ShardInfo] = {}
        self._agent_locations: dict[UUID, str] = {}

    @trace("register_shard")
    def register_shard(self, config: ShardConfig) -> None:
        """Register a new shard.

        Args:
            config: Configuration for the shard

        Raises:
            ShardingError: If shard already exists
        """
        if config.shard_id in self._shards:
            raise ShardingError(f"Shard {config.shard_id} already exists")

        self._shards[config.shard_id] = ShardInfo(
            config=config,
            agents=set(),
            last_heartbeat=datetime.utcnow(),
            metrics={
                "cpu_usage": 0.0,
                "memory_usage": 0.0,
                "network_usage": 0.0,
            },
        )
        logger.info("Registered new shard", shard_id=config.shard_id)

    @trace("assign_agent")
    def assign_agent(self, agent_id: UUID, shard_id: str | None = None) -> str:
        """Assign an agent to a shard.

        Args:
            agent_id: ID of the agent to assign
            shard_id: Optional specific shard to assign to

        Returns:
            ID of the assigned shard

        Raises:
            ShardingError: If no suitable shard is found or specified shard is invalid
        """
        if agent_id in self._agent_locations:
            raise ShardingError(f"Agent {agent_id} is already assigned")

        if shard_id:
            if shard_id not in self._shards:
                raise ShardingError(f"Shard {shard_id} does not exist")
            target_shard = shard_id
        else:
            target_shard = self._find_best_shard()

        shard = self._shards[target_shard]
        if len(shard.agents) >= shard.config.capacity:
            raise ShardingError(f"Shard {target_shard} is at capacity")

        shard.agents.add(agent_id)
        self._agent_locations[agent_id] = target_shard
        logger.info(
            "Assigned agent to shard",
            agent_id=str(agent_id),
            shard_id=target_shard,
        )
        return target_shard

    def _find_best_shard(self) -> str:
        """Find the best shard for a new agent.

        Returns:
            ID of the best shard

        Raises:
            ShardingError: If no suitable shard is found
        """
        if not self._shards:
            raise ShardingError("No shards available")

        # Find shard with most free capacity
        best_shard = min(
            self._shards.items(),
            key=lambda x: len(x[1].agents) / x[1].config.capacity,
        )
        return best_shard[0]

    @trace("rebalance_shards")
    def rebalance_shards(self) -> None:
        """Rebalance agents across shards."""
        if len(self._shards) < 2:
            return

        # Calculate average load
        total_agents = sum(len(shard.agents) for shard in self._shards.values())
        avg_load = total_agents / len(self._shards)

        # Find overloaded and underloaded shards
        overloaded = [
            shard_id
            for shard_id, info in self._shards.items()
            if len(info.agents) > avg_load * (1 + info.config.rebalance_threshold)
        ]
        underloaded = [
            shard_id
            for shard_id, info in self._shards.items()
            if len(info.agents) < avg_load * (1 - info.config.rebalance_threshold)
        ]

        if not (overloaded and underloaded):
            return

        # Rebalance agents
        for over_id in overloaded:
            over_shard = self._shards[over_id]
            agents_to_move = len(over_shard.agents) - int(avg_load)

            if agents_to_move <= 0:
                continue

            for under_id in underloaded:
                under_shard = self._shards[under_id]
                space_available = int(avg_load) - len(under_shard.agents)

                if space_available <= 0:
                    continue

                to_move = min(agents_to_move, space_available)
                self._move_agents(over_id, under_id, to_move)
                agents_to_move -= to_move

                if agents_to_move <= 0:
                    break

    def _move_agents(self, from_shard: str, to_shard: str, count: int) -> None:
        """Move agents between shards.

        Args:
            from_shard: Source shard ID
            to_shard: Destination shard ID
            count: Number of agents to move
        """
        source = self._shards[from_shard]
        target = self._shards[to_shard]

        # Select agents to move (prefer non-busy agents)
        agents_to_move = sorted(
            source.agents,
            key=lambda x: self._get_agent_load(x),
        )[:count]

        # Move agents
        for agent_id in agents_to_move:
            source.agents.remove(agent_id)
            target.agents.add(agent_id)
            self._agent_locations[agent_id] = to_shard

        logger.info(
            "Moved agents between shards",
            from_shard=from_shard,
            to_shard=to_shard,
            count=len(agents_to_move),
        )

    def _get_agent_load(self, agent_id: UUID) -> float:
        """Get the current load of an agent.

        Args:
            agent_id: ID of the agent

        Returns:
            Load value between 0 and 1
        """
        # TODO: Implement actual load calculation based on agent metrics
        return 0.5

    @trace("handle_shard_failure")
    def handle_shard_failure(self, shard_id: str) -> None:
        """Handle failure of a shard.

        Args:
            shard_id: ID of the failed shard

        Raises:
            ShardingError: If shard does not exist
        """
        if shard_id not in self._shards:
            raise ShardingError(f"Shard {shard_id} does not exist")

        failed_shard = self._shards[shard_id]
        agents_to_reassign = list(failed_shard.agents)

        # Remove failed shard
        del self._shards[shard_id]
        logger.warning("Removed failed shard", shard_id=shard_id)

        # Reassign agents
        for agent_id in agents_to_reassign:
            try:
                new_shard = self.assign_agent(agent_id)
                logger.info(
                    "Reassigned agent from failed shard",
                    agent_id=str(agent_id),
                    new_shard=new_shard,
                )
            except ShardingError as e:
                logger.error(
                    "Failed to reassign agent",
                    agent_id=str(agent_id),
                    error=str(e),
                )

    @trace("update_shard_metrics")
    def update_shard_metrics(self, shard_id: str, metrics: dict[str, float]) -> None:
        """Update metrics for a shard.

        Args:
            shard_id: ID of the shard
            metrics: Dictionary of metric values

        Raises:
            ShardingError: If shard does not exist
        """
        if shard_id not in self._shards:
            raise ShardingError(f"Shard {shard_id} does not exist")

        shard = self._shards[shard_id]
        shard.metrics.update(metrics)
        shard.last_heartbeat = datetime.utcnow()

    def get_shard_info(self, shard_id: str) -> ShardInfo:
        """Get information about a shard.

        Args:
            shard_id: ID of the shard

        Returns:
            Information about the shard

        Raises:
            ShardingError: If shard does not exist
        """
        if shard_id not in self._shards:
            raise ShardingError(f"Shard {shard_id} does not exist")
        return self._shards[shard_id]

    def get_agent_shard(self, agent_id: UUID) -> str:
        """Get the shard ID for an agent.

        Args:
            agent_id: ID of the agent

        Returns:
            ID of the shard containing the agent

        Raises:
            ShardingError: If agent is not assigned
        """
        if agent_id not in self._agent_locations:
            raise ShardingError(f"Agent {agent_id} is not assigned to a shard")
        return self._agent_locations[agent_id]

    def list_shards(self) -> list[str]:
        """Get a list of all shard IDs.

        Returns:
            List of shard IDs
        """
        return list(self._shards.keys())
