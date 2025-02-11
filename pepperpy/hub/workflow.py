"""Workflow engine for executing declarative workflows.

This module provides the core workflow engine that processes workflow
definitions in YAML format and executes them using the appropriate agents.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import yaml
from jsonschema import ValidationError, validate
from pydantic import BaseModel, validator

from pepperpy.core.errors import WorkflowError
from pepperpy.hub.agents import AgentRegistry
from pepperpy.monitoring import logger


class WorkflowStep(BaseModel):
    """Model for a workflow step definition."""

    name: str
    method: str
    inputs: List[Dict[str, Any]]
    outputs: List[Dict[str, Any]]


class WorkflowContent(BaseModel):
    """Model for workflow content."""

    agent: Dict[str, str]
    steps: List[WorkflowStep]
    flow: List[Dict[str, Any]]
    validation: Dict[str, Any]


class WorkflowMetadata(BaseModel):
    """Model for workflow metadata."""

    created_at: str
    updated_at: str
    author: str
    dependencies: List[str]


class WorkflowDefinition(BaseModel):
    """Model for a complete workflow definition."""

    name: str
    type: str = "workflow"
    version: str
    description: str
    tags: List[str]
    content: WorkflowContent
    metadata: WorkflowMetadata

    @validator("type")
    def validate_type(cls, v: str) -> str:
        """Validate that type is 'workflow'."""
        if v != "workflow":
            raise ValueError("Type must be 'workflow'")
        return v

    class Config:
        """Pydantic model configuration."""

        validate_assignment = True


class WorkflowEngine:
    """Engine for loading and executing workflows."""

    def __init__(self, workflow_dir: Union[str, Path]) -> None:
        """Initialize the workflow engine.

        Args:
        ----
            workflow_dir: Directory containing workflow definitions.

        """
        self.workflow_dir = Path(workflow_dir)
        self.log = logger.bind(component="workflow_engine")

    def load_workflow(
        self, name: str, version: Optional[str] = None
    ) -> WorkflowDefinition:
        """Load a workflow definition from YAML.

        Args:
        ----
            name: Name of the workflow to load.
            version: Optional version string.

        Returns:
        -------
            WorkflowDefinition: The loaded workflow definition.

        Raises:
        ------
            WorkflowError: If workflow cannot be loaded.

        """
        # Find workflow directory
        workflow_path = self.workflow_dir / name
        if not workflow_path.exists():
            raise WorkflowError(f"Workflow directory not found: {workflow_path}")

        # Find specific version or latest
        if version:
            yaml_path = workflow_path / f"{version}.yaml"
        else:
            yaml_files = list(workflow_path.glob("*.yaml"))
            if not yaml_files:
                raise WorkflowError(f"No workflow definitions found in {workflow_path}")
            # Sort by version number and get latest
            yaml_path = max(
                yaml_files, key=lambda p: [int(x) for x in p.stem.split(".")]
            )

        try:
            with open(yaml_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
            return WorkflowDefinition(**data)
        except Exception as e:
            raise WorkflowError(f"Failed to load workflow: {str(e)}")

    def validate_input(
        self, workflow: WorkflowDefinition, input_data: Dict[str, Any]
    ) -> None:
        """Validate workflow input against schema.

        Args:
        ----
            workflow: Workflow definition.
            input_data: Input data to validate.

        Raises:
        ------
            WorkflowError: If input data is invalid.

        """
        try:
            validate(
                instance=input_data, schema=workflow.content.validation["input_schema"]
            )
        except ValidationError as e:
            raise WorkflowError(f"Invalid workflow input: {str(e)}")

    async def execute(
        self, workflow: WorkflowDefinition, input_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute a workflow with given input.

        Args:
        ----
            workflow: Workflow definition to execute.
            input_data: Input data for the workflow.

        Returns:
        -------
            Dict[str, Any]: Workflow execution results.

        Raises:
        ------
            WorkflowError: If workflow execution fails.

        """
        self.log.info(
            "Starting workflow execution",
            workflow=workflow.name,
            version=workflow.version,
        )

        # Validate input
        self.validate_input(workflow, input_data)

        # Get agent
        try:
            agent = AgentRegistry.get(
                workflow.content.agent["name"], workflow.content.agent.get("version")
            )
        except KeyError as e:
            raise WorkflowError(f"Failed to get agent: {str(e)}")

        # Initialize workflow context
        context = {"input": input_data, "output": {}, "step_outputs": {}}

        # Execute flow steps
        for step in workflow.content.flow:
            step_name = step["step"]
            step_def = next(s for s in workflow.content.steps if s.name == step_name)

            # Prepare step inputs
            step_inputs = {}
            for input_def in step["inputs"].items():
                key, value = input_def
                if isinstance(value, str) and value.startswith("${"):
                    # Resolve variable reference
                    ref = value[2:-1]  # Remove ${ and }
                    parts = ref.split(".")
                    current = context
                    for part in parts:
                        current = current[part]
                    step_inputs[key] = current
                else:
                    step_inputs[key] = value

            # Execute step
            self.log.debug(f"Executing step: {step_name}", inputs=step_inputs)
            try:
                method = getattr(agent, step_def.method)
                result = await method(**step_inputs)
            except Exception as e:
                raise WorkflowError(f"Failed to execute step {step_name}: {str(e)}")

            # Store step outputs
            context["step_outputs"][step_name] = result
            for output_def in step["outputs"].items():
                key, value = output_def
                if isinstance(value, str) and value.startswith("${"):
                    ref = value[2:-1].split(".")[-1]
                    context["output"][ref] = result

        # Validate output
        try:
            validate(
                instance=context["output"],
                schema=workflow.content.validation["output_schema"],
            )
        except ValidationError as e:
            raise WorkflowError(f"Invalid workflow output: {str(e)}")

        self.log.info(
            "Workflow execution completed",
            workflow=workflow.name,
            outputs=list(context["output"].keys()),
        )

        return context["output"]

    async def run(
        self,
        workflow_name: str,
        input_data: Dict[str, Any],
        version: Optional[str] = None,
    ) -> Dict[str, Any]:
        """High-level method to load and execute a workflow.

        Args:
        ----
            workflow_name: Name of the workflow to run.
            input_data: Input data for the workflow.
            version: Optional workflow version.

        Returns:
        -------
            Dict[str, Any]: Workflow execution results.

        """
        workflow = self.load_workflow(workflow_name, version)
        return await self.execute(workflow, input_data)

    def run_sync(
        self,
        workflow_name: str,
        input_data: Dict[str, Any],
        version: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Synchronous version of run method.

        Args:
        ----
            workflow_name: Name of the workflow to run.
            input_data: Input data for the workflow.
            version: Optional workflow version.

        Returns:
        -------
            Dict[str, Any]: Workflow execution results.

        """
        import asyncio

        return asyncio.run(self.run(workflow_name, input_data, version))
