"""Builder implementations for PepperPy workflows.

This module provides builder classes for constructing workflows and components
in a fluent and type-safe manner.
"""

from typing import Any, Dict, List, Optional, TypeVar

from pepperpy.core.base import Component, ComponentRegistry
from pepperpy.workflow.base import WorkflowBase, WorkflowStatus

T = TypeVar("T")


class ComponentBuilder:
    """Builder for workflow components.

    The component builder provides a fluent interface for constructing
    workflow components with proper configuration and validation.
    """

    def __init__(self, registry: ComponentRegistry) -> None:
        """Initialize component builder.

        Args:
            registry: Component registry for component creation
        """
        self._registry = registry
        self._components: List[Component] = []

    def add(
        self,
        name: str,
        config: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> "ComponentBuilder":
        """Add a component to the build sequence.

        Args:
            name: Component name
            config: Optional component configuration
            metadata: Optional component metadata

        Returns:
            Self for method chaining
        """
        component = self._registry.create(name, config, metadata)
        self._components.append(component)
        return self

    def build(self) -> List[Component]:
        """Build the component sequence.

        Returns:
            List of configured components
        """
        return self._components


class WorkflowBuilder:
    """Builder for workflows.

    The workflow builder provides a fluent interface for constructing
    complete workflows with components and configuration.
    """

    def __init__(self, registry: ComponentRegistry) -> None:
        """Initialize workflow builder.

        Args:
            registry: Component registry for component creation
        """
        self._registry = registry
        self._name: Optional[str] = None
        self._config: Dict[str, Any] = {}
        self._metadata: Dict[str, Any] = {}
        self._components: List[Component] = []

    def name(self, name: str) -> "WorkflowBuilder":
        """Set workflow name.

        Args:
            name: Workflow name

        Returns:
            Self for method chaining
        """
        self._name = name
        return self

    def config(self, config: Dict[str, Any]) -> "WorkflowBuilder":
        """Set workflow configuration.

        Args:
            config: Workflow configuration

        Returns:
            Self for method chaining
        """
        self._config = config
        return self

    def metadata(self, metadata: Dict[str, Any]) -> "WorkflowBuilder":
        """Set workflow metadata.

        Args:
            metadata: Workflow metadata

        Returns:
            Self for method chaining
        """
        self._metadata = metadata
        return self

    def add_component(
        self,
        name: str,
        config: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> "WorkflowBuilder":
        """Add a component to the workflow.

        Args:
            name: Component name
            config: Optional component configuration
            metadata: Optional component metadata

        Returns:
            Self for method chaining
        """
        component = self._registry.create(name, config, metadata)
        self._components.append(component)
        return self

    def build(self) -> WorkflowBase:
        """Build the workflow.

        Returns:
            Configured workflow instance

        Raises:
            ValueError: If workflow name not set
        """
        if not self._name:
            raise ValueError("Workflow name must be set")

        return WorkflowBase(
            id=f"workflow_{self._name}",
            name=self._name,
            components=self._components,
            config=self._config,
            status=WorkflowStatus.PENDING,
            metadata=self._metadata or None,
        )
