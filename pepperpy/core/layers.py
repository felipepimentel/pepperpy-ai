"""Layered architecture implementation for the Pepperpy framework.

This module defines the core architectural layers and their extension points:
- Core Layer: Base functionality and utilities
- Provider Layer: External service integrations
- Capability Layer: AI capabilities and features
- Agent Layer: Agent implementations and behaviors
- Workflow Layer: Process and task orchestration
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Type, TypeVar, Union

from pydantic import BaseModel

from pepperpy.agents.base import BaseAgent
from pepperpy.capabilities.base import BaseCapability
from pepperpy.core.extensions import Extension, ExtensionPoint
from pepperpy.core.logging import get_logger
from pepperpy.providers.base import BaseProvider
from pepperpy.workflows.base import BaseWorkflow

# Configure logging
logger = get_logger(__name__)

# Type variables
T = TypeVar("T", bound=BaseModel)
ExtensionType = Union[
    Type[Extension[T]],
    Type[BaseProvider],
    Type[BaseCapability],
    Type[BaseAgent],
    Type[BaseWorkflow],
]


class LayerExtension(Extension[T]):
    """Base class for layer-specific extensions."""

    @abstractmethod
    async def get_capabilities(self) -> List[str]:
        """Get list of capabilities provided by this extension."""
        pass

    @abstractmethod
    async def get_dependencies(self) -> List[str]:
        """Get list of required dependencies."""
        pass


class Layer(ABC):
    """Base class for architectural layers."""

    def __init__(self, name: str) -> None:
        """Initialize layer.

        Args:
            name: Layer name
        """
        self.name = name
        self._extension_points: Dict[str, ExtensionPoint] = {}
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize layer and its extension points."""
        if self._initialized:
            return

        try:
            # Initialize extension points
            extension_points = await self._get_extension_points()
            for point_name, point_type in extension_points.items():
                self._extension_points[point_name] = ExtensionPoint(
                    f"{self.name}.{point_name}", point_type
                )

            self._initialized = True
            logger.info(f"Layer {self.name} initialized")

        except Exception as e:
            logger.error(f"Failed to initialize layer {self.name}: {e}")
            raise

    async def cleanup(self) -> None:
        """Clean up layer resources."""
        try:
            # Clean up extension points
            for point in self._extension_points.values():
                await point.cleanup()

            self._initialized = False
            logger.info(f"Layer {self.name} cleaned up")

        except Exception as e:
            logger.error(f"Failed to clean up layer {self.name}: {e}")
            raise

    def get_extension_point(self, name: str) -> Optional[ExtensionPoint]:
        """Get extension point by name.

        Args:
            name: Extension point name

        Returns:
            Extension point if found, None otherwise
        """
        return self._extension_points.get(name)

    @abstractmethod
    async def _get_extension_points(self) -> Dict[str, ExtensionType]:
        """Get layer's extension points.

        Returns:
            Dictionary mapping extension point names to their types
        """
        pass


class CoreLayer(Layer):
    """Core layer implementation."""

    def __init__(self) -> None:
        """Initialize core layer."""
        super().__init__("core")

    async def _get_extension_points(self) -> Dict[str, ExtensionType]:
        """Get core layer extension points."""
        from pepperpy.core.extensions import Extension

        return {
            "logging": Extension,  # Logging extensions
            "metrics": Extension,  # Metrics extensions
            "security": Extension,  # Security extensions
            "config": Extension,  # Configuration extensions
        }


class ProviderLayer(Layer):
    """Provider layer implementation."""

    def __init__(self) -> None:
        """Initialize provider layer."""
        super().__init__("provider")

    async def _get_extension_points(self) -> Dict[str, ExtensionType]:
        """Get provider layer extension points."""
        return {
            "llm": BaseProvider,  # LLM providers
            "storage": BaseProvider,  # Storage providers
            "memory": BaseProvider,  # Memory providers
            "content": BaseProvider,  # Content providers
        }


class CapabilityLayer(Layer):
    """Capability layer implementation."""

    def __init__(self) -> None:
        """Initialize capability layer."""
        super().__init__("capability")

    async def _get_extension_points(self) -> Dict[str, ExtensionType]:
        """Get capability layer extension points."""
        return {
            "reasoning": BaseCapability,  # Reasoning capabilities
            "learning": BaseCapability,  # Learning capabilities
            "planning": BaseCapability,  # Planning capabilities
            "synthesis": BaseCapability,  # Synthesis capabilities
        }


class AgentLayer(Layer):
    """Agent layer implementation."""

    def __init__(self) -> None:
        """Initialize agent layer."""
        super().__init__("agent")

    async def _get_extension_points(self) -> Dict[str, ExtensionType]:
        """Get agent layer extension points."""
        return {
            "behavior": BaseAgent,  # Agent behaviors
            "skills": BaseAgent,  # Agent skills
            "memory": BaseAgent,  # Agent memory
            "learning": BaseAgent,  # Agent learning
        }


class WorkflowLayer(Layer):
    """Workflow layer implementation."""

    def __init__(self) -> None:
        """Initialize workflow layer."""
        super().__init__("workflow")

    async def _get_extension_points(self) -> Dict[str, ExtensionType]:
        """Get workflow layer extension points."""
        return {
            "steps": BaseWorkflow,  # Workflow steps
            "triggers": BaseWorkflow,  # Workflow triggers
            "actions": BaseWorkflow,  # Workflow actions
            "conditions": BaseWorkflow,  # Workflow conditions
        }


class LayerManager:
    """Manager for architectural layers."""

    def __init__(self) -> None:
        """Initialize layer manager."""
        self._layers: Dict[str, Layer] = {
            "core": CoreLayer(),
            "provider": ProviderLayer(),
            "capability": CapabilityLayer(),
            "agent": AgentLayer(),
            "workflow": WorkflowLayer(),
        }
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize all layers."""
        if self._initialized:
            return

        try:
            # Initialize layers in order
            for layer in self._layers.values():
                await layer.initialize()

            self._initialized = True
            logger.info("Layer manager initialized")

        except Exception as e:
            logger.error(f"Failed to initialize layer manager: {e}")
            raise

    async def cleanup(self) -> None:
        """Clean up all layers."""
        try:
            # Clean up layers in reverse order
            for layer in reversed(list(self._layers.values())):
                await layer.cleanup()

            self._initialized = False
            logger.info("Layer manager cleaned up")

        except Exception as e:
            logger.error(f"Failed to clean up layer manager: {e}")
            raise

    def get_layer(self, name: str) -> Optional[Layer]:
        """Get layer by name.

        Args:
            name: Layer name

        Returns:
            Layer if found, None otherwise
        """
        return self._layers.get(name)

    def get_extension_point(self, layer: str, point: str) -> Optional[ExtensionPoint]:
        """Get extension point from layer.

        Args:
            layer: Layer name
            point: Extension point name

        Returns:
            Extension point if found, None otherwise
        """
        layer_obj = self.get_layer(layer)
        if layer_obj:
            return layer_obj.get_extension_point(point)
        return None
