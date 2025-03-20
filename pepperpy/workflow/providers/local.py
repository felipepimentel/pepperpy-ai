"""Local workflow execution for PepperPy.

This module provides local execution capabilities for workflows,
allowing them to run in the same process as the application.
"""

import logging
from typing import Any, Dict, List, Optional

from pepperpy.core.providers import LocalProvider
from pepperpy.workflow.base import (
    WorkflowBase,
    WorkflowComponent,
    WorkflowContext,
    WorkflowError,
    WorkflowStatus,
)

logger = logging.getLogger(__name__)


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
        self._workflows: Dict[str, WorkflowBase] = {}

    async def execute_workflow(
        self,
        workflow: WorkflowBase,
        input_data: Optional[Any] = None,
        config: Optional[Dict[str, Any]] = None,
    ) -> WorkflowBase:
        """Execute a workflow locally.

        Args:
            workflow: Workflow to execute
            input_data: Optional input data
            config: Optional execution configuration

        Returns:
            Updated workflow with execution results

        Raises:
            WorkflowError: If execution fails
        """
        try:
            # Update workflow status
            workflow.status = WorkflowStatus.RUNNING
            workflow.config.update(config or {})

            # Execute components in sequence
            current_data = input_data
            for component in workflow.components:
                try:
                    # Create execution context
                    context = WorkflowContext(
                        workflow_id=workflow.id,
                        component_id=component.id,
                        input_data=current_data,
                        config=workflow.config,
                        metadata=workflow.metadata,
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
                    workflow.status = WorkflowStatus.FAILED
                    raise WorkflowError(f"Component execution failed: {str(e)}")

            # Update workflow status
            workflow.status = WorkflowStatus.COMPLETED
            return workflow

        except Exception as e:
            logger.error(f"Workflow {workflow.name} execution failed: {e}")
            workflow.status = WorkflowStatus.FAILED
            raise WorkflowError(f"Workflow execution failed: {str(e)}")

    async def _execute_component(
        self,
        component: WorkflowComponent,
        context: WorkflowContext,
    ) -> Any:
        """Execute a single component.

        Args:
            component: Component to execute
            context: Execution context

        Returns:
            Component output data

        Raises:
            WorkflowError: If component execution fails
        """
        try:
            return await component.process(context.input_data)
        except Exception as e:
            raise WorkflowError(f"Component execution failed: {str(e)}")

    def get_workflow(self, workflow_id: str) -> WorkflowBase:
        """Get workflow by ID.

        Args:
            workflow_id: Workflow identifier

        Returns:
            Workflow instance

        Raises:
            WorkflowError: If workflow not found
        """
        if workflow_id not in self._workflows:
            raise WorkflowError(f"Workflow {workflow_id} not found")
        return self._workflows[workflow_id]

    def list_workflows(
        self,
        status: Optional[WorkflowStatus] = None,
    ) -> List[WorkflowBase]:
        """List workflows with optional status filter.

        Args:
            status: Optional status filter

        Returns:
            List of matching workflows
        """
        if status is None:
            return list(self._workflows.values())
        return [w for w in self._workflows.values() if w.status == status]
