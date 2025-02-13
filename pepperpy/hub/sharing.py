"""Component sharing and publishing functionality.

This module provides functionality for sharing and publishing Pepperpy
components (agents, workflows, teams) to make them available for reuse.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml
from structlog import get_logger

from pepperpy.core.errors import ConfigurationError

logger = get_logger()


class ComponentRegistry:
    """Registry for managing shared components."""

    def __init__(self, hub_path: Optional[Path] = None):
        """Initialize the registry."""
        self.hub_path = hub_path or Path.home() / ".pepperpy" / "hub"
        self.registry_path = self.hub_path / "registry.json"
        self._registry: Dict[str, Dict[str, Any]] = {}
        self._load_registry()

    def _load_registry(self) -> None:
        """Load the component registry."""
        if self.registry_path.exists():
            with open(self.registry_path) as f:
                self._registry = json.load(f)
        else:
            self._registry = {
                "agents": {},
                "workflows": {},
                "teams": {},
            }
            self._save_registry()

    def _save_registry(self) -> None:
        """Save the component registry."""
        with open(self.registry_path, "w") as f:
            json.dump(self._registry, f, indent=2)

    def register_component(
        self,
        component_type: str,
        name: str,
        metadata: Dict[str, Any],
    ) -> None:
        """Register a component.

        Args:
            component_type: Type of component ("agent", "workflow", "team")
            name: Component name
            metadata: Component metadata

        Example:
            >>> registry = ComponentRegistry()
            >>> registry.register_component(
            ...     "agent",
            ...     "researcher",
            ...     {"version": "1.0.0", "author": "PepperPy"}
            ... )

        """
        if component_type not in self._registry:
            raise ValueError(f"Invalid component type: {component_type}")

        self._registry[component_type][name] = {
            "name": name,
            "type": component_type,
            "metadata": metadata,
            "path": f"{component_type}s/{name}.yaml",
        }
        self._save_registry()
        logger.info(
            "Component registered",
            type=component_type,
            name=name,
        )

    def get_component(
        self,
        component_type: str,
        name: str,
    ) -> Dict[str, Any]:
        """Get component information.

        Args:
            component_type: Type of component
            name: Component name

        Returns:
            Component information

        Raises:
            ValueError: If component not found

        """
        if (
            component_type not in self._registry
            or name not in self._registry[component_type]
        ):
            raise ValueError(f"{component_type.title()} '{name}' not found in registry")

        return self._registry[component_type][name]

    def list_components(
        self,
        component_type: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """List registered components.

        Args:
            component_type: Optional type to filter by

        Returns:
            List of component information

        """
        if component_type:
            if component_type not in self._registry:
                raise ValueError(f"Invalid component type: {component_type}")
            return list(self._registry[component_type].values())
        else:
            components = []
            for type_components in self._registry.values():
                components.extend(type_components.values())
            return components

    def publish_component(
        self,
        component_type: str,
        name: str,
        config_path: Path,
    ) -> None:
        """Publish a component to make it available for sharing.

        Args:
            component_type: Type of component
            name: Component name
            config_path: Path to component configuration

        Example:
            >>> registry = ComponentRegistry()
            >>> registry.publish_component(
            ...     "agent",
            ...     "researcher",
            ...     Path("agents/researcher.yaml")
            ... )

        """
        # Validate component type
        if component_type not in ["agent", "workflow", "team"]:
            raise ValueError(f"Invalid component type: {component_type}")

        # Check if config exists
        if not config_path.exists():
            raise ConfigurationError(f"Configuration not found: {config_path}")

        try:
            # Load and validate config
            with open(config_path) as f:
                config = yaml.safe_load(f)

            # Extract metadata
            metadata = {
                "version": config.get("version", "0.1.0"),
                "description": config.get("description", ""),
                "author": config.get("metadata", {}).get("author", ""),
                "tags": config.get("metadata", {}).get("tags", []),
            }

            # Register component
            self.register_component(component_type, name, metadata)

            logger.info(
                "Component published",
                type=component_type,
                name=name,
                config=config_path,
            )

        except Exception as e:
            logger.error(
                "Failed to publish component",
                type=component_type,
                name=name,
                error=str(e),
            )
            raise ConfigurationError(
                f"Failed to publish {component_type} '{name}': {str(e)}"
            )


__all__ = ["ComponentRegistry"]
