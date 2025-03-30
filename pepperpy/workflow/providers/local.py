"""Local workflow execution for PepperPy.

This module provides local execution capabilities for workflows,
allowing them to run in the same process as the application.
"""

import logging
from typing import Any, Dict, List, Optional

from pepperpy.core.providers import LocalProvider
from pepperpy.core.utils import lazy_provider_class
from pepperpy.workflow.base import (
    ComponentType,
    PipelineContext,
    PipelineError,
    Workflow,
    WorkflowComponent,
)

logger = logging.getLogger(__name__)


@lazy_provider_class("workflow", "local")
class LocalExecutor(LocalProvider):
    """Local workflow executor.

    Executes workflows in the local process, managing component
    execution and data flow between components.
    """

    def __init__(
        self,
        config: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize local executor.

        Args:
            config: Optional executor configuration
            metadata: Optional executor metadata
        """
        self.config = config or {}
        self.metadata = metadata
        self._workflows: Dict[str, Workflow] = {}

    async def execute_workflow(
        self,
        workflow: Workflow,
        input_data: Optional[Any] = None,
        config: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Execute a workflow locally.

        Args:
            workflow: Workflow to execute
            input_data: Optional input data
            config: Optional execution configuration

        Returns:
            Dictionary with workflow execution results

        Raises:
            PipelineError: If execution fails
        """
        try:
            # Update workflow status
            workflow.status = ComponentType.PROCESSOR
            workflow.config.update(config or {})

            # Execute components in sequence
            current_data = input_data or workflow.config.get("file_path")
            for component in workflow.components:
                try:
                    # Create execution context
                    context = PipelineContext(
                        data={
                            "workflow_id": workflow.id,
                            "component_id": component.id,
                            "input_data": current_data,
                            "config": workflow.config,
                            "metadata": workflow.metadata,
                        }
                    )

                    # Execute component
                    logger.info(
                        f"Executing component {component.name} in workflow {workflow.name}"
                    )
                    current_data = await self._execute_component(component, context)

                except Exception as e:
                    logger.error(
                        f"Component {component.name} failed in workflow {workflow.name}: {e}"
                    )
                    workflow.status = ComponentType.SINK
                    raise PipelineError(f"Component execution failed: {str(e)}") from e

            # Update workflow status
            workflow.status = ComponentType.SINK
            return {"text": current_data} if current_data else {}

        except Exception as e:
            logger.error(f"Workflow {workflow.name} execution failed: {e}")
            workflow.status = ComponentType.SINK
            raise PipelineError(f"Workflow execution failed: {str(e)}") from e

    async def _execute_component(
        self,
        component: WorkflowComponent,
        context: PipelineContext,
    ) -> Any:
        """Execute a single component.

        Args:
            component: Component to execute
            context: Execution context

        Returns:
            Component output data

        Raises:
            PipelineError: If component execution fails
        """
        try:
            return await component.process(context.data.get("input_data"))
        except Exception as e:
            raise PipelineError(f"Component execution failed: {str(e)}") from e

    def get_workflow(self, workflow_id: str) -> Workflow:
        """Get workflow by ID.

        Args:
            workflow_id: Workflow identifier

        Returns:
            Workflow instance

        Raises:
            PipelineError: If workflow not found
        """
        if workflow_id not in self._workflows:
            raise PipelineError(f"Workflow {workflow_id} not found")
        return self._workflows[workflow_id]

    def list_workflows(
        self,
        status: Optional[ComponentType] = None,
    ) -> List[Workflow]:
        """List workflows with optional status filter.

        Args:
            status: Optional status filter

        Returns:
            List of matching workflows
        """
        if status is None:
            return list(self._workflows.values())
        return [w for w in self._workflows.values() if w.status == status]

    async def cleanup(self) -> None:
        """Clean up resources.

        This method is called when the provider is being shut down.
        """
        # Clear workflows
        self._workflows.clear()
