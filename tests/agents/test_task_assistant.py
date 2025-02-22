"""Tests for task assistant agent."""

from typing import Any, Dict

import pytest

from pepperpy.agents.task_assistant import TaskAssistant
from pepperpy.core.errors import ConfigError, ProcessingError
from pepperpy.core.resources import resource_session


@pytest.fixture
def agent_config() -> Dict[str, Any]:
    """Sample agent configuration."""
    return {
        "model": "test-model",
        "temperature": 0.5,
        "max_tokens": 1000,
        "memory": {
            "enabled": True,
            "type": "simple",
            "config": {
                "auto_cleanup": True,
                "cleanup_interval": 60,
            },
        },
        "workflow": [
            {
                "step": "plan",
                "description": "Plan task execution",
                "timeout": 10,
            },
            {
                "step": "execute",
                "description": "Execute planned steps",
                "timeout": 30,
            },
            {
                "step": "validate",
                "description": "Validate execution results",
                "timeout": 10,
            },
        ],
    }


@pytest.mark.asyncio
async def test_task_assistant_lifecycle():
    """Test task assistant lifecycle."""
    agent = TaskAssistant()

    # Test initialization
    await agent.initialize()
    assert agent._initialized
    assert agent._memory is not None
    assert agent._memory._initialized

    # Test cleanup
    await agent.cleanup()
    assert not agent._initialized
    assert not agent._memory._initialized


@pytest.mark.asyncio
async def test_task_assistant_memory():
    """Test task assistant memory operations."""
    async with resource_session(TaskAssistant()) as agent:
        # Store and retrieve values
        await agent.remember("test_key", "test_value")
        value = await agent.recall("test_key")
        assert value == "test_value"


@pytest.mark.asyncio
async def test_task_assistant_workflow():
    """Test task assistant workflow execution."""
    agent = TaskAssistant(**agent_config())
    await agent.initialize()

    try:
        # Process task
        result = await agent.process("Test task")

        # Verify workflow execution
        assert "Validated result" in result

        # Check intermediate results
        plan = await agent.recall("step_plan")
        assert "Plan for task" in plan

        execution = await agent.recall("step_execute")
        assert "Executed plan" in execution

        validation = await agent.recall("step_validate")
        assert "Validated result" in validation

    finally:
        await agent.cleanup()


@pytest.mark.asyncio
async def test_task_assistant_error_handling():
    """Test task assistant error handling."""
    # Test with invalid workflow step
    agent = TaskAssistant(workflow=[{"step": "invalid"}])
    await agent.initialize()

    try:
        with pytest.raises(ProcessingError) as exc:
            await agent.process("Test task")
        assert "Unknown workflow step" in str(exc.value)
    finally:
        await agent.cleanup()


@pytest.mark.asyncio
async def test_task_assistant_from_hub():
    """Test creating task assistant from Hub configuration."""
    # Test with non-existent configuration
    with pytest.raises(ConfigError):
        TaskAssistant.from_hub("nonexistent")

    # Test with valid configuration
    agent = TaskAssistant.from_hub(
        "task_assistant",
        config_version="v1.0.0",
    )
    assert agent.config["model"] == "gpt-4"
    assert agent.config["memory"]["enabled"] is True
