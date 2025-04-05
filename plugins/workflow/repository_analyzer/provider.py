"""
Provider for repository analyzer workflow.
"""

import logging
from typing import Any

from pepperpy.workflow.base import WorkflowProvider

from .workflow import RepositoryAnalyzerWorkflow

logger = logging.getLogger(__name__)


class RepositoryAnalyzerAdapter(WorkflowProvider):
    """Adapter for RepositoryAnalyzerWorkflow to work with the plugin system.

    This adapter bypasses the ContentGeneratorWorkflow inheritance chain to avoid
    input validation issues.
    """

    def __init__(self, **kwargs: Any) -> None:
        """Initialize the adapter.

        Args:
            **kwargs: Provider configuration
        """
        super().__init__(**kwargs)
        # Create the actual workflow implementation
        self.workflow_impl = RepositoryAnalyzerWorkflow(**kwargs)
        self._workflows = {}  # Required by the WorkflowProvider base class

    async def initialize(self) -> None:
        """Initialize the provider."""
        if not self.initialized:
            await self.workflow_impl.initialize()
            self.initialized = True

    async def cleanup(self) -> None:
        """Clean up resources."""
        if self.initialized:
            await self.workflow_impl.cleanup()
            self.initialized = False

    async def execute(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """Execute the workflow with any input.

        This method bypasses the ContentGeneratorWorkflow.execute method
        and directly routes to the appropriate analyzer method.

        Args:
            input_data: Input data in any format

        Returns:
            Dictionary with analysis results
        """
        if not self.initialized:
            await self.initialize()

        # CRITICAL: Fix for ContentGeneratorWorkflow's topic validation
        input_data["topic"] = "repository analysis"

        # Extract task and input from CLI-formatted input
        task = input_data.get("task", "analyze_repository")
        task_input = input_data.get("input", {})
        options = input_data.get("options", {})

        logger.info(f"Executing repository analysis task: {task}")
        logger.debug(f"Input data: {input_data}")

        # Prepare our analyzer configuration
        analysis_config = {}

        # Copy all parameters from the task input
        analysis_config.update(task_input)

        # Add options to config
        analysis_config.update(options)

        # Execute the appropriate analysis based on the task
        try:
            if task == "analyze_repository":
                return await self.workflow_impl._analyze_repository(analysis_config)
            elif task == "analyze_code_quality":
                return await self.workflow_impl._analyze_code_quality(analysis_config)
            elif task == "analyze_structure":
                return await self.workflow_impl._analyze_structure(analysis_config)
            elif task == "analyze_complexity":
                return await self.workflow_impl._analyze_complexity(analysis_config)
            else:
                return {
                    "status": "error",
                    "message": f"Unknown task: {task}. Please use one of: analyze_repository, analyze_code_quality, analyze_structure, analyze_complexity",
                }
        except Exception as e:
            logger.error(f"Error executing task '{task}': {e}")
            return {"status": "error", "message": str(e)}

    async def create_workflow(
        self,
        name: str,
        components: list["WorkflowComponent"],
        config: dict[str, Any] | None = None,
    ) -> "Workflow":
        """Create a new workflow.

        Args:
            name: Workflow name
            components: List of workflow components
            config: Optional workflow configuration

        Returns:
            Created workflow instance
        """
        # Just delegate to the workflow implementation
        return await self.workflow_impl.create_workflow(name, components, config)

    async def execute_workflow(
        self,
        workflow: "Workflow",
        input_data: Any | None = None,
        config: dict[str, Any] | None = None,
    ) -> Any:
        """Execute a workflow.

        Args:
            workflow: Workflow to execute
            input_data: Optional input data
            config: Optional execution configuration

        Returns:
            Workflow execution result
        """
        # Just delegate to the workflow implementation
        return await self.workflow_impl.execute_workflow(workflow, input_data, config)

    async def get_workflow(self, workflow_id: str) -> "Workflow | None":
        """Get workflow by ID.

        Args:
            workflow_id: Workflow identifier

        Returns:
            Workflow instance or None if not found
        """
        # Just delegate to the workflow implementation
        return await self.workflow_impl.get_workflow(workflow_id)

    async def list_workflows(self) -> list["Workflow"]:
        """List all workflows.

        Returns:
            List of workflows
        """
        # Just delegate to the workflow implementation
        return await self.workflow_impl.list_workflows()


# Re-export the class for plugin discovery
__all__ = ["RepositoryAnalyzerAdapter"]
