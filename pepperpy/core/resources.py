"""Resource and asset management module.

This module provides a unified system for managing resources and assets.
"""

import asyncio
import logging
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from pepperpy.core.metrics.base import Counter, Histogram

from pepperpy.core.base import ComponentBase
from pepperpy.core.enums import ResourceType
from pepperpy.core.errors import ResourceError
from pepperpy.core.metrics import metrics_manager
from pepperpy.core.models import BaseModel, Field

# Configure logging
logger = logging.getLogger(__name__)


class ResourceMetadata(BaseModel):
    """Resource metadata model.

    This class defines the metadata associated with a resource.
    """

    name: str = Field(..., description="Resource name")
    type: ResourceType = Field(..., description="Resource type")
    created: datetime = Field(
        default_factory=datetime.utcnow, description="Creation timestamp"
    )
    updated: datetime = Field(
        default_factory=datetime.utcnow, description="Last update timestamp"
    )
    tags: set[str] = Field(default_factory=set, description="Resource tags")
    description: str | None = Field(None, description="Resource description")
    version: str | None = Field(None, description="Resource version")
    dependencies: set[str] = Field(
        default_factory=set, description="Resource dependencies"
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )


class Resource(BaseModel):
    """Resource model.

    This class defines the base resource model.
    """

    metadata: ResourceMetadata = Field(..., description="Resource metadata")
    content: Any = Field(..., description="Resource content")
    path: Path | None = Field(None, description="Resource path")
    checksum: str | None = Field(None, description="Resource checksum")
    size: int | None = Field(None, description="Resource size in bytes")
    format: str | None = Field(None, description="Resource format")
    encoding: str | None = Field(None, description="Resource encoding")
    compression: str | None = Field(None, description="Resource compression")
    encrypted: bool = Field(False, description="Whether resource is encrypted")


class ResourceManager(ComponentBase):
    """Resource manager implementation.

    This class provides methods for managing resources and assets.
    """

    def __init__(self) -> None:
        """Initialize manager."""
        super().__init__()
        self._resources: dict[str, Resource] = {}
        self._lock = asyncio.Lock()

        # Initialize metrics
        self._resources_loaded = None
        self._resources_saved = None
        self._resource_errors = None
        self._resource_size = None

    async def _setup_metrics(self) -> None:
        """Set up metrics for the component."""
        # Initialize metrics
        self._resources_loaded = await metrics_manager.create_counter(
            name="resources_loaded_total",
            description="Total number of resources loaded",
        )
        self._resources_saved = await metrics_manager.create_counter(
            name="resources_saved_total",
            description="Total number of resources saved",
        )
        self._resource_errors = await metrics_manager.create_counter(
            name="resource_errors_total",
            description="Total number of resource errors",
        )
        self._resource_size = await metrics_manager.create_histogram(
            name="resource_size_bytes",
            description="Resource size in bytes",
            buckets=[1024, 10240, 102400, 1048576],  # 1KB, 10KB, 100KB, 1MB
        )

    def _increment_metric(self, metric: Counter | None) -> None:
        """Increment a metric if it exists.

        Args:
            metric: Metric to increment
        """
        if metric is not None:
            metric.inc()

    def _observe_metric(self, metric: Histogram | None, value: float) -> None:
        """Observe a metric value if the metric exists.

        Args:
            metric: Metric to observe
            value: Value to observe
        """
        if metric is not None:
            metric.observe(value)

    async def load_resource(
        self,
        path: str | Path,
        resource_type: ResourceType | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> Resource:
        """Load resource from path.

        Args:
            path: Resource path
            resource_type: Resource type
            metadata: Additional metadata

        Returns:
            Resource: Loaded resource

        Raises:
            ResourceError: If resource cannot be loaded
        """
        try:
            path = Path(path)
            if not path.exists():
                raise ResourceError(f"Resource not found: {path}")

            async with self._lock:
                if str(path) in self._resources:
                    return self._resources[str(path)]

                # Load resource content
                content = await self._load_content(path)

                # Create resource metadata
                resource_metadata = ResourceMetadata(
                    name=path.name,
                    type=resource_type or self._infer_type(path),
                    description=f"Resource loaded from {path}",
                    version="1.0.0",
                    metadata=metadata or {},
                )

                # Create resource
                resource = Resource(
                    metadata=resource_metadata,
                    content=content,
                    path=path,
                    size=path.stat().st_size,
                    format=path.suffix.lstrip("."),
                    checksum=None,  # TODO: Implement checksum calculation
                    encoding="utf-8",  # Default encoding
                    compression=None,  # No compression by default
                    encrypted=False,  # Not encrypted by default
                )

                # Update metrics
                self._increment_metric(self._resources_loaded)
                self._observe_metric(self._resource_size, resource.size or 0)

                # Cache resource
                self._resources[str(path)] = resource
                return resource

        except Exception as e:
            self._increment_metric(self._resource_errors)
            logger.error(
                f"Failed to load resource: {e}",
                extra={
                    "path": str(path),
                    "type": str(resource_type),
                },
                exc_info=True,
            )
            raise ResourceError(f"Failed to load resource: {e}") from e

    async def save_resource(
        self,
        resource: Resource,
        path: str | Path | None = None,
    ) -> None:
        """Save resource to path.

        Args:
            resource: Resource to save
            path: Target path (defaults to resource.path)

        Raises:
            ResourceError: If resource cannot be saved
        """
        try:
            target_path = Path(path) if path else resource.path
            if not target_path:
                raise ResourceError("No target path specified")

            # Create parent directories
            target_path.parent.mkdir(parents=True, exist_ok=True)

            async with self._lock:
                # Save resource content
                await self._save_content(target_path, resource.content)

                # Update resource
                resource.path = target_path
                resource.size = target_path.stat().st_size
                resource.metadata.updated = datetime.utcnow()

                # Update metrics
                self._increment_metric(self._resources_saved)
                self._observe_metric(self._resource_size, resource.size or 0)

                # Cache resource
                self._resources[str(target_path)] = resource

        except Exception as e:
            self._increment_metric(self._resource_errors)
            logger.error(
                f"Failed to save resource: {e}",
                extra={
                    "path": str(path or resource.path),
                    "type": str(resource.metadata.type),
                },
                exc_info=True,
            )
            raise ResourceError(f"Failed to save resource: {e}") from e

    async def get_resource(
        self,
        path: str | Path,
    ) -> Resource | None:
        """Get resource by path.

        Args:
            path: Resource path

        Returns:
            Optional[Resource]: Resource if found
        """
        return self._resources.get(str(Path(path)))

    async def list_resources(
        self,
        resource_type: ResourceType | None = None,
        tags: set[str] | None = None,
    ) -> list[Resource]:
        """List resources.

        Args:
            resource_type: Filter by resource type
            tags: Filter by tags

        Returns:
            List[Resource]: List of resources
        """
        resources = list(self._resources.values())

        if resource_type:
            resources = [r for r in resources if r.metadata.type == resource_type]

        if tags:
            resources = [r for r in resources if tags.issubset(r.metadata.tags)]

        return resources

    async def delete_resource(
        self,
        path: str | Path,
    ) -> None:
        """Delete resource.

        Args:
            path: Resource path

        Raises:
            ResourceError: If resource cannot be deleted
        """
        try:
            path = Path(path)
            if not path.exists():
                return

            async with self._lock:
                # Delete file
                path.unlink()

                # Remove from cache
                self._resources.pop(str(path), None)

        except Exception as e:
            self._increment_metric(self._resource_errors)
            logger.error(
                f"Failed to delete resource: {e}",
                extra={"path": str(path)},
                exc_info=True,
            )
            raise ResourceError(f"Failed to delete resource: {e}") from e

    def _infer_type(self, path: Path) -> ResourceType:
        """Infer resource type from path.

        Args:
            path: Resource path

        Returns:
            ResourceType: Inferred resource type
        """
        # Default to MODEL type for now
        return ResourceType.MODEL

    async def _load_content(self, path: Path) -> Any:
        """Load resource content.

        Args:
            path: Resource path

        Returns:
            Any: Resource content

        Raises:
            ResourceError: If content cannot be loaded
        """
        try:
            # TODO: Implement content loading based on format
            return await asyncio.to_thread(path.read_bytes)
        except Exception as e:
            raise ResourceError(f"Failed to load content: {e}") from e

    async def _save_content(self, path: Path, content: Any) -> None:
        """Save resource content.

        Args:
            path: Target path
            content: Resource content

        Raises:
            ResourceError: If content cannot be saved
        """
        try:
            # TODO: Implement content saving based on format
            await asyncio.to_thread(path.write_bytes, content)
        except Exception as e:
            raise ResourceError(f"Failed to save content: {e}") from e
