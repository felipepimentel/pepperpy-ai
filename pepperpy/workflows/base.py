"""Base workflow interface.

This module defines the base interface for workflows.
It includes:
- Base workflow interface
- Workflow configuration
- Common workflow types
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel

from pepperpy.core.extensions import Extension


class WorkflowConfig(BaseModel):
    """Workflow configuration.

    Attributes:
        name: Workflow name
        description: Workflow description
        parameters: Workflow parameters
        metadata: Additional metadata
    """

    name: str
    description: str = ""
    parameters: Dict[str, Any] = {}
    metadata: Dict[str, Any] = {}


class BaseWorkflow(Extension[WorkflowConfig]):
    """Base class for workflows.

    This class defines the interface that all workflows must implement.
    """

    def __init__(
        self,
        name: str,
        version: str,
        config: Optional[WorkflowConfig] = None,
    ) -> None:
        """Initialize workflow.

        Args:
            name: Workflow name
            version: Workflow version
            config: Optional workflow configuration
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
        """Initialize workflow resources."""
        pass

    async def _cleanup(self) -> None:
        """Clean up workflow resources."""
        pass
