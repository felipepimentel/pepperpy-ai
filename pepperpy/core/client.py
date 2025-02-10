"""Pepperpy client for interacting with language models.

This module provides the main client interface for interacting with
language models through various providers and managing agent lifecycles.
"""

import logging
import time
from collections.abc import AsyncGenerator, Callable, Mapping
from types import TracebackType
from typing import (
    Any,
    Generic,
    TypeVar,
    cast,
)
from uuid import UUID, uuid4

from pydantic import BaseModel, Field
from pydantic.types import SecretStr

from pepperpy.core.base import AgentContext, AgentState, BaseAgent
from pepperpy.core.errors import ConfigurationError, StateError
from pepperpy.core.memory.store import MemoryStore, create_memory_store
from pepperpy.core.prompt.template import PromptTemplate, create_prompt_template
from pepperpy.core.types import Response
from pepperpy.providers.base import (
    BaseProvider,
    ExtraConfig,
    ProviderConfig,
    ProviderConfigValue,
)
from pepperpy.providers.domain import (
    ProviderError,
)
from pepperpy.providers.domain import (
    ProviderNotFoundError as NotFoundError,
)
from pepperpy.providers.manager import ProviderManager

# Configure logging
logger = logging.getLogger(__name__)

# Type variables for generic implementations
T_Input = TypeVar("T_Input")  # Input data type
T_Output = TypeVar("T_Output")  # Output data type
T_Config = TypeVar("T_Config", bound=Mapping[str, Any])  # Configuration type
T_Context = TypeVar("T_Context")  # Context type

# Error type aliases for better readability
ProviderErrorType = type[ProviderError]
ExceptionType = type[BaseException]

# Valid hook event types
VALID_HOOK_EVENTS = frozenset({
    "initialize",
    "cleanup",
    "agent_created",
    "agent_removed",
})

# Hook type alias for better readability
HookCallbackType = Callable[
    ["PepperpyClient[T_Input, T_Output, T_Config, T_Context]"], None
]


class ClientConfig(BaseModel):
    """Configuration for the Pepperpy client.

    Attributes:
        timeout: Operation timeout in seconds
        max_retries: Maximum number of retries
        retry_delay: Delay between retries in seconds
        provider_type: Type of provider to use
        provider_config: Provider-specific configuration
        memory_config: Memory store configuration
        prompt_config: Prompt template configuration
    """

    timeout: float = Field(default=30.0, gt=0)
    max_retries: int = Field(default=3, ge=0)
    retry_delay: float = Field(default=1.0, ge=0)
    provider_type: str = Field(default="openrouter")
    provider_config: dict[str, Any] = Field(default_factory=lambda: {})
    memory_config: dict[str, Any] = Field(default_factory=lambda: {})
    prompt_config: dict[str, Any] = Field(default_factory=lambda: {})


class PepperpyClient(Generic[T_Input, T_Output, T_Config, T_Context]):
    """Main client for interacting with the Pepperpy system.

    This class provides the primary interface for:
    - Managing agent lifecycles
    - Interacting with language models
    - Handling configuration and resources
    """

    def __init__(self) -> None:
        """Initialize the Pepperpy client."""
        self._agent_factory: (
            Callable[
                [str, AgentContext, T_Config],
                BaseAgent[T_Input, T_Output, T_Config, T_Context],
            ]
            | None
        ) = None
        self._provider: BaseProvider | None = None
        self._config: ClientConfig | None = None
        self._raw_config: dict[str, Any] = {}
        self._agents: dict[UUID, BaseAgent[T_Input, T_Output, T_Config, T_Context]] = {}
        self._manager: ProviderManager | None = None
        self._initialized = False
        self._created_at = time.time()
        self._updated_at = self._created_at
        self._lifecycle_hooks: dict[
            str,
            set[
                Callable[[PepperpyClient[T_Input, T_Output, T_Config, T_Context]], None]
            ],
        ] = {event: set() for event in VALID_HOOK_EVENTS}
        self._memory: MemoryStore | None = None
        self._prompt: PromptTemplate | None = None

    @property
    def is_initialized(self) -> bool:
        """Check if the client is initialized."""
        return self._initialized

    @property
    def config(self) -> ClientConfig:
        """Get current client configuration.

        Raises:
            StateError: If client is not initialized
        """
        if not self._config:
            raise StateError("Client not initialized")
        return self._config

    async def __aenter__(
        self,
    ) -> "PepperpyClient[T_Input, T_Output, T_Config, T_Context]":
        """Initialize the client for use in async context.

        Returns:
            Initialized client instance

        Raises:
            ConfigurationError: If initialization fails
        """
        await self.initialize()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """Clean up resources when exiting async context.

        Args:
            exc_type: The type of the exception that was raised
            exc_val: The instance of the exception that was raised
            exc_tb: The traceback of the exception that was raised
        """
        await self.cleanup()

    def add_lifecycle_hook(
        self,
        event: str,
        callback: Callable[
            ["PepperpyClient[T_Input, T_Output, T_Config, T_Context]"], None
        ],
    ) -> None:
        """Add event hook.

        Args:
            event: Event to hook. Valid events:
                - "initialize"
                - "cleanup"
                - "agent_created"
                - "agent_removed"
            callback: Function to call on event

        Raises:
            ValueError: If event is invalid
        """
        if event not in VALID_HOOK_EVENTS:
            raise ValueError(f"Invalid event: {event}")
        self._lifecycle_hooks[event].add(callback)

    def remove_lifecycle_hook(
        self,
        event: str,
        callback: Callable[
            ["PepperpyClient[T_Input, T_Output, T_Config, T_Context]"], None
        ],
    ) -> None:
        """Remove a lifecycle hook.

        Args:
            event: Event to unhook
            callback: Function to remove

        Raises:
            ValueError: If event is invalid
        """
        if event not in VALID_HOOK_EVENTS:
            raise ValueError(f"Invalid event: {event}")
        self._lifecycle_hooks[event].discard(callback)

    async def _trigger_hooks(
        self,
        event: str,
        error_context: dict[str, Any] | None = None,
    ) -> None:
        """Trigger lifecycle hooks for an event.

        Args:
            event: Event that triggered the hooks
            error_context: Optional context for error logging
        """
        for hook in self._lifecycle_hooks[event]:
            try:
                hook(self)
            except Exception as hook_error:
                # Get error type name safely
                error_type = hook_error.__class__.__name__
                error_msg = f"Lifecycle hook failed - Event: {event}, Error Type: {error_type}, Message: {hook_error!s}"
                if error_context:
                    error_msg += f", Context: {error_context}"
                logger.error(error_msg)

    async def initialize(self) -> None:
        """Initialize the client.

        This method must be called before using the client.
        It initializes the provider and sets up the manager.

        Raises:
            RuntimeError: If initialization fails
            ValueError: If provider is not set
        """
        try:
            # Create and initialize manager with provider
            if self._provider is None:
                raise ValueError("Provider not initialized")
            self._manager = ProviderManager(primary_provider=self._provider)
            await self._manager.initialize()

            # Initialize memory store if configured
            if self.config.memory_config:
                self._memory = await create_memory_store(self.config.memory_config)
                await self._memory.initialize()

            # Initialize prompt template if configured
            if self.config.prompt_config:
                self._prompt = await create_prompt_template(self.config.prompt_config)
                await self._prompt.initialize()

            self._initialized = True
            logger.info("Initialized client")

        except Exception as e:
            error_msg = f"Failed to initialize client: {e!s}"
            logger.error(error_msg)
            raise RuntimeError("Failed to initialize client") from e

    async def cleanup(self) -> None:
        """Clean up client resources.

        This method ensures proper cleanup of:
        1. Provider manager
        2. All active agents
        3. Any open connections

        Raises:
            RuntimeError: If cleanup fails
        """
        try:
            # Trigger hooks
            await self._trigger_hooks("cleanup")

            # Cleanup provider
            if self._manager:
                await self._manager.cleanup()
                self._manager = None

            # Cleanup agents
            for agent in list(self._agents.values()):
                try:
                    await agent.cleanup()
                except Exception as agent_error:
                    error_msg = f"Agent cleanup failed - Agent ID: {agent.id}, Error: {agent_error!s}"
                    logger.error(error_msg)

            self._agents.clear()
            self._initialized = False
            self._updated_at = time.time()

        except Exception as e:
            raise RuntimeError(f"Failed to cleanup client: {e!s}") from e

    def _ensure_initialized(self) -> None:
        """Ensure the client is initialized.

        Raises:
            StateError: If client is not initialized
        """
        if not self._initialized:
            raise StateError("Client not initialized")

    async def chat(self, message: str) -> str:
        """Send a chat message and get a response.

        This method provides direct access to the language model for
        simple chat interactions.

        Args:
            message: The message to send

        Returns:
            The text response from the provider

        Raises:
            StateError: If client is not initialized
            TypeError: If provider returns a streaming response
            ConfigurationError: If provider configuration is invalid
            TimeoutError: If operation times out
        """
        self._ensure_initialized()
        if not self._manager:
            raise StateError("Provider manager not available")

        try:
            response = await self._manager.complete(message, stream=False)
            if isinstance(response, AsyncGenerator):
                raise TypeError("Provider returned a streaming response")
            text = response.content.get("text")
            if not isinstance(text, str):
                raise TypeError("Provider returned invalid response format")
            return text
        except Exception as e:
            if isinstance(e, StateError | NotFoundError | TimeoutError | TypeError):
                raise
            raise ConfigurationError(f"Chat completion failed: {e!s}") from e

    async def chat_stream(self, message: str) -> AsyncGenerator[Response, None]:
        """Send a chat message and get a streaming response.

        This method provides direct access to the language model for
        streaming chat interactions.

        Args:
            message: The message to send

        Returns:
            An async generator yielding response chunks

        Raises:
            StateError: If client is not initialized
            ConfigurationError: If provider configuration is invalid
            TimeoutError: If operation times out
        """
        self._ensure_initialized()
        if not self._manager:
            raise StateError("Provider manager not available")

        try:
            response = await self._manager.complete(message, stream=True)
            if isinstance(response, AsyncGenerator):
                return response
            else:
                # If provider doesn't support streaming, yield the entire response
                async def single_response() -> AsyncGenerator[Response, None]:
                    yield response

                return single_response()
        except Exception as e:
            if isinstance(e, StateError | NotFoundError | TimeoutError):
                raise
            raise ConfigurationError(f"Streaming chat completion failed: {e!s}") from e

    async def create_agent(
        self,
        agent_type: str,
        config: T_Config,
    ) -> BaseAgent[T_Input, T_Output, T_Config, T_Context]:
        """Create a new agent instance.

        Args:
            agent_type: Type of agent to create
            config: Agent configuration

        Returns:
            Created and initialized agent instance

        Raises:
            StateError: If client is not initialized
            ConfigurationError: If configuration is invalid
            NotFoundError: If agent type is not found
            TimeoutError: If operation times out
        """
        self._ensure_initialized()

        try:
            # Create context with timestamps
            context = AgentContext(
                agent_id=uuid4(),
                session_id=uuid4(),
                state=AgentState.CREATED,
                created_at=time.time(),
                updated_at=time.time(),
                memory_id=None,  # Optional field
                metadata={},  # Empty metadata
                parent_id=None,  # No parent
            )

            if not self._agent_factory:
                raise RuntimeError("Agent factory not set")

            # Create and initialize agent
            agent = self._agent_factory(
                agent_type,
                context,
                config,
            )

            # Store agent
            self._agents[agent.id] = agent
            self._updated_at = time.time()

            # Trigger hooks
            await self._trigger_hooks(
                "agent_created",
                {"agent_id": str(agent.id), "agent_type": agent_type},
            )

            return agent

        except Exception as e:
            if isinstance(e, StateError | NotFoundError | TimeoutError):
                raise
            raise ConfigurationError(f"Failed to create agent: {e!s}") from e

    def get_agent(
        self, agent_id: UUID
    ) -> BaseAgent[T_Input, T_Output, T_Config, T_Context]:
        """Get an existing agent by ID.

        Args:
            agent_id: Unique identifier of the agent

        Returns:
            The requested agent instance

        Raises:
            StateError: If client is not initialized
            NotFoundError: If agent is not found
        """
        self._ensure_initialized()

        agent = self._agents.get(agent_id)
        if not agent:
            raise NotFoundError(f"Agent not found: {agent_id}")
        return agent

    def list_agents(self) -> list[BaseAgent[T_Input, T_Output, T_Config, T_Context]]:
        """Get a list of all active agents.

        Returns:
            List of active agent instances

        Raises:
            StateError: If client is not initialized
        """
        self._ensure_initialized()
        return list(self._agents.values())

    async def remove_agent(self, agent_id: UUID) -> None:
        """Remove an agent instance.

        This method ensures proper cleanup of the agent before removal.

        Args:
            agent_id: Unique identifier of the agent to remove

        Raises:
            StateError: If client is not initialized
            NotFoundError: If agent is not found
            RuntimeError: If cleanup fails
        """
        self._ensure_initialized()

        agent = self.get_agent(agent_id)
        try:
            # Cleanup agent
            await agent.cleanup()

            # Remove from storage
            del self._agents[agent_id]
            self._updated_at = time.time()

            # Trigger hooks
            await self._trigger_hooks(
                "agent_removed",
                {"agent_id": str(agent_id)},
            )

        except Exception as e:
            if isinstance(e, StateError | NotFoundError):
                raise
            raise RuntimeError(f"Failed to remove agent: {e!s}") from e

    def get_provider(self) -> BaseProvider | None:
        """Get the current provider.

        Returns:
            Current provider instance or None if not set
        """
        return self._provider

    def set_agent_factory(
        self,
        factory: Callable[
            [str, AgentContext, T_Config],
            BaseAgent[T_Input, T_Output, T_Config, T_Context],
        ],
    ) -> None:
        """Set the agent factory.

        Args:
            factory: Factory function for creating agents
        """
        self._agent_factory = factory

    async def setup_provider(
        self,
        provider: BaseProvider,
        config: ProviderConfig | None = None,
    ) -> None:
        """Set up a provider for the client.

        Args:
            provider: Provider instance to use
            config: Optional provider configuration
        """
        self._provider = provider
        if config is not None:
            # Initialize provider (no config needed since it's passed in constructor)
            await provider.initialize()

    def _create_provider_config(
        self,
        *,
        provider_type: str | None = None,
        api_key: str | None = None,
        model: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        timeout: float | None = None,
        max_retries: int | None = None,
        extra_config: dict[str, dict[str, str | int | float | bool]] | None = None,
    ) -> ProviderConfig:
        """Create provider configuration.

        Args:
            provider_type: Type of provider
            api_key: API key for authentication
            model: Model to use
            temperature: Sampling temperature
            max_tokens: Maximum tokens per request
            timeout: Request timeout in seconds
            max_retries: Maximum number of retries
            extra_config: Additional configuration parameters

        Returns:
            Provider configuration.

        Raises:
            ConfigurationError: If required parameters are missing.
        """
        if api_key is None:
            raise ConfigurationError("API key is required")

        # Convert string API key to SecretStr
        secret_key = SecretStr(api_key)

        # Convert extra_config dict to ExtraConfig
        extra_config_model = (
            ExtraConfig(
                model_params=(
                    cast(
                        dict[str, ProviderConfigValue],
                        extra_config.get("model_params", {}),
                    )
                    if extra_config
                    else {}
                ),
                api_params=(
                    cast(
                        dict[str, ProviderConfigValue],
                        extra_config.get("api_params", {}),
                    )
                    if extra_config
                    else {}
                ),
                custom_settings=(
                    cast(
                        dict[str, ProviderConfigValue],
                        extra_config.get("custom_settings", {}),
                    )
                    if extra_config
                    else {}
                ),
            )
            if extra_config
            else ExtraConfig(
                model_params={},
                api_params={},
                custom_settings={},
            )
        )

        return ProviderConfig(
            provider_type=provider_type or "",
            model=model or "",
            timeout=timeout or 30,
            max_retries=max_retries or 3,
            api_key=secret_key,
            extra_config=extra_config_model,
        )
