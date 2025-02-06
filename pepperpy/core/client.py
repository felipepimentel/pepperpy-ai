"""Pepperpy client for interacting with language models.

This module provides the main client interface for interacting with
language models through various providers and managing agent lifecycles.
"""

import time
from collections.abc import AsyncGenerator, Callable, Mapping
from typing import Any, Generic, TypeVar
from uuid import UUID, uuid4

from pydantic import BaseModel, Field
from pydantic.types import SecretStr

from pepperpy.common.config import AutoConfig
from pepperpy.common.errors import ConfigurationError, NotFoundError, StateError
from pepperpy.core.base import AgentContext, AgentState, BaseAgent
from pepperpy.core.types import Response
from pepperpy.monitoring import logger
from pepperpy.providers.base import BaseProvider, ProviderConfig
from pepperpy.providers.manager import ProviderManager
from pepperpy.providers.services.openrouter import OpenRouterProvider

# Type variables for generic implementations
T_Input = TypeVar("T_Input")  # Input data type
T_Output = TypeVar("T_Output")  # Output data type
T_Config = TypeVar("T_Config", bound=Mapping[str, Any])  # Configuration type
T_Context = TypeVar("T_Context")  # Context type


class ClientConfig(BaseModel):
    """Configuration for the Pepperpy client.

    Attributes:
        timeout: Operation timeout in seconds
        max_retries: Maximum number of retries
        retry_delay: Delay between retries in seconds
        provider_type: Type of provider to use
        provider_config: Provider-specific configuration
    """

    timeout: float = Field(default=30.0, gt=0)
    max_retries: int = Field(default=3, ge=0)
    retry_delay: float = Field(default=1.0, ge=0)
    provider_type: str = Field(default="openrouter")
    provider_config: dict[str, Any] = Field(default_factory=dict)


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
        ] = {
            "initialize": set(),
            "cleanup": set(),
            "agent_created": set(),
            "agent_removed": set(),
        }

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

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Clean up resources when exiting async context.

        This ensures all resources are properly released, including:
        - Provider manager cleanup
        - Agent cleanup
        - Connection cleanup
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
        """
        if event not in self._lifecycle_hooks:
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
        """
        if event not in self._lifecycle_hooks:
            raise ValueError(f"Invalid event: {event}")
        self._lifecycle_hooks[event].discard(callback)

    async def initialize(self) -> None:
        """Initialize the client.

        This method:
        1. Loads configuration from environment
        2. Sets up the provider manager
        3. Initializes core services

        Raises:
            ConfigurationError: If configuration is invalid or initialization fails
            TimeoutError: If initialization times out
        """
        try:
            # Load and validate configuration
            env_config = AutoConfig.from_env()
            self._config = ClientConfig(**self._raw_config)
            provider_config = {
                **env_config.get_provider_config(),
                **self._config.provider_config,
            }

            # Initialize provider
            if self._config.provider_type == "openrouter":
                api_key = provider_config.get("api_key")
                if api_key is None:
                    raise ConfigurationError("API key is required")
                if isinstance(api_key, SecretStr):
                    secret_key = api_key
                elif isinstance(api_key, str):
                    secret_key = SecretStr(api_key)
                else:
                    raise ConfigurationError("API key must be a string or SecretStr")

                # Type assertion to help mypy understand the type
                assert isinstance(secret_key, SecretStr)

                config = ProviderConfig(
                    provider_type=self._config.provider_type,
                    timeout=int(self._config.timeout),
                    max_retries=self._config.max_retries,
                    model=provider_config.get("model", ""),
                    api_key=secret_key,
                    extra_config=provider_config,
                )
                provider = OpenRouterProvider(config)
                await provider.initialize()
                self._provider = provider
            else:
                raise ConfigurationError(
                    f"Unsupported provider: {self._config.provider_type}"
                )

            # Create and initialize manager with provider
            if self._provider is None:
                raise ConfigurationError("Provider not initialized")
            self._manager = ProviderManager(primary_provider=self._provider)
            await self._manager.initialize()

            # Update state
            self._initialized = True
            self._updated_at = time.time()

            # Trigger hooks
            for hook in self._lifecycle_hooks["initialize"]:
                try:
                    hook(self)
                except Exception as e:
                    logger.error(
                        "Lifecycle hook failed", event="initialize", error=str(e)
                    )

        except Exception as e:
            if isinstance(e, TimeoutError):
                raise
            raise ConfigurationError(f"Failed to initialize client: {e!s}") from e

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
            for hook in self._lifecycle_hooks["cleanup"]:
                try:
                    hook(self)
                except Exception as e:
                    logger.error("Lifecycle hook failed", event="cleanup", error=str(e))

            # Cleanup provider
            if self._manager:
                await self._manager.cleanup()
                self._manager = None

            # Cleanup agents
            for agent in list(self._agents.values()):
                try:
                    await agent.cleanup()
                except Exception as e:
                    logger.error(
                        "Agent cleanup failed", agent_id=str(agent.id), error=str(e)
                    )

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
            if isinstance(e, StateError | NotFoundError | TimeoutError):
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
            for hook in self._lifecycle_hooks["agent_created"]:
                try:
                    hook(self)
                except Exception as e:
                    logger.error(
                        "Lifecycle hook failed", event="agent_created", error=str(e)
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
            for hook in self._lifecycle_hooks["agent_removed"]:
                try:
                    hook(self)
                except Exception as e:
                    logger.error(
                        "Lifecycle hook failed", event="agent_removed", error=str(e)
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

    def _create_provider_config(self, **kwargs: Any) -> ProviderConfig:
        """Create provider configuration.

        Args:
            **kwargs: Provider configuration parameters.

        Returns:
            Provider configuration.

        Raises:
            ConfigurationError: If required parameters are missing.
        """
        api_key = kwargs.get("api_key")
        if api_key is None:
            raise ConfigurationError("API key is required")
        if not isinstance(api_key, SecretStr):
            api_key = SecretStr(api_key)

        return ProviderConfig(
            provider_type=kwargs.get("provider_type", ""),
            model=kwargs.get("model", ""),
            timeout=kwargs.get("timeout", 30),
            max_retries=kwargs.get("max_retries", 3),
            api_key=api_key,
            extra_config=kwargs.get("extra_config", {}),
        )
