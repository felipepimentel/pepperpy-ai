"""Tests for the workflow management system."""

import asyncio
from typing import AsyncGenerator

import pytest

from pepperpy.core.workflows import (
    WorkflowContext,
    WorkflowEngine,
    WorkflowError,
    WorkflowState,
    WorkflowStep,
)


@pytest.fixture
def simple_workflow() -> list[WorkflowStep]:
    """Create a simple workflow for testing."""
    return [
        WorkflowStep(
            name="step1",
            action="test_action",
            inputs={"input1": "value1"},
            outputs=["result1"],
        ),
        WorkflowStep(
            name="step2",
            action="test_action",
            inputs={"input2": "value2"},
            outputs=["result2"],
            condition="context.variables.get('result1') == 'Executed test_action'",
        ),
    ]


@pytest.fixture
async def workflow_engine() -> AsyncGenerator[WorkflowEngine, None]:
    """Create a workflow engine instance."""
    engine = WorkflowEngine()
    await engine.initialize()
    yield engine
    await engine.cleanup()


@pytest.mark.asyncio
async def test_workflow_registration(
    workflow_engine: WorkflowEngine, simple_workflow: list[WorkflowStep]
):
    """Test workflow registration."""
    await workflow_engine.register("test_workflow", simple_workflow)

    # Test duplicate registration
    with pytest.raises(WorkflowError):
        await workflow_engine.register("test_workflow", simple_workflow)

    # Test empty workflow
    with pytest.raises(WorkflowError):
        await workflow_engine.register("empty_workflow", [])

    # Test duplicate step names
    duplicate_steps = [
        WorkflowStep(name="step1", action="action1", inputs={}),
        WorkflowStep(name="step1", action="action2", inputs={}),
    ]
    with pytest.raises(WorkflowError):
        await workflow_engine.register("duplicate_workflow", duplicate_steps)


@pytest.mark.asyncio
async def test_workflow_execution(
    workflow_engine: WorkflowEngine, simple_workflow: list[WorkflowStep]
):
    """Test workflow execution."""
    await workflow_engine.register("test_workflow", simple_workflow)

    # Test successful execution
    result = await workflow_engine.execute("test_workflow", {"initial": "value"})
    assert "result1" in result
    assert "result2" in result

    # Test non-existent workflow
    with pytest.raises(WorkflowError):
        await workflow_engine.execute("non_existent", {})

    # Test concurrent execution of same workflow
    task1 = asyncio.create_task(workflow_engine.execute("test_workflow", {}))
    task2 = asyncio.create_task(workflow_engine.execute("test_workflow", {}))

    with pytest.raises(WorkflowError):
        await asyncio.gather(task1, task2)


@pytest.mark.asyncio
async def test_workflow_conditions(workflow_engine: WorkflowEngine):
    """Test conditional step execution."""
    steps = [
        WorkflowStep(
            name="step1",
            action="test_action",
            inputs={},
            outputs=["result1"],
        ),
        WorkflowStep(
            name="step2",
            action="test_action",
            inputs={},
            condition="context.variables.get('result1') == 'wrong_value'",
        ),
    ]

    await workflow_engine.register("conditional_workflow", steps)
    result = await workflow_engine.execute("conditional_workflow", {})

    # Step2 should be skipped due to condition
    assert "result1" in result
    assert len(result) == 1


@pytest.mark.asyncio
async def test_workflow_timeouts(workflow_engine: WorkflowEngine):
    """Test step timeout handling."""
    steps = [
        WorkflowStep(
            name="timeout_step",
            action="test_action",
            inputs={},
            timeout=0.1,
        ),
    ]

    await workflow_engine.register("timeout_workflow", steps)
    with pytest.raises(WorkflowError) as exc_info:
        await workflow_engine.execute("timeout_workflow", {})
    assert "timed out" in str(exc_info.value)


@pytest.mark.asyncio
async def test_workflow_retries(workflow_engine: WorkflowEngine):
    """Test step retry handling."""
    steps = [
        WorkflowStep(
            name="retry_step",
            action="test_action",
            inputs={},
            retry_config={"max_retries": 2, "delay": 0.1},
        ),
    ]

    await workflow_engine.register("retry_workflow", steps)
    result = await workflow_engine.execute("retry_workflow", {})
    assert result["result"] == "Executed test_action"


@pytest.mark.asyncio
async def test_workflow_cancellation(
    workflow_engine: WorkflowEngine, simple_workflow: list[WorkflowStep]
):
    """Test workflow cancellation."""
    await workflow_engine.register("test_workflow", simple_workflow)

    # Start workflow execution
    task = asyncio.create_task(workflow_engine.execute("test_workflow", {}))

    # Cancel workflow
    await workflow_engine.cancel("test_workflow")

    # Verify workflow was cancelled
    with pytest.raises(WorkflowError):
        await task

    # Test cancelling non-existent workflow
    with pytest.raises(WorkflowError):
        await workflow_engine.cancel("non_existent")


@pytest.mark.asyncio
async def test_workflow_context():
    """Test workflow context functionality."""
    context = WorkflowContext()

    # Test initial state
    assert context.state == WorkflowState.CREATED
    assert context.error is None
    assert context.current_step is None
    assert len(context.history) == 0

    # Test state updates
    context.state = WorkflowState.RUNNING
    assert context.state == WorkflowState.RUNNING

    # Test error handling
    error = Exception("Test error")
    context.set_error(error)
    assert context.error == error
    assert context.state == WorkflowState.FAILED

    # Test history tracking
    entry = {"step": "test_step", "status": "completed"}
    context.add_history_entry(entry)
    assert len(context.history) == 1
    assert context.history[0] == entry

    # Test current step tracking
    context.set_current_step("test_step")
    assert context.current_step == "test_step"
