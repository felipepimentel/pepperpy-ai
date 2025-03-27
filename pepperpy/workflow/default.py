"""Default workflow provider for PepperPy."""

from typing import Any, Dict, List, cast

from pepperpy.core.base import WorkflowProvider
from pepperpy.exceptions import ValidationError
from pepperpy.workflow.base import Workflow, WorkflowComponent


class DefaultWorkflow(Workflow):
    """Default workflow implementation."""

    def __init__(self) -> None:
        """Initialize default workflow."""
        super().__init__()
        self.name: str = ""
        self._components: List[WorkflowComponent] = []
        self._config: Dict[str, Any] = {}

    @property
    def components(self) -> List[WorkflowComponent]:
        """Get workflow components.

        Returns:
            List of workflow components
        """
        return self._components

    def set_components(self, components: List[WorkflowComponent]) -> None:
        """Set workflow components.

        Args:
            components: List of workflow components
        """
        self._components = components

    def set_config(self, config: Dict[str, Any]) -> None:
        """Set workflow configuration.

        Args:
            config: Configuration dictionary
        """
        self._config = config


class DefaultProvider(WorkflowProvider):
    """Default workflow provider implementation."""

    def __init__(self, **kwargs: Any) -> None:
        """Initialize default workflow provider.

        Args:
            **kwargs: Additional configuration options
        """
        super().__init__(**kwargs)
        self._workflows: Dict[str, DefaultWorkflow] = {}

    async def initialize(self) -> None:
        """Initialize the workflow provider."""
        pass

    async def create_workflow(self, workflow_id: str, **kwargs: Any) -> DefaultWorkflow:
        """Create a new workflow.

        Args:
            workflow_id: Unique workflow identifier
            **kwargs: Additional workflow configuration

        Returns:
            Created workflow instance

        Raises:
            ValidationError if workflow already exists
        """
        if workflow_id in self._workflows:
            raise ValidationError(f"Workflow already exists: {workflow_id}")

        workflow = DefaultWorkflow()
        workflow.name = kwargs.get("name", "")
        workflow.set_components(kwargs.get("components", []))
        workflow.set_config(kwargs.get("config", {}))
        self._workflows[workflow_id] = workflow
        return workflow

    async def get_workflow(self, workflow_id: str) -> DefaultWorkflow:
        """Get an existing workflow.

        Args:
            workflow_id: Workflow identifier

        Returns:
            Workflow instance

        Raises:
            ValidationError if workflow not found
        """
        if workflow_id not in self._workflows:
            raise ValidationError(f"Workflow not found: {workflow_id}")

        return self._workflows[workflow_id]

    async def delete_workflow(self, workflow_id: str) -> None:
        """Delete a workflow.

        Args:
            workflow_id: Workflow identifier

        Raises:
            ValidationError if workflow not found
        """
        if workflow_id not in self._workflows:
            raise ValidationError(f"Workflow not found: {workflow_id}")

        del self._workflows[workflow_id]

    async def list_workflows(self) -> List[str]:
        """List all workflow IDs.

        Returns:
            List of workflow IDs
        """
        return list(self._workflows.keys())

    async def execute_workflow(self, workflow_id: str, data: Any) -> Any:
        """Execute a workflow.

        Args:
            workflow_id: Workflow identifier
            data: Input data for workflow

        Returns:
            Workflow execution result

        Raises:
            ValidationError if workflow not found
        """
        workflow = await self.get_workflow(workflow_id)
        default_workflow = cast(DefaultWorkflow, workflow)

        result = data
        for component in default_workflow.components:
            result = await component.process(result)

        return result
