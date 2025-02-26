"""Hub base module.

This module provides base classes for Hub functionality.
"""

import logging
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from pydantic import BaseModel, Field

from pepperpy.core.base import Lifecycle
from pepperpy.core.types import ComponentState
from pepperpy.core.workflows import WorkflowConfig, WorkflowEngine


class HubType(str, Enum):
    """Type of hub."""

    LOCAL = "local"
    REMOTE = "remote"


class HubConfig(BaseModel):
    """Configuration for a Hub instance."""

    name: str = Field(description="Hub name")
    type: HubType = Field(default=HubType.LOCAL, description="Hub type")
    description: Optional[str] = Field(default=None, description="Hub description")
    version: str = Field(description="Hub version")
    enabled: bool = Field(default=True, description="Whether the hub is enabled")
    resources: List[str] = Field(
        default_factory=list, description="List of resource identifiers"
    )
    workflows: List[str] = Field(
        default_factory=list, description="List of workflow identifiers"
    )
    settings: Dict[str, Any] = Field(default_factory=dict, description="Hub settings")
    enable_hot_reload: bool = Field(
        default=False, description="Whether to enable hot-reload support"
    )
    manifest_path: Optional[Path] = Field(
        default=None, description="Path to the hub manifest file"
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary.

        Returns:
            Dict[str, Any]: Dictionary representation of config
        """
        return self.model_dump()


logger = logging.getLogger(__name__)


class Hub(Lifecycle):
    """Hub instance that manages resources and workflows."""

    def __init__(self, name: str, config: HubConfig) -> None:
        """Initialize hub.

        Args:
            name: Hub name
            config: Hub configuration
        """
        self.name = name
        self.config = config
        self.state = ComponentState.INITIALIZED
        self._workflow_engine = WorkflowEngine()
        self._resources: Dict[str, Any] = {}
        self._resource_deps: Dict[str, Set[str]] = {}
        self._metadata: Dict[str, Any] = {}

    async def initialize(self) -> None:
        """Initialize hub resources."""
        try:
            # Initialize workflow engine
            await self._workflow_engine.initialize()

            # Load resources
            for resource_id in self.config.resources:
                await self._load_resource(resource_id)

            # Load workflows
            for workflow_id in self.config.workflows:
                workflow_config = WorkflowConfig(
                    name=workflow_id, version=self.config.version, enabled=True
                )
                await self._workflow_engine.register_workflow(workflow_config)

            self.state = ComponentState.RUNNING
            logger.info(f"Hub initialized: {self.name}")

        except Exception as e:
            self.state = ComponentState.ERROR
            logger.error(f"Failed to initialize hub: {e}")
            raise

    async def cleanup(self) -> None:
        """Clean up hub resources."""
        try:
            # Clean up workflow engine
            await self._workflow_engine.cleanup()

            # Release resources in reverse dependency order
            resources = list(self._resources.keys())
            resources.sort(key=lambda x: len(self._resource_deps[x]), reverse=True)

            for resource_id in resources:
                await self._release_resource(resource_id)

            self.state = ComponentState.STOPPED
            logger.info(f"Hub cleaned up: {self.name}")

        except Exception as e:
            self.state = ComponentState.ERROR
            logger.error(f"Failed to clean up hub: {e}")
            raise

    async def _load_resource(self, resource_id: str) -> None:
        """Load a resource.

        Args:
            resource_id: Resource identifier

        Raises:
            Exception: If resource loading fails

        """
        # TODO: Implement resource loading
        pass

    async def _release_resource(self, resource_id: str) -> None:
        """Release a resource.

        Args:
            resource_id: Resource identifier

        Raises:
            Exception: If resource release fails

        """
        # TODO: Implement resource release
        pass

    async def get_workflow(self, name: str) -> Optional[WorkflowConfig]:
        """Get a workflow by name.

        Args:
            name: Workflow name

        Returns:
            Optional[WorkflowConfig]: Workflow configuration if found
        """
        return await self._workflow_engine.get_workflow(name)

    async def list_workflows(self) -> List[WorkflowConfig]:
        """List all workflows.

        Returns:
            List[WorkflowConfig]: List of workflow configurations
        """
        return await self._workflow_engine.list_workflows()
