"""Example usage of the unified workflow system.

This module provides examples of how to use the workflow system.
"""

import asyncio
from typing import Any, Dict

from .base import BaseWorkflow, WorkflowStep
from .builder import WorkflowBuilder
from .factory import default_factory


async def simple_workflow_example() -> None:
    """Example of creating and executing a simple workflow."""
    # Create a workflow definition
    builder = WorkflowBuilder("data_processing")

    # Add steps
    builder.add_step(
        "fetch_data", "Fetch Data", "http_get", {"url": "https://example.com/data"}
    )
    builder.add_step("process_data", "Process Data", "transform", {"format": "json"})
    builder.depends_on("fetch_data")
    builder.add_step(
        "store_data", "Store Data", "database_write", {"table": "processed_data"}
    )
    builder.depends_on("process_data")

    # Build the workflow definition
    definition = builder.build()

    # Create a workflow instance
    workflow = default_factory.create(definition)

    # Execute the workflow
    results = await workflow.execute({"api_key": "your_api_key"})
    print(f"Workflow results: {results}")


class DataProcessingWorkflow(BaseWorkflow):
    """Custom workflow implementation for data processing."""

    async def _execute_step(self, step: WorkflowStep, context: Dict[str, Any]) -> Any:
        """Execute a single step with custom logic.

        Args:
            step: Step to execute
            context: Execution context

        Returns:
            Step result
        """
        print(f"Executing step: {step.name} ({step.action})")

        if step.action == "http_get":
            # Simulate fetching data
            url = step.parameters.get("url", "")
            print(f"Fetching data from {url}")
            return {"data": "Sample data", "source": url}

        elif step.action == "transform":
            # Simulate data transformation
            format_type = step.parameters.get("format", "")
            input_data = context.get(step.dependencies[0], {}).get("data", "")
            print(f"Transforming data to {format_type}")
            return {"data": f"Transformed: {input_data}", "format": format_type}

        elif step.action == "database_write":
            # Simulate database write
            table = step.parameters.get("table", "")
            input_data = context.get(step.dependencies[0], {}).get("data", "")
            print(f"Writing data to table {table}")
            return {"status": "success", "table": table, "records": 1}

        # Fall back to default implementation
        return await super()._execute_step(step, context)


async def custom_workflow_example() -> None:
    """Example of creating and executing a custom workflow."""
    # Register the custom workflow
    default_factory.register_workflow("data_processing", DataProcessingWorkflow)

    # Create a workflow definition
    builder = WorkflowBuilder("data_processing")
    builder.with_metadata("workflow_type", "data_processing")

    # Add steps
    builder.add_step(
        "fetch_data", "Fetch Data", "http_get", {"url": "https://example.com/data"}
    )
    builder.add_step("process_data", "Process Data", "transform", {"format": "json"})
    builder.depends_on("fetch_data")
    builder.add_step(
        "store_data", "Store Data", "database_write", {"table": "processed_data"}
    )
    builder.depends_on("process_data")

    # Build the workflow definition
    definition = builder.build()

    # Create a workflow instance
    workflow = default_factory.create(definition)

    # Execute the workflow
    results = await workflow.execute()
    print(f"Custom workflow results: {results}")


async def dictionary_workflow_example() -> None:
    """Example of creating a workflow from a dictionary."""
    workflow_data = {
        "name": "data_pipeline",
        "metadata": {"workflow_type": "data_processing", "version": "1.0"},
        "steps": {
            "step1": {
                "name": "Extract Data",
                "action": "extract",
                "parameters": {"source": "database"},
                "dependencies": [],
            },
            "step2": {
                "name": "Transform Data",
                "action": "transform",
                "parameters": {"operations": ["filter", "map"]},
                "dependencies": ["step1"],
            },
            "step3": {
                "name": "Load Data",
                "action": "load",
                "parameters": {"destination": "warehouse"},
                "dependencies": ["step2"],
            },
        },
    }

    # Create a workflow instance
    workflow = default_factory.create_from_dict(workflow_data)

    # Execute the workflow
    results = await workflow.execute()
    print(f"Dictionary workflow results: {results}")


async def run_examples() -> None:
    """Run all examples."""
    print("Running simple workflow example...")
    await simple_workflow_example()

    print("\nRunning custom workflow example...")
    await custom_workflow_example()

    print("\nRunning dictionary workflow example...")
    await dictionary_workflow_example()


if __name__ == "__main__":
    asyncio.run(run_examples())
