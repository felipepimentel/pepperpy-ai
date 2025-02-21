"""Base adapter interface for external frameworks.

This module defines the base interface for adapting Pepperpy components to external frameworks.
It provides a consistent way to convert Pepperpy agents, workflows, and tools to their
equivalent representations in other frameworks like LangChain, AutoGen, etc.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, TypeVar

from pydantic import BaseModel

from pepperpy.agents.base import BaseAgent
from pepperpy.core.extensions import Extension
from pepperpy.workflows.base import BaseWorkflow


class AdapterConfig(BaseModel):
    """Configuration for framework adapters.

    Attributes:
        name: Adapter name
        framework_version: Target framework version
        parameters: Additional adapter parameters
        metadata: Additional metadata
    """

    name: str
    framework_version: str
    parameters: Dict[str, Any] = {}
    metadata: Dict[str, Any] = {}


T = TypeVar("T", bound=AdapterConfig)


class BaseAdapter(Extension[T], ABC):
    """Base class for framework adapters.

    This class defines the interface that all framework adapters must implement.
    It provides methods for adapting Pepperpy components to external framework equivalents.
    """

    def __init__(
        self,
        name: str,
        version: str,
        config: Optional[T] = None,
    ) -> None:
        """Initialize adapter.

        Args:
            name: Adapter name
            version: Adapter version
            config: Optional adapter configuration
        """
        super().__init__(name, version, config)

    @abstractmethod
    async def adapt_agent(self, agent: BaseAgent) -> Any:
        """Adapt a Pepperpy agent to the target framework.

        Args:
            agent: Pepperpy agent to adapt

        Returns:
            Framework-specific agent representation
        """
        pass

    @abstractmethod
    async def adapt_workflow(self, workflow: BaseWorkflow) -> Any:
        """Adapt a Pepperpy workflow to the target framework.

        Args:
            workflow: Pepperpy workflow to adapt

        Returns:
            Framework-specific workflow representation
        """
        pass

    @abstractmethod
    async def adapt_tool(self, tool: Any) -> Any:
        """Adapt a Pepperpy tool to the target framework.

        Args:
            tool: Pepperpy tool to adapt

        Returns:
            Framework-specific tool representation
        """
        pass

    @abstractmethod
    async def adapt_from_agent(self, external_agent: Any) -> BaseAgent:
        """Adapt an external framework agent to a Pepperpy agent.

        Args:
            external_agent: External framework agent to adapt

        Returns:
            Pepperpy agent representation
        """
        pass

    @abstractmethod
    async def adapt_from_workflow(self, external_workflow: Any) -> BaseWorkflow:
        """Adapt an external framework workflow to a Pepperpy workflow.

        Args:
            external_workflow: External framework workflow to adapt

        Returns:
            Pepperpy workflow representation
        """
        pass

    @abstractmethod
    async def adapt_from_tool(self, external_tool: Any) -> Any:
        """Adapt an external framework tool to a Pepperpy tool.

        Args:
            external_tool: External framework tool to adapt

        Returns:
            Pepperpy tool representation
        """
        pass
