"""Base capability interface.

This module defines the base interface for AI capabilities.
It includes:
- Base capability interface
- Capability configuration
- Common capability types
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel

from pepperpy.core.common.extensions import Extension


class CapabilityConfig(BaseModel):
    """Capability configuration.

    Attributes:
        name: Capability name
        description: Capability description
        parameters: Capability parameters
        metadata: Additional metadata
    """

    name: str
    description: str = ""
    parameters: Dict[str, Any] = {}
    metadata: Dict[str, Any] = {}


class BaseCapability(Extension[CapabilityConfig]):
    """Base class for AI capabilities.

    This class defines the interface that all capabilities must implement.
    """

    def __init__(
        self,
        name: str,
        version: str,
        config: Optional[CapabilityConfig] = None,
    ) -> None:
        """Initialize capability.

        Args:
            name: Capability name
            version: Capability version
            config: Optional capability configuration
        """
        super().__init__(name, version, config)

    async def get_capabilities(self) -> List[str]:
        """Get list of capabilities provided.

        Returns:
            List of capability identifiers
        """
        return [self.metadata.name]

    async def get_dependencies(self) -> List[str]:
        """Get list of required dependencies.

        Returns:
            List of dependency identifiers
        """
        return []

    async def _initialize(self) -> None:
        """Initialize capability resources."""
        pass

    async def _cleanup(self) -> None:
        """Clean up capability resources."""
        pass
