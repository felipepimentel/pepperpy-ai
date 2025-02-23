"""System tests for lifecycle management.

This module contains system tests that verify the complete
lifecycle of the system, including initialization, execution,
and cleanup of multiple components.
"""

import asyncio
from typing import AsyncGenerator, List

import pytest

from pepperpy.tests.base import TestContext
from pepperpy.tests.conftest import TestComponent


class SystemComponent(TestComponent):
    """System component implementation."""

    def __init__(self, name: str) -> None:
        """Initialize component.

        Args:
            name: Component name
        """
        super().__init__()
        self.name = name
        self._dependencies: List[SystemComponent] = []

    async def _initialize(self) -> None:
        """Initialize component."""
        await super()._initialize()
        self._operations.inc()
        self._state["initialized"] = True
        self._duration.observe(0.1)

    async def _cleanup(self) -> None:
        """Clean up component."""
        self._operations.inc()
        self._state["cleaned"] = True
        self._duration.observe(0.1)
        await super()._cleanup()

    async def _execute(self) -> None:
        """Execute component operation."""
        self._operations.inc()
        try:
            # Initialize dependencies first
            for dep in self._dependencies:
                if not dep._state.get("initialized", False):
                    await dep._initialize()

            # Simulate work
            await asyncio.sleep(0.1)
            self._state["executed"] = True
            self._duration.observe(0.1)

        except Exception:
            self._errors.inc()
            raise

    def add_dependency(self, component: "SystemComponent") -> None:
        """Add dependency.

        Args:
            component: Dependency component
        """
        self._dependencies.append(component)


class SystemManager:
    """System manager implementation."""

    def __init__(self) -> None:
        """Initialize manager."""
        self._components: List[SystemComponent] = []

    def add_component(self, component: SystemComponent) -> None:
        """Add component.

        Args:
            component: Component to add
        """
        self._components.append(component)

    async def initialize(self) -> None:
        """Initialize system."""
        for component in self._components:
            await component._initialize()

    async def cleanup(self) -> None:
        """Clean up system."""
        # Clean up in reverse order
        for component in reversed(self._components):
            await component._cleanup()

    async def execute(self) -> None:
        """Execute system."""
        for component in self._components:
            await component._execute()


@pytest.fixture
async def system_manager() -> AsyncGenerator[SystemManager, None]:
    """Fixture that provides a system manager.

    Yields:
        SystemManager: System manager
    """
    manager = SystemManager()
    yield manager


@pytest.fixture
async def system_components() -> AsyncGenerator[List[SystemComponent], None]:
    """Fixture that provides system components.

    Yields:
        List[SystemComponent]: System components
    """
    # Create components
    component_a = SystemComponent("A")
    component_b = SystemComponent("B")
    component_c = SystemComponent("C")

    # Set up dependencies
    component_c.add_dependency(component_a)
    component_c.add_dependency(component_b)
    component_b.add_dependency(component_a)

    components = [component_a, component_b, component_c]
    yield components

    # Clean up components in reverse order
    for component in reversed(components):
        await component._cleanup()


@pytest.mark.asyncio
async def test_system_lifecycle(
    system_manager: SystemManager,
    system_components: List[SystemComponent],
    test_context: TestContext,
) -> None:
    """Test system lifecycle.

    This test verifies that the system can be initialized,
    executed, and cleaned up correctly.

    Args:
        system_manager: System manager fixture
        system_components: System components fixture
        test_context: Test context fixture
    """
    # Add components to manager
    for component in system_components:
        system_manager.add_component(component)

    # Initialize system
    await system_manager.initialize()

    # Verify initialization
    for component in system_components:
        assert component._state["initialized"]
        assert component._operations.get_value() == 1
        assert component._errors.get_value() == 0
        assert component._duration.get_value()["count"] == 1

    # Execute system
    await system_manager.execute()

    # Verify execution
    for component in system_components:
        assert component._state["executed"]
        assert component._operations.get_value() == 2
        assert component._errors.get_value() == 0
        assert component._duration.get_value()["count"] == 2

    # Clean up system
    await system_manager.cleanup()

    # Verify cleanup
    for component in reversed(system_components):
        assert component._state["cleaned"]
        assert component._operations.get_value() == 3
        assert component._errors.get_value() == 0
        assert component._duration.get_value()["count"] == 3


@pytest.mark.asyncio
async def test_system_error_handling(
    system_manager: SystemManager,
    system_components: List[SystemComponent],
    test_context: TestContext,
) -> None:
    """Test system error handling.

    This test verifies that the system handles errors correctly
    during initialization, execution, and cleanup.

    Args:
        system_manager: System manager fixture
        system_components: System components fixture
        test_context: Test context fixture
    """
    # Add components to manager
    for component in system_components:
        system_manager.add_component(component)

    # Override component B's execute method to raise an error
    component_b = system_components[1]

    async def execute_with_error() -> None:
        component_b._operations.inc()
        raise ValueError("Component B error")

    component_b._execute = execute_with_error  # type: ignore

    # Initialize system
    await system_manager.initialize()

    # Execute should raise error
    with pytest.raises(ValueError, match="Component B error"):
        await system_manager.execute()

    # Verify component states
    component_a = system_components[0]
    component_c = system_components[2]

    # Component A should have executed successfully
    assert component_a._state["executed"]
    assert component_a._operations.get_value() == 2
    assert component_a._errors.get_value() == 0

    # Component B should have failed
    assert "executed" not in component_b._state
    assert component_b._operations.get_value() == 2
    assert component_b._errors.get_value() == 1

    # Component C should not have executed
    assert "executed" not in component_c._state
    assert component_c._operations.get_value() == 1
    assert component_c._errors.get_value() == 0

    # Clean up system
    await system_manager.cleanup()

    # Verify cleanup
    for component in reversed(system_components):
        assert component._state["cleaned"]
