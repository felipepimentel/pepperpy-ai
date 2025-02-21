"""Base agent interface.

This module defines the base interface for agents.
It includes:
- Base agent interface
- Agent configuration
- Common agent types
"""

from typing import TYPE_CHECKING, Any, Dict, List, Optional, Protocol

from pydantic import BaseModel

from pepperpy.core.errors import PepperpyError

if TYPE_CHECKING:
    pass


class AgentError(PepperpyError):
    """Raised when an agent operation fails."""

    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        user_message: Optional[str] = None,
        recovery_hint: Optional[str] = None,
    ) -> None:
        """Initialize the error."""
        error_details = {"error_code": "ERR006", **(details or {})}
        super().__init__(
            message,
            details=error_details,
            user_message=user_message,
            recovery_hint=recovery_hint,
        )


class AgentConfig(BaseModel):
    """Agent configuration.

    Attributes:
        name: Agent name
        description: Agent description
        parameters: Agent parameters
        metadata: Additional metadata
    """

    name: str
    description: str = ""
    parameters: Dict[str, Any] = {}
    metadata: Dict[str, Any] = {}


class AgentMessage(BaseModel):
    """Message exchanged with an agent.

    Attributes:
        role: Message role (e.g. "user", "assistant")
        content: Message content
        metadata: Additional metadata
    """

    role: str
    content: str
    metadata: Dict[str, Any] = {}


class AgentResponse(BaseModel):
    """Response from an agent.

    Attributes:
        messages: List of messages in the response
        metadata: Additional metadata
    """

    messages: List[AgentMessage]
    metadata: Dict[str, Any] = {}


class AgentProvider(Protocol):
    """Protocol for agent providers."""

    async def create(self, config: AgentConfig, **kwargs: Any) -> str:
        """Create a new agent.

        Args:
            config: Agent configuration
            **kwargs: Additional provider-specific parameters

        Returns:
            Agent ID

        Raises:
            AgentError: If creation fails
        """
        ...

    async def execute(
        self,
        agent_id: str,
        messages: List[AgentMessage],
        **kwargs: Any,
    ) -> AgentResponse:
        """Execute an agent.

        Args:
            agent_id: Agent ID to execute
            messages: Messages to process
            **kwargs: Additional provider-specific parameters

        Returns:
            Agent response

        Raises:
            AgentError: If execution fails
        """
        ...

    async def cleanup(self) -> None:
        """Clean up provider resources."""
        ...


class AgentExtension:
    """Concrete extension class for agents."""

    def __init__(
        self,
        name: str,
        version: str,
        config: Optional[AgentConfig] = None,
    ) -> None:
        """Initialize agent extension."""
        from pepperpy.core.extensions import Extension

        class ConcreteExtension(Extension[AgentConfig]):
            async def _initialize(self) -> None:
                pass

            async def _cleanup(self) -> None:
                pass

        self._extension = ConcreteExtension(name, version, config)


class BaseAgent:
    """Base class for agents.

    This class defines the interface that all agents must implement.
    """

    def __init__(
        self,
        name: str,
        version: str,
        config: Optional[AgentConfig] = None,
    ) -> None:
        """Initialize agent.

        Args:
            name: Agent name
            version: Agent version
            config: Optional agent configuration
        """
        self._extension = AgentExtension(name, version, config)._extension
        self._name = name
        self._version = version
        self._config = config

    @property
    def metadata(self):
        """Get agent metadata."""
        return self._extension.metadata

    async def initialize(self) -> None:
        """Initialize agent."""
        await self._extension.initialize()
        await self._initialize()

    async def cleanup(self) -> None:
        """Clean up agent resources."""
        await self._cleanup()
        await self._extension.cleanup()

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
        """Initialize agent resources."""
        pass

    async def _cleanup(self) -> None:
        """Clean up agent resources."""
        pass
