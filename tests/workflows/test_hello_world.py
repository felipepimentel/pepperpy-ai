"""Tests for hello world workflow."""

import pytest

from pepperpy.workflowss.examples.hello_world import HelloWorldWorkflow
from pepperpy.workflowss.execution.executor import WorkflowExecutor


@pytest.mark.asyncio
async def test_hello_world_workflow() -> None:
    """Test hello world workflow execution."""
    # Create workflow
    workflow = HelloWorldWorkflow()

    # Create executor
    executor = WorkflowExecutor()

    # Execute workflow
    results = await executor.execute(workflow)

    # Verify results
    assert results["hello"] == "Hello"
    assert results["world"] == "World"
