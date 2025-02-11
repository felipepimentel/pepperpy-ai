"""Core client implementation for the Pepperpy framework.

This module provides the main client interface for interacting with the framework,
including configuration management, agent creation, and workflow execution.
"""

import logging
import time
from collections.abc import AsyncGenerator
from typing import Any, Callable, Dict, Optional, Set, cast
from uuid import UUID

from pydantic import BaseModel, Field
from pydantic.types import SecretStr

from pepperpy.agents.factory import AgentFactory
from pepperpy.core.base import BaseAgent
from pepperpy.core.config import PepperpyConfig
from pepperpy.core.errors import ConfigurationError, StateError
from pepperpy.core.factory import Factory
from pepperpy.core.memory.store import BaseMemoryStore, create_memory_store
from pepperpy.core.messages import Response
from pepperpy.core.prompt.template import PromptTemplate, create_prompt_template
from pepperpy.core.types import (
    PepperpyClientProtocol,
)
from pepperpy.hub.registry import AgentRegistry
from pepperpy.monitoring import logger as log
from pepperpy.providers.base import (
    BaseProvider,
    ExtraConfig,
    ProviderConfig,
    ProviderConfigValue,
    Response,
)
from pepperpy.providers.domain import ProviderError
from pepperpy.providers.domain import ProviderNotFoundError as NotFoundError
from pepperpy.providers.factory import create_provider_factory
from pepperpy.providers.manager import ProviderManager

# Configure logging
logger = logging.getLogger(__name__)

# Error type aliases for better readability
ProviderErrorType = type[ProviderError]
ExceptionType = type[BaseException]

# Valid hook event types
VALID_HOOK_EVENTS = ["before_request", "after_request", "on_error"]

# Type alias for lifecycle hooks
HookCallback = Callable[["PepperpyClient"], None]


class ClientConfig(BaseModel):
    """Configuration for the Pepperpy client.

    Attributes
    ----------
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


class PepperpyClient(PepperpyClientProtocol):
    """Main client interface for the Pepperpy framework.

    This class provides a high-level interface for:
    - Creating and managing agents
    - Executing workflows
    - Managing configuration
    - Handling lifecycle events
    """

    def __init__(
        self,
        config: Optional[PepperpyConfig] = None,
        cache_enabled: bool = True,
        cache_store: str = "memory",
    ) -> None:
        """Initialize the client.

        Args:
        ----
            config: Optional configuration instance
            cache_enabled: Whether to enable caching
            cache_store: Type of cache store to use

        """
        self.config = config or PepperpyConfig.auto()
        self._initialized = False
        self._lifecycle_hooks: Dict[str, Set[HookCallback]] = {
            "before_request": set(),
            "after_request": set(),
            "on_error": set(),
        }
        self._agent_factory: Optional[Factory] = None
        self._cache_enabled = cache_enabled
        self._cache_store = cache_store
        self._provider: Optional[BaseProvider] = None
        self._agents: Dict[UUID, BaseAgent] = {}
        self._memory: Optional[BaseMemoryStore] = None
        self._prompt: Optional[PromptTemplate] = None
        self._manager: Optional[ProviderManager] = None
        self._updated_at = time.time()

    @classmethod
    async def auto(cls) -> "PepperpyClient":
        """Create and initialize a client automatically.

        This method creates a client with automatic configuration and
        initializes it for immediate use.

        Returns:
        -------
            An initialized PepperpyClient instance

        Example:
        -------
            ```python
            async with PepperpyClient.auto() as client:
                agent = await client.get_agent("research_assistant")
                result = await agent.process(...)
            ```

        """
        client = cls()
        await client.initialize()
        return client

    async def initialize(self, config: Optional[PepperpyConfig] = None) -> None:
        """Initialize the client.

        Args:
        ----
            config: Optional client configuration

        Raises:
        ------
            ConfigurationError: If configuration is invalid

        """
        if self._initialized:
            return

        try:
            # Set configuration
            self._config = config or PepperpyConfig()

            # Initialize components
            self._agent_factory = AgentFactory(self)
            self._provider_factory = await create_provider_factory(self._config.dict())
            self._memory = await create_memory_store(self._config.dict())
            self._prompt = await create_prompt_template(self._config.dict())

            # Register built-in agent types
            from pepperpy.agents.research import ResearchAgent

            self._agent_factory.register_agent_type("research_assistant", ResearchAgent)

            # Mark as initialized
            self._initialized = True
            self._updated_at = time.time()

            log.info("Client initialized successfully")

        except Exception as e:
            log.error("Failed to initialize client", error=str(e))
            raise ConfigurationError(f"Failed to initialize client: {e}") from e

    async def cleanup(self) -> None:
        """Clean up client resources."""
        if not self._initialized:
            return

        try:
            # Clean up components
            await self._cleanup_components()
            self._initialized = False
            log.info("Client cleaned up successfully")
        except Exception as e:
            log.error("Failed to clean up client", error=str(e))
            raise

    def add_lifecycle_hook(self, event: str, callback: HookCallback) -> None:
        """Add a lifecycle hook.

        Args:
        ----
            event: Event to hook
            callback: Function to call on event

        """
        if event not in self._lifecycle_hooks:
            raise ValueError(f"Invalid event: {event}")
        self._lifecycle_hooks[event].add(callback)

    def remove_lifecycle_hook(self, event: str, callback: HookCallback) -> None:
        """Remove a lifecycle hook.

        Args:
        ----
            event: Event to unhook
            callback: Function to remove

        """
        if event not in self._lifecycle_hooks:
            raise ValueError(f"Invalid event: {event}")
        self._lifecycle_hooks[event].discard(callback)

    async def get_agent(
        self,
        agent_type: str,
        config: Optional[Dict[str, Any]] = None,
    ) -> BaseAgent:
        """Get an agent instance.

        This is a high-level method that creates and initializes an agent
        in a single call.

        Args:
        ----
            agent_type: Type of agent to create
            config: Optional agent configuration

        Returns:
        -------
            An initialized agent instance

        Example:
        -------
            ```python
            agent = await client.get_agent("research_assistant")
            result = await agent.process(...)
            ```

        """
        if not self._agent_factory:
            raise ConfigurationError("Agent factory not set")

        agent_config = {
            "type": agent_type,
            **(config or {}),
        }

        agent = await self._agent_factory.create(agent_config)
        await agent.initialize(agent_config)
        return agent

    async def run(
        self,
        agent_type: str,
        action: str,
        **kwargs: Any,
    ) -> Any:
        """Run an agent action directly.

        This is a high-level method that handles agent creation, initialization,
        action execution, and cleanup in a single call.

        Args:
        ----
            agent_type: Type of agent to use
            action: Action to execute
            **kwargs: Arguments for the action

        Returns:
        -------
            Result of the action

        Example:
        -------
            ```python
            result = await client.run(
                "research_assistant",
                "analyze_topic",
                topic="AI in Healthcare"
            )
            ```

        """
        agent = await self.get_agent(agent_type)
        try:
            if not hasattr(agent, action):
                raise ValueError(f"Action not found: {action}")
            method = getattr(agent, action)
            return await method(**kwargs)
        finally:
            await agent.cleanup()

    async def run_workflow(
        self,
        workflow_name: str,
        **kwargs: Any,
    ) -> Any:
        """Run a predefined workflow.

        This method executes a workflow defined in the .pepper_hub directory.

        Args:
        ----
            workflow_name: Name of the workflow to run
            **kwargs: Arguments for the workflow

        Returns:
        -------
            Result of the workflow

        Example:
        -------
            ```python
            result = await client.run_workflow(
                "research_simple",
                topic="AI in Healthcare",
                max_sources=5
            )
            ```

        """
        # TODO: Implement workflow execution
        raise NotImplementedError("Workflow execution not implemented yet")

    def set_agent_factory(self, factory: Factory) -> None:
        """Set the agent factory.

        Args:
        ----
            factory: Factory instance for creating agents

        """
        self._agent_factory = factory

    async def _initialize_components(self) -> None:
        """Initialize client components."""
        self._manager = ProviderManager()
        self._provider = await self._manager.get_provider(
            self.config.provider_type,
            self.config.provider_config,
        )
        self._memory = await create_memory_store(self.config.memory_config)
        self._prompt = await create_prompt_template(self.config.prompt_config)

        await self._provider.initialize()

    async def _cleanup_components(self) -> None:
        """Clean up client components."""
        for hook in self._lifecycle_hooks.get("cleanup", set()):
            hook(self)

        for agent in self._agents.values():
            await agent.cleanup()

        self._agents.clear()
        self._provider = None
        self._memory = None
        self._prompt = None
        self._manager = None

    async def __aenter__(self) -> "PepperpyClient":
        """Enter async context."""
        await self.initialize()
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Exit async context."""
        await self.cleanup()

    async def send_message(self, message: str) -> str:
        """Send a message and get a response."""
        if not self._initialized:
            await self.initialize()

        if not self._provider:
            raise StateError("Provider not initialized")

        response = await self._provider.send_message(message)
        return response.content

    async def chat(self, message: str) -> str:
        """Send a chat message and get a response.

        This method provides direct access to the language model for
        simple chat interactions.

        Args:
        ----
            message: The message to send

        Returns:
        -------
            The text response from the provider

        Raises:
        ------
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
        ----
            message: The message to send

        Returns:
        -------
            An async generator yielding response chunks

        Raises:
        ------
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
        config: Optional[Dict[str, Any]] = None,
    ) -> BaseAgent:
        """Create an agent instance.

        Args:
        ----
            agent_type: Type of agent to create
            config: Optional agent configuration

        Returns:
        -------
            Created agent instance

        Raises:
        ------
            ConfigurationError: If agent type is not supported

        """
        if not self._agent_factory:
            raise ConfigurationError("Agent factory not set")

        agent_config = {
            "type": agent_type,
            **(config or {}),
        }

        try:
            agent = await self._agent_factory.create(agent_config)
            await agent.initialize(agent_config)
            return agent
        except Exception as e:
            raise ConfigurationError(f"Failed to create agent: {e}") from e

    def get_agent(self, agent_id: UUID) -> BaseAgent:
        """Get an existing agent by ID.

        Args:
        ----
            agent_id: Unique identifier of the agent

        Returns:
        -------
            The requested agent instance

        Raises:
        ------
            StateError: If client is not initialized
            NotFoundError: If agent is not found

        """
        self._ensure_initialized()

        agent = self._agents.get(agent_id)
        if not agent:
            raise NotFoundError(f"Agent not found: {agent_id}")
        return agent

    def list_agents(self) -> list[BaseAgent]:
        """Get a list of all active agents.

        Returns
        -------
            List of active agent instances

        Raises
        ------
            StateError: If client is not initialized

        """
        self._ensure_initialized()
        return list(self._agents.values())

    async def remove_agent(self, agent_id: UUID) -> None:
        """Remove an agent instance.

        This method ensures proper cleanup of the agent before removal.

        Args:
        ----
            agent_id: Unique identifier of the agent to remove

        Raises:
        ------
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

        Returns
        -------
            Current provider instance or None if not set

        """
        return self._provider

    def _ensure_initialized(self) -> None:
        """Ensure the client is initialized.

        Raises
        ------
            StateError: If client is not initialized

        """
        if not self._initialized:
            raise StateError("Client not initialized")

    async def _get_cached_result(self, key: str) -> Any:
        """Get a cached result if available.

        Args:
        ----
            key: Cache key

        Returns:
        -------
            Cached result if found and valid, None otherwise

        """
        if not self._cache_enabled or not self._memory:
            return None

        try:
            entry = await self._memory.get(key)
            if entry and hasattr(entry, "value"):
                return entry.value
        except Exception as e:
            logger.warning(f"Failed to get cached result: {e}")
        return None

    async def _cache_result(self, key: str, value: Any) -> None:
        """Cache a result.

        Args:
        ----
            key: Cache key
            value: Value to cache

        """
        if not self._cache_enabled or not self._memory:
            return

        try:
            await self._memory.set(key, value)
        except Exception as e:
            logger.warning(f"Failed to cache result: {e}")

    async def _trigger_hooks(
        self,
        event: str,
        error_context: dict[str, Any] | None = None,
    ) -> None:
        """Trigger lifecycle hooks for an event.

        Args:
        ----
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
        ----
            provider_type: Type of provider
            api_key: API key for authentication
            model: Model to use
            temperature: Sampling temperature
            max_tokens: Maximum tokens per request
            timeout: Request timeout in seconds
            max_retries: Maximum number of retries
            extra_config: Additional configuration parameters

        Returns:
        -------
            Provider configuration.

        Raises:
        ------
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

    async def get_agent(
        self, agent_type: str, version: Optional[str] = None, **kwargs: Any
    ) -> Any:
        """Get or create an agent of the specified type.

        This method handles agent creation and configuration automatically.
        If no version is specified, it will use the latest available version.

        Args:
        ----
            agent_type: Type of agent to get/create (e.g., "research_assistant")
            version: Optional specific version to use (e.g., "1.2.3")
            **kwargs: Additional configuration overrides

        Returns:
        -------
            The requested agent instance

        Example:
        -------
            ```python
            # Get latest version
            agent = await client.get_agent("research_assistant")

            # Get specific version
            agent = await client.get_agent("research_assistant", version="1.2.3")
            ```

        Raises:
        ------
            ValueError: If agent_type is invalid or version not found

        """
        # Get agent configuration from registry
        registry = AgentRegistry()
        agent_config = await registry.get_agent_config(
            agent_type=agent_type,
            version=version,  # None means latest
        )

        # Merge with any overrides
        agent_config.update(kwargs)

        # Create the agent
        agent = await self.create_agent(agent_type=agent_type, config=agent_config)

        return agent
