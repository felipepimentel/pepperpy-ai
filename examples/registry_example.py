"""Example of using the unified registry system.

This example demonstrates how to use the unified registry system to register
and discover components across different modules.
"""

import logging

from pepperpy.agents.registry import get_agent_registry
from pepperpy.core.registry import (
    ComponentMetadata,
    Registry,
    RegistryComponent,
    auto_register,
    get_registry,
)
from pepperpy.core.registry.auto import (
    initialize_registry_system,
    register_component,
)
from pepperpy.rag.registry import get_component_registry
from pepperpy.workflows.core.registry import get_workflow_registry

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ExampleComponent(RegistryComponent):
    """Example component for demonstration."""

    def __init__(self, name: str, description: str = ""):
        self._name = name
        self._description = description

    @property
    def name(self) -> str:
        """Get component name."""
        return self._name

    @property
    def metadata(self) -> ComponentMetadata:
        """Get component metadata."""
        return ComponentMetadata(
            name=self.name,
            description=self._description,
            tags={"example"},
            properties={"type": "example"},
        )


@register_component("examples", "CustomComponent")
class CustomComponent(ExampleComponent):
    """Custom component with auto-registration."""

    def __init__(
        self, name: str = "custom", description: str = "Auto-registered component"
    ):
        super().__init__(name, description)


def main():
    """Run the registry example."""
    # Initialize registry system
    logger.info("Initializing registry system...")
    registries = initialize_registry_system()
    logger.info(f"Registered registries: {list(registries.keys())}")

    # Create example registry
    logger.info("Creating example registry...")
    example_registry = Registry(ExampleComponent)
    registry_manager = get_registry()
    registry_manager.register_registry("examples", example_registry)

    # Register components
    logger.info("Registering components...")
    component1 = ExampleComponent("example1", "First example component")
    component2 = ExampleComponent("example2", "Second example component")
    example_registry.register(component1)
    example_registry.register(component2)

    # Register component types
    logger.info("Registering component types...")
    example_registry.register_type(
        "ExampleType",
        ExampleComponent,
        ComponentMetadata(
            name="ExampleType",
            description="Example component type",
            tags={"type", "example"},
        ),
    )

    # Auto-register components
    logger.info("Auto-registering components...")
    registered = auto_register(example_registry, __import__(__name__))
    logger.info(f"Auto-registered components: {registered}")

    # List components
    logger.info("Listing components...")
    components = example_registry.list_components()
    logger.info(f"Registered components: {list(components.keys())}")

    # List component types
    logger.info("Listing component types...")
    types = example_registry.list_component_types()
    logger.info(f"Registered component types: {list(types.keys())}")

    # Get component metadata
    logger.info("Getting component metadata...")
    metadata = example_registry.get_metadata("example1")
    logger.info(f"Component metadata: {metadata}")

    # Create component from type
    logger.info("Creating component from type...")
    new_component = example_registry.create(
        "ExampleType", "example3", "Created from type"
    )
    example_registry.register(new_component)
    logger.info(f"Created component: {new_component.name}")

    # Get component
    logger.info("Getting component...")
    component = example_registry.get("example1")
    logger.info(f"Got component: {component.name}")

    # Access other registries
    logger.info("Accessing other registries...")
    agent_registry = get_agent_registry()
    rag_registry = get_component_registry()
    workflow_registry = get_workflow_registry()

    logger.info(f"Agent types: {list(agent_registry.list_component_types().keys())}")
    logger.info(f"RAG components: {rag_registry.list_components('chunker')}")

    logger.info("Registry example completed successfully!")


if __name__ == "__main__":
    main()
