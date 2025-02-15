"""Test configuration for workflow tests."""

from typing import Any, Dict

import pytest

from pepperpy.core.workflows import WorkflowStep


@pytest.fixture
def test_inputs() -> Dict[str, Any]:
    """Create test workflow inputs."""
    return {
        "input1": "value1",
        "input2": "value2",
        "input3": 123,
        "input4": True,
    }


@pytest.fixture
def complex_workflow() -> list[WorkflowStep]:
    """Create a complex workflow for testing.

    This workflow includes:
    - Multiple steps with dependencies
    - Conditional execution
    - Retry configuration
    - Timeouts
    """
    return [
        WorkflowStep(
            name="start",
            action="initialize",
            inputs={},
            outputs=["initialized"],
        ),
        WorkflowStep(
            name="process",
            action="process_data",
            inputs={"data": "input1"},
            outputs=["processed"],
            condition="context.variables.get('initialized') == 'Executed initialize'",
            retry_config={"max_retries": 3, "delay": 0.1},
        ),
        WorkflowStep(
            name="validate",
            action="validate_data",
            inputs={"data": "processed"},
            outputs=["validated"],
            timeout=1.0,
        ),
        WorkflowStep(
            name="finish",
            action="finalize",
            inputs={"data": "validated"},
            outputs=["result"],
            condition="context.variables.get('validated') is not None",
        ),
    ]
