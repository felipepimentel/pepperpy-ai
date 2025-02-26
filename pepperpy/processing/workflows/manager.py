"""Workflow manager module for the Pepperpy framework.

This module provides the workflow manager that handles workflow registration and discovery.
It manages workflow types, configurations, and provides a central point for workflow creation.
"""

import logging
from typing import Any
from uuid import UUID

from pepperpy.core.base import Lifecycle
from pepperpy.core.errors import WorkflowError
from pepperpy.core.types import ComponentState, WorkflowID
from pepperpy.hub.manager import get_hub_manager
from pepperpy.monitoring import (
    Counter,
    Histogram,
    get_metrics_manager,
    logger,
)
from pepperpy.resources.manager import ResourceManager
from pepperpy.workflows.base import BaseWorkflow, WorkflowConfig, WorkflowState
from pepperpy.workflows.engine import WorkflowEngine

logger = logging.getLogger(__name__)


class WorkflowManager(Lifecycle):
    """Workflow manager for the Pepperpy framework.

    This class provides functionality for:
    - Workflow type registration and discovery
    - Workflow configuration management
    - Workflow creation and lifecycle management
    - Workflow monitoring and metrics
    """

    def __init__(self) -> None:
        """Initialize workflow manager."""
        super().__init__()
        self._engine = WorkflowEngine()
        self._metrics_manager = get_metrics_manager()
        self._metrics: dict[str, Counter | Histogram] = {}
        self._workflow_types: dict[str, type[BaseWorkflow]] = {}
        self._resource_manager = ResourceManager.get_instance()
        self._hub_manager = get_hub_manager()

    async def initialize(self) -> None:
        """Initialize workflow manager."""
        try:
            # Initialize metrics
            workflow_types_counter = await self._metrics_manager.create_counter(
                name="workflow_types",
                description="Number of registered workflow types",
            )
            workflow_configs_counter = await self._metrics_manager.create_counter(
                name="workflow_configs",
                description="Number of loaded workflow configurations",
            )
            if not isinstance(workflow_types_counter, Counter):
                raise WorkflowError("Failed to create workflow types counter")
            if not isinstance(workflow_configs_counter, Counter):
                raise WorkflowError("Failed to create workflow configs counter")
            self._metrics["workflow_types"] = workflow_types_counter
            self._metrics["workflow_configs"] = workflow_configs_counter

            # Initialize engine
            await self._engine.initialize()

            self._state = ComponentState.READY
            logger.info("Workflow manager initialized")

        except Exception as e:
            self._state = ComponentState.ERROR
            logger.error("Failed to initialize workflow manager: %s", str(e))
            raise WorkflowError(f"Failed to initialize workflow manager: {e}")

    async def cleanup(self) -> None:
        """Clean up workflow manager."""
        try:
            # Clean up engine
            await self._engine.cleanup()

            self._state = ComponentState.CLEANED
            logger.info("Workflow manager cleaned up")

        except Exception as e:
            self._state = ComponentState.ERROR
            logger.error("Failed to clean up workflow manager: %s", str(e))
            raise WorkflowError(f"Failed to clean up workflow manager: {e}")

    async def register_workflow(self, workflow_type: type[BaseWorkflow]) -> None:
        """Register a workflow type.

        Args:
            workflow_type: Workflow type to register
        """
        name = workflow_type.__name__
        self._workflow_types[name] = workflow_type
        if isinstance(self._metrics["workflow_types"], Counter):
            await self._metrics["workflow_types"].inc()
        logger.info("Registered workflow type: %s", name)

    async def load_workflow_config(
        self, name: str, version: str = "v1.0.0"
    ) -> dict[str, Any]:
        """Load workflow configuration.

        Args:
            name: Name of the workflow configuration
            version: Version of the configuration

        Returns:
            Workflow configuration

        Raises:
            WorkflowError: If configuration loading fails
        """
        try:
            config = self._hub_manager.load_config("workflows", name, version)
            if isinstance(self._metrics["workflow_configs"], Counter):
                await self._metrics["workflow_configs"].inc()
            return config

        except Exception as e:
            logger.error("Failed to load workflow config: %s", str(e))
            raise WorkflowError(f"Failed to load workflow config: {e}")

    async def create_workflow(
        self,
        workflow_type: str,
        config: WorkflowConfig,
    ) -> WorkflowID:
        """Create a new workflow instance.

        Args:
            workflow_type: Type of workflow to create
            config: Workflow configuration

        Returns:
            ID of the created workflow

        Raises:
            WorkflowError: If workflow creation fails
        """
        try:
            if workflow_type not in self._workflow_types:
                raise WorkflowError(f"Unknown workflow type: {workflow_type}")

            workflow_class = self._workflow_types[workflow_type]
            workflow = workflow_class(config=config)
            await workflow.initialize()
            workflow_id = workflow.id
            logger.info("Created workflow: %s (type: %s)", workflow_id, workflow_type)
            return workflow_id

        except Exception as e:
            logger.error("Failed to create workflow: %s", str(e))
            raise WorkflowError(f"Failed to create workflow: {e}")

    async def start_workflow(self, workflow_id: str | UUID | WorkflowID) -> None:
        """Start a workflow.

        Args:
            workflow_id: ID of the workflow to start

        Raises:
            WorkflowError: If workflow start fails
        """
        try:
            if isinstance(workflow_id, str):
                workflow_id = WorkflowID(workflow_id)
            elif isinstance(workflow_id, UUID):
                workflow_id = WorkflowID(str(workflow_id))

            await self._engine.start_workflow(workflow_id)

        except Exception as e:
            logger.error("Failed to start workflow: %s", str(e))
            raise WorkflowError(f"Failed to start workflow: {e}")

    async def stop_workflow(self, workflow_id: str | UUID | WorkflowID) -> None:
        """Stop a workflow.

        Args:
            workflow_id: ID of the workflow to stop

        Raises:
            WorkflowError: If workflow stop fails
        """
        try:
            if isinstance(workflow_id, str):
                workflow_id = WorkflowID(workflow_id)
            elif isinstance(workflow_id, UUID):
                workflow_id = WorkflowID(str(workflow_id))

            await self._engine.stop_workflow(workflow_id)

        except Exception as e:
            logger.error("Failed to stop workflow: %s", str(e))
            raise WorkflowError(f"Failed to stop workflow: {e}")

    async def get_workflow_state(
        self, workflow_id: str | UUID | WorkflowID
    ) -> WorkflowState:
        """Get workflow state.

        Args:
            workflow_id: ID of the workflow

        Returns:
            Current state of the workflow

        Raises:
            WorkflowError: If getting workflow state fails
        """
        try:
            if isinstance(workflow_id, str):
                workflow_id = WorkflowID(workflow_id)
            elif isinstance(workflow_id, UUID):
                workflow_id = WorkflowID(str(workflow_id))

            workflow = self._engine.get_workflow(workflow_id)
            return workflow.state

        except Exception as e:
            logger.error("Failed to get workflow state: %s", str(e))
            raise WorkflowError(f"Failed to get workflow state: {e}")

    def get_workflow(self, workflow_id: UUID | str) -> BaseWorkflow:
        """Get workflow instance.

        Args:
            workflow_id: ID of workflow to get

        Returns:
            Workflow instance

        Raises:
            ValueError: If workflow not found
        """
        return self._engine.get_workflow(workflow_id)

    def list_workflows(self) -> list[dict[str, Any]]:
        """List all registered workflows.

        Returns:
            List of workflow information dictionaries
        """
        return self._engine.list_workflows()

    def list_workflow_types(self) -> list[str]:
        """List all registered workflow types.

        Returns:
            List of registered workflow type names
        """
        return list(self._workflow_types.keys())
