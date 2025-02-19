"""@file: sharding.py
@purpose: Runtime sharding functionality for distributed operations
@component: Runtime
@created: 2024-02-15
@task: TASK-003
@status: active
"""

import threading
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Set
from uuid import UUID, uuid4

from pepperpy.core.errors import ConfigurationError, StateError
from pepperpy.core.logging import get_logger
from pepperpy.core.types import JSON
from pepperpy.runtime.context import get_current_context
from pepperpy.runtime.lifecycle import get_lifecycle_manager

logger = get_logger(__name__)


@dataclass
class ShardConfig:
    """Configuration for sharding."""

    enabled: bool = True
    max_shards: int = 10
    min_shard_size: int = 1000
    replication_factor: int = 2

    def validate(self) -> None:
        """Validate shard configuration."""
        if self.max_shards < 1:
            raise ConfigurationError("Max shards must be positive")
        if self.min_shard_size < 1:
            raise ConfigurationError("Min shard size must be positive")
        if self.replication_factor < 1:
            raise ConfigurationError("Replication factor must be positive")


@dataclass
class Shard:
    """Runtime shard for distributed operations."""

    name: str
    capacity: int
    id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)
    nodes: Set[str] = field(default_factory=set)

    def to_json(self) -> JSON:
        """Convert shard to JSON format."""
        return {
            "id": str(self.id),
            "name": self.name,
            "capacity": self.capacity,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "metadata": self.metadata,
            "nodes": list(self.nodes),
        }


class ShardingStrategy:
    """Strategy for shard management and distribution."""

    def __init__(self, config: Optional[ShardConfig] = None) -> None:
        """Initialize sharding strategy.

        Args:
            config: Optional sharding configuration

        """
        self.config = config or ShardConfig()
        self.config.validate()

    def calculate_shard_distribution(self, total_size: int) -> List[int]:
        """Calculate shard size distribution.

        Args:
            total_size: Total size to distribute

        Returns:
            List of shard sizes

        """
        if total_size < self.config.min_shard_size:
            return [total_size]

        num_shards = min(
            self.config.max_shards,
            total_size // self.config.min_shard_size,
        )
        base_size = total_size // num_shards
        remainder = total_size % num_shards

        sizes = [base_size] * num_shards
        for i in range(remainder):
            sizes[i] += 1

        return sizes

    def get_shard_for_key(self, key: str, num_shards: int) -> int:
        """Get shard index for a key.

        Args:
            key: Key to get shard for
            num_shards: Number of shards

        Returns:
            Shard index

        """
        return hash(key) % num_shards


class ShardManager:
    """Manager for runtime shards."""

    def __init__(self, config: Optional[ShardConfig] = None) -> None:
        """Initialize shard manager.

        Args:
            config: Optional shard configuration

        """
        self.config = config or ShardConfig()
        self.config.validate()

        self._shards: Dict[UUID, Shard] = {}
        self._strategy = ShardingStrategy(self.config)
        self._lock = threading.Lock()
        self._lifecycle = get_lifecycle_manager().create(
            context=get_current_context(),
            metadata={"component": "shard_manager"},
        )

    def create_shard(
        self,
        name: str,
        capacity: int,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Shard:
        """Create a new shard.

        Args:
            name: Shard name
            capacity: Shard capacity
            metadata: Optional shard metadata

        Returns:
            Created shard instance

        Raises:
            ConfigurationError: If max shards limit reached

        """
        with self._lock:
            if len(self._shards) >= self.config.max_shards:
                raise ConfigurationError("Max shards limit reached")

            shard = Shard(
                name=name,
                capacity=capacity,
                metadata=metadata or {},
            )
            self._shards[shard.id] = shard
            return shard

    def get_shard(self, shard_id: UUID) -> Optional[Shard]:
        """Get a shard by ID.

        Args:
            shard_id: Shard ID

        Returns:
            Shard if found, None otherwise

        """
        return self._shards.get(shard_id)

    def add_node(self, shard_id: UUID, node: str) -> None:
        """Add a node to a shard.

        Args:
            shard_id: Shard ID
            node: Node identifier

        Raises:
            StateError: If shard not found

        """
        with self._lock:
            shard = self._shards.get(shard_id)
            if not shard:
                raise StateError(f"Shard not found: {shard_id}")
            shard.nodes.add(node)
            shard.updated_at = datetime.utcnow()

    def remove_node(self, shard_id: UUID, node: str) -> None:
        """Remove a node from a shard.

        Args:
            shard_id: Shard ID
            node: Node identifier

        Raises:
            StateError: If shard not found

        """
        with self._lock:
            shard = self._shards.get(shard_id)
            if not shard:
                raise StateError(f"Shard not found: {shard_id}")
            shard.nodes.discard(node)
            shard.updated_at = datetime.utcnow()

    def get_shard_for_key(self, key: str) -> Optional[Shard]:
        """Get the shard for a key.

        Args:
            key: Key to get shard for

        Returns:
            Shard if found, None otherwise

        """
        with self._lock:
            if not self._shards:
                return None

            shard_index = self._strategy.get_shard_for_key(
                key,
                len(self._shards),
            )
            return list(self._shards.values())[shard_index]


# Global shard manager instance
_shard_manager = ShardManager()


def get_shard_manager() -> ShardManager:
    """Get the global shard manager instance.

    Returns:
        Global shard manager instance

    """
    return _shard_manager
