"""Workflow Service for PepperPy API

This module defines the workflow service interface and implementation for
managing and executing PepperPy workflows.
"""

import importlib
import os
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml

from .base import BaseService


class WorkflowService(BaseService):
    """Service for workflow operations.

    This service provides methods for discovering available workflows,
    retrieving workflow metadata, and executing workflows.
    """

    def __init__(self) -> None:
        """Initialize the workflow service."""
        super().__init__()
        self._workflows: dict[str, dict[str, Any]] = {}

    async def initialize(self) -> None:
        """Initialize workflow service resources."""
        if self._initialized:
            return

        try:
            # Load available workflows from plugin directory
            await self._load_workflows()

            self._initialized = True
            self.logger.info("Workflow service initialized")
        except Exception as e:
            self.logger.error(f"Failed to initialize workflow service: {e}")
            raise

    async def cleanup(self) -> None:
        """Clean up workflow service resources."""
        if not self._initialized:
            return

        try:
            # Clean up any resources (workflow providers, etc.)
            self._workflows = {}

            self._initialized = False
            self.logger.info("Workflow service cleaned up")
        except Exception as e:
            self.logger.error(f"Error during workflow service cleanup: {e}")

    async def get_workflows(self) -> list[dict[str, Any]]:
        """Get all available workflows.

        Returns:
            List of workflow metadata
        """
        if not self._initialized:
            await self.initialize()

        return [
            {
                "id": workflow_id,
                "name": details.get("name", ""),
                "description": details.get("description", ""),
                "category": details.get("category", "other"),
                "version": details.get("version", "0.1.0"),
            }
            for workflow_id, details in self._workflows.items()
        ]

    async def get_workflow_schema(self, workflow_id: str) -> dict[str, Any]:
        """Get the schema for a specific workflow.

        Args:
            workflow_id: ID of the workflow

        Returns:
            Workflow schema

        Raises:
            ValueError: If workflow not found
        """
        if not self._initialized:
            await self.initialize()

        if workflow_id not in self._workflows:
            raise ValueError(f"Workflow not found: {workflow_id}")

        workflow = self._workflows[workflow_id]
        return {
            "id": workflow_id,
            "name": workflow.get("name", ""),
            "description": workflow.get("description", ""),
            "schema": workflow.get("schema", {}),
            "version": workflow.get("version", "0.1.0"),
        }

    async def execute_workflow(
        self,
        workflow_id: str,
        input_data: dict[str, Any],
        config: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Execute a workflow.

        Args:
            workflow_id: ID of the workflow to execute
            input_data: Input data for the workflow
            config: Optional configuration for the workflow

        Returns:
            Workflow execution result

        Raises:
            ValueError: If workflow not found
        """
        if not self._initialized:
            await self.initialize()

        if workflow_id not in self._workflows:
            raise ValueError(f"Workflow not found: {workflow_id}")

        try:
            # Get workflow provider
            provider = await self._get_workflow_provider(workflow_id, config)

            # Execute workflow
            start_time = datetime.now()
            result = await provider.execute(input_data)
            execution_time = (datetime.now() - start_time).total_seconds()

            # Clean up provider
            await provider.cleanup()

            # Return result with metadata
            return {
                "status": "success",
                "workflow_id": workflow_id,
                "execution_time": execution_time,
                "timestamp": datetime.now().isoformat(),
                "result": result,
            }
        except Exception as e:
            self.logger.error(f"Error executing workflow {workflow_id}: {e}")
            return {
                "status": "error",
                "workflow_id": workflow_id,
                "timestamp": datetime.now().isoformat(),
                "error": str(e),
            }

    async def _load_workflows(self) -> None:
        """Load available workflows from plugins directory."""
        self._workflows = {}

        # Get plugin directory from environment or use default
        plugin_dir = os.environ.get("PEPPERPY_PLUGIN_DIR", "plugins")
        workflow_dir = Path(plugin_dir) / "workflow"

        if not workflow_dir.exists():
            self.logger.warning(f"Workflow directory not found: {workflow_dir}")
            return

        for plugin_dir in workflow_dir.iterdir():
            if not plugin_dir.is_dir():
                continue

            # Check for plugin.yaml
            plugin_yaml = plugin_dir / "plugin.yaml"
            if not plugin_yaml.exists():
                continue

            try:
                # Load plugin metadata
                with open(plugin_yaml) as f:
                    plugin_data = yaml.safe_load(f)

                # Extract workflow information
                workflow_id = plugin_data.get("name", "").lower().replace(" ", "_")
                workflow_info = {
                    "id": workflow_id,
                    "name": plugin_data.get("name", ""),
                    "description": plugin_data.get("description", ""),
                    "version": plugin_data.get("version", "0.1.0"),
                    "category": plugin_data.get("category", "other"),
                    "entry_point": plugin_data.get("entry_point", ""),
                    "config_schema": plugin_data.get("config_schema", {}),
                    "schema": plugin_data.get("config_schema", {}),
                }

                # Register workflow
                self._workflows[workflow_id] = workflow_info
                self.logger.info(f"Registered workflow: {workflow_id}")
            except Exception as e:
                self.logger.error(f"Error loading workflow from {plugin_dir}: {e}")

    async def _get_workflow_provider(
        self, workflow_id: str, config: dict[str, Any] | None = None
    ) -> Any:
        """Get workflow provider instance.

        Args:
            workflow_id: ID of the workflow
            config: Optional configuration for the workflow

        Returns:
            Workflow provider instance
        """
        workflow = self._workflows[workflow_id]
        entry_point = workflow.get("entry_point", "")

        if not entry_point or "." not in entry_point:
            raise ValueError(
                f"Invalid entry point for workflow {workflow_id}: {entry_point}"
            )

        # Parse entry point
        module_path, class_name = entry_point.split(".", 1)
        module_path = f"plugins.workflow.{workflow_id}.{module_path}"

        try:
            # Import module
            module = importlib.import_module(module_path)

            # Get provider class
            provider_class = getattr(module, class_name)

            # Create provider instance with config
            config = config or {}
            provider = provider_class(**config)

            # Initialize provider
            await provider.initialize()

            return provider
        except Exception as e:
            self.logger.error(f"Error creating provider for {workflow_id}: {e}")
            raise


# Create a singleton instance
workflow_service = WorkflowService()
