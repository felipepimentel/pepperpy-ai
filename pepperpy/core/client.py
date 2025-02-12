"""Core client implementation for the Pepperpy framework.

This module provides the main client interface for interacting with the framework,
including zero-config setup, agent management, and workflow execution.
"""

import asyncio
import logging
import time
from collections.abc import AsyncGenerator, Sequence
from pathlib import Path
from typing import Any, Callable, Dict, Optional, Set, TypeVar, cast
from uuid import UUID, uuid4

from pydantic import BaseModel, Field
from pydantic.types import SecretStr

from pepperpy.agents.factory import AgentFactory
from pepperpy.agents.research_assistant import ResearchAssistant
from pepperpy.core.base import BaseAgent
from pepperpy.core.config import PepperpyConfig
from pepperpy.core.errors import ConfigurationError, StateError
from pepperpy.core.factory import Factory
from pepperpy.core.hooks import HookCallback
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
)
from pepperpy.providers.base import (
    Response as ProviderResponse,
)
from pepperpy.providers.domain import ProviderError, ProviderNotFoundError
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
AgentType = TypeVar("AgentType", bound=BaseAgent)


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
    - Zero-config setup with automatic configuration
    - Simple agent and workflow execution
    - Built-in caching and monitoring
    - Plugin/hook system for customization
    """

    def __init__(
        self,
        config: Optional[PepperpyConfig] = None,
        *,
        cache_enabled: bool = True,
        cache_store: str = "memory",
    ) -> None:
        """Initialize the client.

        Args:
            config: Optional configuration instance
            cache_enabled: Whether to enable caching
            cache_store: Type of cache store to use

        Example:
            ```python
            # Auto-configured client
            client = PepperpyClient.auto()

            # Custom configuration
            client = PepperpyClient(
                config=my_config,
                cache_enabled=True,
                cache_store="redis"
            )
            ```

        """
        self.config = config or PepperpyConfig.auto()
        self._initialized = False
        self._lifecycle_hooks: Dict[str, Set[HookCallback]] = {
            "before_request": set(),
            "after_request": set(),
            "on_error": set(),
        }
        self._agent_factory: Optional[AgentFactory] = None
        self._cache_enabled = cache_enabled
        self._cache_store = cache_store
        self._provider: Optional[BaseProvider] = None
        self._agents: Dict[UUID, BaseAgent] = {}
        self._memory: Optional[BaseMemoryStore] = None
        self._prompt: Optional[PromptTemplate] = None
        self._updated_at = time.time()

    @classmethod
    async def auto(cls) -> "PepperpyClient":
        """Create and initialize a client automatically.

        This method creates a client with automatic configuration and
        initializes it for immediate use.

        Returns:
            An initialized PepperpyClient instance

        Example:
            ```python
            async with PepperpyClient.auto() as client:
                result = await client.run(
                    "research_assistant",
                    "analyze",
                    topic="AI in Healthcare"
                )
            ```

        """
        client = cls()
        await client.initialize()
        return client

    async def initialize(self) -> None:
        """Initialize the client."""
        if self._initialized:
            return

        try:
            # Initialize components
            self._agent_factory = AgentFactory(self)
            self._provider = create_provider_factory(
                default_provider=self.config.provider_type,
                default_config=self.config.provider_config,
            )
            await self._provider.initialize()
            self._memory = await create_memory_store(self.config.memory_config)
            self._prompt = await create_prompt_template(self.config.prompt_config)

            # Register built-in agent types
            self._agent_factory.register_agent_type(
                "research_assistant", ResearchAssistant
            )

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
            cleanup_tasks = []
            for agent_id, agent in list(self._agents.items()):
                task = asyncio.create_task(agent.cleanup())
                cleanup_tasks.append(task)

            # Wait for all cleanup tasks to complete
            await asyncio.gather(*cleanup_tasks, return_exceptions=True)

            self._agents.clear()
            self._provider = None
            self._memory = None
            self._prompt = None
            self._initialized = False
            self._updated_at = time.time()

        except Exception as e:
            log.error("Failed to cleanup client", error=str(e))
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
            agent_type: Type of agent to use
            action: Action to execute
            **kwargs: Arguments for the action

        Returns:
            Result of the action

        Example:
            ```python
            result = await client.run(
                "research_assistant",
                "analyze",
                topic="AI in Healthcare"
            )
            ```

        """
        agent = await self.get_agent(agent_type)
        try:
            if not hasattr(agent, action):
                raise ValueError(f"Action not found: {action}")
            method = getattr(agent, action)
            result = await method(**kwargs)
            await agent.cleanup()
            return result
        except Exception:
            if agent:
                await agent.cleanup()
            raise

    async def run_workflow(
        self,
        workflow_name: str,
        **kwargs: Any,
    ) -> Any:
        """Run a predefined workflow.

        This method executes a workflow defined in the .pepper_hub directory.

        Args:
            workflow_name: Name of the workflow to run
            **kwargs: Arguments for the workflow

        Returns:
            Result of the workflow

        Example:
            ```python
            result = await client.run_workflow(
                "research/comprehensive",
                topic="AI in Healthcare",
                max_sources=5
            )
            ```

        """
        workflow_path = (
            Path.home() / ".pepper_hub" / "workflows" / f"{workflow_name}.yml"
        )
        if not workflow_path.exists():
            raise ConfigurationError(f"Workflow not found: {workflow_name}")

        try:
            # TODO: Implement workflow execution
            raise NotImplementedError("Workflow execution not implemented yet")
        except Exception as e:
            log.error(
                "Workflow execution failed",
                workflow=workflow_name,
                error=str(e),
                **kwargs,
            )
            raise

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

    async def __aenter__(self) -> "PepperpyClient":
        """Enter async context."""
        if not self._initialized:
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
            if isinstance(
                e, StateError | ProviderNotFoundError | TimeoutError | TypeError
            ):
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
            if isinstance(e, StateError | ProviderNotFoundError | TimeoutError):
                raise
            raise ConfigurationError(f"Streaming chat completion failed: {e!s}") from e

    async def create_agent(self, agent_type: str) -> BaseAgent:
        """Create a new agent instance."""
        if not self._agent_factory:
            raise ConfigurationError("Agent factory not set")

        try:
            # Get agent configuration from registry
            registry = AgentRegistry()
            agent_config = await registry.get_agent_config(agent_type)

            # Create and initialize the agent
            agent = await self._agent_factory.create(agent_config)
            agent_id = uuid4()
            self._agents[agent_id] = agent
            await asyncio.create_task(agent.initialize())
            return agent

        except Exception as e:
            log.error(
                "Failed to create agent",
                agent_type=agent_type,
                error=str(e),
            )
            raise

    async def get_agent(self, agent_id: UUID) -> BaseAgent:
        """Get an existing agent instance by ID."""
        if agent_id not in self._agents:
            raise ValueError(f"Agent not found: {agent_id}")
        return self._agents[agent_id]

    def list_agents(self) -> Sequence[BaseAgent]:
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
            if isinstance(e, StateError | ProviderNotFoundError):
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
        """Ensure the client is initialized."""
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

    async def stream_chat(
        self,
        messages: list[dict[str, str]],
        **kwargs: Any,
    ) -> AsyncGenerator[ProviderResponse, None]:
        """Stream chat completion responses."""
        self._ensure_initialized()

        if not self._provider:
            raise StateError("Provider not initialized")

        try:
            async for response in self._provider.stream_chat(messages, **kwargs):
                yield response
        except Exception as e:
            if isinstance(e, StateError | ProviderNotFoundError | TimeoutError):
                raise
            raise ConfigurationError(f"Streaming chat completion failed: {e!s}") from e
