"""Base provider implementation for agents."""

import asyncio
import logging
from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import (
    Any,
    NotRequired,
    Protocol,
    TypedDict,
    TypeVar,
)
from uuid import UUID, uuid4

from pydantic import BaseModel

from pepperpy.core.common.base import BaseComponent
from pepperpy.core.errors import ConfigurationError, StateError
from pepperpy.core.common.logging import get_logger
from pepperpy.core.types import (
    AgentConfig,
    AgentError,
    AgentMessage,
    AgentProvider,
    AgentResponse,
    AgentState,
)

from .domain import (
    ProviderCapability,
    ProviderConfig,
    ProviderMetadata,
    ProviderState,
)
from .types import ProviderMessage, ProviderResponse

logger = logging.getLogger(__name__)

T = TypeVar("T", covariant=True)

# Type alias for provider callback
ProviderCallback = Callable[[dict[str, Any]], None]

# Valid provider types
VALID_PROVIDER_TYPES = frozenset({
    "services.openai",
    "services.openrouter",
    "services.anthropic",
    "services.gemini",
    "services.perplexity",
    "services.stackspot",
})

# Configure logger
logger = get_logger(__name__)


class LogContext(TypedDict, total=True):
    """Type definition for logging context information."""

    error: NotRequired[str | Exception]
    status: NotRequired[str]
    model: NotRequired[str]
    provider: NotRequired[str]
    duration: NotRequired[float]
    tokens: NotRequired[int]
    request_id: NotRequired[str]
    extra: NotRequired[dict[str, str | int | float | bool]]


class Message(BaseModel):
    """A message that can be exchanged with providers."""

    id: str
    content: str
    metadata: dict[str, Any] | None = None


class Response(BaseModel):
    """A response from a provider."""

    id: UUID
    content: str
    metadata: dict[str, Any] | None = None


class LoggerProtocol(Protocol):
    """Protocol for logger interface."""

    def error(self, message: str, **context: str) -> None:
        """Log an error message.

        Args:
        ----
            message: The error message to log.
            **context: Additional context information as string values.

        """
        ...

    def info(self, message: str, **context: str) -> None:
        """Log an info message.

        Args:
        ----
            message: The info message to log.
            **context: Additional context information as string values.

        """
        ...

    def debug(self, message: str, **context: str) -> None:
        """Log a debug message.

        Args:
        ----
            message: The debug message to log.
            **context: Additional context information as string values.

        """
        ...

    def warning(self, message: str, **context: str) -> None:
        """Log a warning message.

        Args:
        ----
            message: The warning message to log.
            **context: Additional context information as string values.

        """
        ...


# Type alias for provider configuration values
type ProviderConfigValue = str | int | float | bool | list[str] | dict[str, Any]


class ExtraConfig(TypedDict, total=False):
    """Additional provider configuration options."""

    model_params: NotRequired[dict[str, ProviderConfigValue]]
    api_params: NotRequired[dict[str, ProviderConfigValue]]
    custom_settings: NotRequired[dict[str, ProviderConfigValue]]


class GenerateKwargs(BaseModel):
    """Keyword arguments for generate method."""

    model: str | None = None
    temperature: float | None = None
    max_tokens: int | None = None
    stop: list[str] | None = None
    stop_sequences: list[str] | None = None
    presence_penalty: float | None = None
    frequency_penalty: float | None = None
    top_p: float | None = None
    top_k: int | None = None


class ProviderKwargs(TypedDict, total=False):
    """Type definition for provider-specific keyword arguments."""

    model: str
    temperature: float
    max_tokens: int
    stop: list[str] | None
    stop_sequences: list[str] | None


class EmbeddingKwargs(TypedDict, total=False):
    """Keyword arguments for embedding methods."""

    model: NotRequired[str]
    model_params: NotRequired[dict[str, Any]]
    batch_size: NotRequired[int]
    encoding_format: NotRequired[str]


class StreamKwargs(BaseModel):
    """Keyword arguments for stream method."""

    temperature: float | None = None
    max_tokens: int | None = None
    stop: list[str] | None = None
    chunk_size: int | None = None
    buffer_size: int | None = None


class BaseProvider(BaseComponent):
    """Base class for all Pepperpy providers.

    This class provides the foundation for building providers in the Pepperpy
    framework. It handles lifecycle management, state tracking, and basic
    provider functionality.

    Attributes:
        id: Unique identifier for the provider
        state: Current provider state
        metadata: Provider metadata
        config: Provider configuration
        capabilities: List of provider capabilities

    """

    def __init__(
        self,
        id: UUID,
        metadata: ProviderMetadata | None = None,
        config: ProviderConfig | None = None,
    ) -> None:
        """Initialize the base provider.

        Args:
            id: Unique identifier for the provider
            metadata: Optional provider metadata
            config: Optional provider configuration

        Raises:
            ConfigurationError: If configuration is invalid

        """
        super().__init__(id, metadata)
        self.config = config or ProviderConfig(
            provider_type="base",
            name="base",
            version="1.0.0",
        )
        self.state = ProviderState.CREATED
        self._logger = logger.getChild(self.__class__.__name__)

    @property
    def capabilities(self) -> list[ProviderCapability]:
        """Get provider capabilities.

        Returns:
            List of capability identifiers

        """
        return []

    async def initialize(self) -> None:
        """Initialize the provider.

        This method is called during provider startup to perform any necessary
        initialization.

        Raises:
            StateError: If provider is in invalid state
            ConfigurationError: If initialization fails

        """
        if self.state != ProviderState.CREATED:
            raise StateError(f"Cannot initialize provider in state: {self.state}")

        try:
            self.state = ProviderState.INITIALIZING
            # Perform initialization
            self.state = ProviderState.READY
        except Exception as e:
            self.state = ProviderState.ERROR
            raise ConfigurationError(f"Provider initialization failed: {e}") from e

    async def cleanup(self) -> None:
        """Clean up provider resources.

        This method is called during provider shutdown to perform cleanup.
        """
        if self.state not in {ProviderState.READY, ProviderState.ERROR}:
            raise StateError(f"Cannot cleanup provider in state: {self.state}")

        try:
            self.state = ProviderState.CLEANING
            # Perform cleanup
            self.state = ProviderState.TERMINATED
        except Exception as e:
            self.state = ProviderState.ERROR
            raise StateError(f"Provider cleanup failed: {e}") from e

    @abstractmethod
    async def process_message(self, message: ProviderMessage) -> ProviderResponse[Any]:
        """Process an incoming message.

        This is the main entry point for provider message processing. All providers
        must implement this method to handle incoming messages.

        Args:
            message: The message to process

        Returns:
            Response containing processing results

        Raises:
            NotImplementedError: If not implemented by subclass

        """
        raise NotImplementedError

    async def execute(self, **kwargs: Any) -> Any:
        """Execute the provider's main functionality.

        This method implements the BaseComponent interface. It processes
        a message if one is provided in kwargs.

        Args:
            **kwargs: Execution parameters

        Returns:
            Execution results

        Raises:
            StateError: If provider is in invalid state

        """
        if self.state != ProviderState.READY:
            raise StateError(f"Cannot execute provider in state: {self.state}")

        message = kwargs.get("message")
        if not message:
            raise ConfigurationError("Message is required for execution")

        try:
            self.state = ProviderState.PROCESSING
            response = await self.process_message(message)
            self.state = ProviderState.READY
            return response
        except Exception as e:
            self.state = ProviderState.ERROR
            raise StateError(f"Provider execution failed: {e}") from e

    def validate(self) -> None:
        """Validate provider state and configuration.

        Raises:
            StateError: If provider state is invalid
            ConfigurationError: If configuration is invalid

        """
        super().validate()
        if not isinstance(self.state, ProviderState):
            raise StateError(f"Invalid provider state: {self.state}")
        if not isinstance(self.config, ProviderConfig):
            raise ConfigurationError(
                "Provider config must be a ProviderConfig instance"
            )


class Provider(ABC):
    """Base class for AI providers."""

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        """Initialize the provider.

        Args:
        ----
            config: Optional configuration for the provider.

        """
        self.config = config or {}

    @abstractmethod
    async def generate(
        self, prompt: str, parameters: dict[str, Any] | None = None
    ) -> str:
        """Generate a response for the given prompt.

        Args:
        ----
            prompt: The prompt to generate a response for.
            parameters: Optional parameters for the generation.

        Returns:
        -------
            The generated response.

        """
        pass


class BaseAgentProvider(AgentProvider):
    """Base implementation of agent provider."""

    def __init__(self, **config: Any) -> None:
        """Initialize provider with configuration.

        Args:
            **config: Configuration parameters

        Raises:
            ConfigurationError: If configuration is invalid
        """
        super().__init__()
        self.config = config
        self._agents: dict[str, AgentConfig] = {}
        self._states: dict[str, AgentState] = {}
        self._locks: dict[str, asyncio.Lock] = {}

    async def create(
        self,
        config: AgentConfig,
        **kwargs: Any,
    ) -> str:
        """Create a new agent.

        Args:
            config: Agent configuration
            **kwargs: Additional provider-specific parameters

        Returns:
            Agent ID

        Raises:
            AgentError: If creation fails
            ConfigurationError: If configuration is invalid
        """
        try:
            # Generate ID if not provided
            agent_id = str(config.id or uuid4())

            # Validate configuration
            if agent_id in self._agents:
                raise ConfigurationError(f"Agent {agent_id} already exists")

            # Initialize state
            self._agents[agent_id] = config
            self._states[agent_id] = AgentState.CREATED
            self._locks[agent_id] = asyncio.Lock()

            # Initialize agent
            try:
                self._states[agent_id] = AgentState.INITIALIZING
                await self._initialize_agent(agent_id, config, **kwargs)
                self._states[agent_id] = AgentState.READY
            except Exception as e:
                self._states[agent_id] = AgentState.ERROR
                raise AgentError(
                    f"Failed to initialize agent: {e}",
                    agent_id=agent_id,
                    provider=self.__class__.__name__,
                )

            return agent_id

        except Exception as e:
            raise AgentError(
                f"Failed to create agent: {e}",
                provider=self.__class__.__name__,
            )

    async def execute(
        self,
        agent_id: str,
        messages: list[AgentMessage],
        **kwargs: Any,
    ) -> AgentResponse:
        """Execute agent with messages.

        Args:
            agent_id: Agent ID to execute
            messages: Messages to process
            **kwargs: Additional provider-specific parameters

        Returns:
            Agent response

        Raises:
            AgentError: If execution fails
            StateError: If agent is not in valid state
        """
        if agent_id not in self._agents:
            raise AgentError(
                f"Agent {agent_id} not found",
                agent_id=agent_id,
                provider=self.__class__.__name__,
            )

        async with self._locks[agent_id]:
            try:
                # Check state
                if self._states[agent_id] != AgentState.READY:
                    raise StateError(
                        f"Agent {agent_id} not ready (state: {self._states[agent_id]})"
                    )

                # Execute
                self._states[agent_id] = AgentState.EXECUTING
                response = await self._execute_agent(
                    agent_id, self._agents[agent_id], messages, **kwargs
                )
                self._states[agent_id] = AgentState.READY
                return response

            except Exception as e:
                self._states[agent_id] = AgentState.ERROR
                raise AgentError(
                    f"Failed to execute agent: {e}",
                    agent_id=agent_id,
                    provider=self.__class__.__name__,
                )

    async def update(
        self,
        agent_id: str,
        config: AgentConfig,
        **kwargs: Any,
    ) -> None:
        """Update agent configuration.

        Args:
            agent_id: Agent ID to update
            config: New configuration
            **kwargs: Additional provider-specific parameters

        Raises:
            AgentError: If update fails
            StateError: If agent is not in valid state
        """
        if agent_id not in self._agents:
            raise AgentError(
                f"Agent {agent_id} not found",
                agent_id=agent_id,
                provider=self.__class__.__name__,
            )

        async with self._locks[agent_id]:
            try:
                # Check state
                if self._states[agent_id] not in {AgentState.READY, AgentState.ERROR}:
                    raise StateError(
                        f"Agent {agent_id} not ready (state: {self._states[agent_id]})"
                    )

                # Update configuration
                old_config = self._agents[agent_id]
                self._agents[agent_id] = config

                # Re-initialize if needed
                if self._needs_reinitialization(old_config, config):
                    self._states[agent_id] = AgentState.INITIALIZING
                    await self._initialize_agent(agent_id, config, **kwargs)
                    self._states[agent_id] = AgentState.READY

            except Exception as e:
                self._states[agent_id] = AgentState.ERROR
                raise AgentError(
                    f"Failed to update agent: {e}",
                    agent_id=agent_id,
                    provider=self.__class__.__name__,
                )

    async def delete(
        self,
        agent_id: str,
        **kwargs: Any,
    ) -> None:
        """Delete an agent.

        Args:
            agent_id: Agent ID to delete
            **kwargs: Additional provider-specific parameters

        Raises:
            AgentError: If deletion fails
        """
        if agent_id not in self._agents:
            return

        async with self._locks[agent_id]:
            try:
                # Clean up
                self._states[agent_id] = AgentState.CLEANING
                await self._cleanup_agent(agent_id, self._agents[agent_id], **kwargs)
                self._states[agent_id] = AgentState.TERMINATED

                # Remove from tracking
                del self._agents[agent_id]
                del self._states[agent_id]
                del self._locks[agent_id]

            except Exception as e:
                self._states[agent_id] = AgentState.ERROR
                raise AgentError(
                    f"Failed to delete agent: {e}",
                    agent_id=agent_id,
                    provider=self.__class__.__name__,
                )

    async def _initialize_agent(
        self,
        agent_id: str,
        config: AgentConfig,
        **kwargs: Any,
    ) -> None:
        """Initialize agent resources.

        Args:
            agent_id: Agent ID to initialize
            config: Agent configuration
            **kwargs: Additional provider-specific parameters

        Raises:
            AgentError: If initialization fails
        """
        pass

    async def _execute_agent(
        self,
        agent_id: str,
        config: AgentConfig,
        messages: list[AgentMessage],
        **kwargs: Any,
    ) -> AgentResponse:
        """Execute agent implementation.

        Args:
            agent_id: Agent ID to execute
            config: Agent configuration
            messages: Messages to process
            **kwargs: Additional provider-specific parameters

        Returns:
            Agent response

        Raises:
            AgentError: If execution fails
        """
        raise NotImplementedError

    async def _cleanup_agent(
        self,
        agent_id: str,
        config: AgentConfig,
        **kwargs: Any,
    ) -> None:
        """Clean up agent resources.

        Args:
            agent_id: Agent ID to clean up
            config: Agent configuration
            **kwargs: Additional provider-specific parameters

        Raises:
            AgentError: If cleanup fails
        """
        pass

    def _needs_reinitialization(
        self,
        old_config: AgentConfig,
        new_config: AgentConfig,
    ) -> bool:
        """Check if agent needs reinitialization after config update.

        Args:
            old_config: Previous configuration
            new_config: New configuration

        Returns:
            True if reinitialization needed
        """
        # Reinitialize if core settings change
        return (
            old_config.provider != new_config.provider
            or old_config.model != new_config.model
            or old_config.memory != new_config.memory
        )
