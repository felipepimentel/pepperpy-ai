"""Unit tests for test component.

This module contains unit tests for the test component.
"""

import pytest
from typing import Any, Dict, cast

from pepperpy.core.base import ComponentBase
from pepperpy.tests.base import TestContext
from pepperpy.tests.conftest import TestComponent


@pytest.mark.asyncio
async def test_component_lifecycle(
    test_component: ComponentBase,
    test_context: TestContext,
) -> None:
    """Test component lifecycle.

    This test verifies that the component can be initialized,
    executed, and cleaned up correctly.

    Args:
        test_component: Test component fixture
        test_context: Test context fixture
    """
    # Cast to TestComponent to access specific attributes
    component = cast(TestComponent, test_component)

    # Component should be initialized
    assert component._initialized

    # Execute component
    await component._execute()

    # Verify metrics
    assert component._operations.get_value() == 1
    assert component._errors.get_value() == 0
    assert component._duration.get_value()["count"] == 1


@pytest.mark.asyncio
async def test_component_state(
    test_component: ComponentBase,
    test_context: TestContext,
) -> None:
    """Test component state management.

    This test verifies that the component can manage its state
    correctly.

    Args:
        test_component: Test component fixture
        test_context: Test context fixture
    """
    # Cast to TestComponent to access specific attributes
    component = cast(TestComponent, test_component)

    # Initial state should be empty
    assert component.get_state() == {}

    # Set state
    test_state: Dict[str, Any] = {"key": "value", "number": 42}
    component.set_state(test_state)

    # Verify state
    assert component.get_state() == test_state

    # Update state
    component.set_state({"key": "new_value"})
    assert component.get_state()["key"] == "new_value"
    assert component.get_state()["number"] == 42


@pytest.mark.asyncio
async def test_component_error_handling(
    test_component: ComponentBase,
    test_context: TestContext,
) -> None:
    """Test component error handling.

    This test verifies that the component handles errors correctly
    and updates error metrics.

    Args:
        test_component: Test component fixture
        test_context: Test context fixture
    """
    # Cast to TestComponent to access specific attributes
    component = cast(TestComponent, test_component)

    # Override execute method to raise an error
    async def _execute_with_error() -> None:
        component._operations.inc()
        raise ValueError("Test error")

    component._execute = _execute_with_error  # type: ignore

    # Execute should raise error
    with pytest.raises(ValueError, match="Test error"):
        await component._execute()

    # Verify metrics
    assert component._operations.get_value() == 1
    assert component._errors.get_value() == 1
