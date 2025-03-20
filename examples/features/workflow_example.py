#!/usr/bin/env python3
"""
Example demonstrating the PepperPy Workflows module.
"""

import asyncio
import uuid
from typing import Any, Dict, List, Optional


class WorkflowStatus:
    """Enum-like class for workflow status."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class WorkflowStep:
    """Represents a step in a workflow."""

    def __init__(
        self,
        name: str,
        function: callable,
        inputs: Optional[Dict[str, Any]] = None,
        depends_on: Optional[List[str]] = None,
    ) -> None:
        """Initialize a workflow step."""
        self.id = str(uuid.uuid4())
        self.name = name
        self.function = function
        self.inputs = inputs or {}
        self.depends_on = depends_on or []
        self.status = WorkflowStatus.PENDING
        self.result = None
        self.error = None

    async def execute(self, context: Dict[str, Any]) -> Any:
        """Execute the step function with the given context."""
        try:
            self.status = WorkflowStatus.RUNNING
            # Prepare inputs from context
            resolved_inputs = {}
            for key, value in self.inputs.items():
                if isinstance(value, str) and value.startswith("$"):
                    # This is a reference to a context variable
                    context_key = value[1:]
                    if context_key in context:
                        resolved_inputs[key] = context[context_key]
                    else:
                        raise ValueError(f"Context variable {context_key} not found")
                else:
                    # This is a literal value
                    resolved_inputs[key] = value

            # Execute the function
            self.result = await self.function(**resolved_inputs)
            self.status = WorkflowStatus.COMPLETED
            return self.result
        except Exception as e:
            self.status = WorkflowStatus.FAILED
            self.error = str(e)
            raise


class Workflow:
    """Represents a workflow with multiple steps."""

    def __init__(self, name: str, description: Optional[str] = None) -> None:
        """Initialize a workflow."""
        self.id = str(uuid.uuid4())
        self.name = name
        self.description = description
        self.steps: Dict[str, WorkflowStep] = {}
        self.status = WorkflowStatus.PENDING
        self.context: Dict[str, Any] = {}

    def add_step(self, step: WorkflowStep) -> None:
        """Add a step to the workflow."""
        self.steps[step.id] = step

    async def execute(self) -> Dict[str, Any]:
        """Execute the workflow."""
        try:
            self.status = WorkflowStatus.RUNNING

            # Keep track of completed steps
            completed_steps = set()

            # Execute steps until all are completed
            while len(completed_steps) < len(self.steps):
                for step_id, step in self.steps.items():
                    if step_id in completed_steps:
                        continue

                    # Check if dependencies are satisfied
                    dependencies_satisfied = all(
                        dep_id in completed_steps for dep_id in step.depends_on
                    )

                    if dependencies_satisfied and step.status == WorkflowStatus.PENDING:
                        # Execute the step
                        try:
                            result = await step.execute(self.context)
                            # Add result to context
                            self.context[step.name] = result
                            completed_steps.add(step_id)
                        except Exception as e:
                            print(f"Step {step.name} failed: {e}")
                            self.status = WorkflowStatus.FAILED
                            return self.context

                # Small delay to prevent CPU spinning
                await asyncio.sleep(0.01)

            self.status = WorkflowStatus.COMPLETED
            return self.context
        except Exception as e:
            self.status = WorkflowStatus.FAILED
            print(f"Workflow failed: {e}")
            return self.context


# Example functions for workflow steps
async def fetch_data(url: str) -> Dict[str, Any]:
    """Simulate fetching data from a URL."""
    print(f"Fetching data from {url}...")
    await asyncio.sleep(1)  # Simulate network delay
    return {"title": "Sample Article", "content": "This is sample content."}


async def process_data(data: Dict[str, Any]) -> str:
    """Process the fetched data."""
    print(f"Processing data: {data['title']}...")
    await asyncio.sleep(0.5)  # Simulate processing time
    return f"Processed: {data['content']}"


async def format_result(processed_data: str) -> str:
    """Format the processed data."""
    print("Formatting result...")
    await asyncio.sleep(0.3)  # Simulate formatting time
    return f"FINAL OUTPUT: {processed_data}"


async def main() -> None:
    """Run the workflow example."""
    print("PepperPy Workflow Example")
    print("=========================")

    # Create a workflow
    workflow = Workflow(
        name="Data Processing Workflow",
        description="Fetches, processes, and formats data",
    )

    # Create steps
    fetch_step = WorkflowStep(
        name="fetch_data",
        function=fetch_data,
        inputs={"url": "https://example.com/api/data"},
    )

    process_step = WorkflowStep(
        name="process_data",
        function=process_data,
        inputs={"data": "$fetch_data"},
        depends_on=[fetch_step.id],
    )

    format_step = WorkflowStep(
        name="format_result",
        function=format_result,
        inputs={"processed_data": "$process_data"},
        depends_on=[process_step.id],
    )

    # Add steps to workflow
    workflow.add_step(fetch_step)
    workflow.add_step(process_step)
    workflow.add_step(format_step)

    # Execute workflow
    print("\nExecuting workflow...")
    results = await workflow.execute()

    print("\nWorkflow completed!")
    print(f"Final result: {results.get('format_result', 'No result')}")


if __name__ == "__main__":
    asyncio.run(main())
