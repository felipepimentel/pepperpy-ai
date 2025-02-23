"""Core client implementation for the Pepperpy framework.

This module provides the main client interface for interacting with the framework,
including zero-config setup, agent management, and workflow execution.
"""

import asyncio
import time
from collections.abc import AsyncGenerator, Sequence
from pathlib import Path
from typing import TYPE_CHECKING, Any, Protocol, TypeVar
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from pepperpy.core.base import BaseAgent
from pepperpy.core.errors import ConfigurationError, StateError
from pepperpy.core.lifecycle import Lifecycle
from pepperpy.core.logging import get_logger
from pepperpy.core.messages import (
    Message,
    ProviderMessage,
    ProviderResponse,
    Response,
)
from pepperpy.core.prompts import PromptTemplate, create_prompt_template
from pepperpy.core.providers import (
    BaseProvider,
    ProviderConfig,
    ProviderManager,
)
from pepperpy.core.providers.errors import (
    ProviderError,
    ProviderNotFoundError,
)
from pepperpy.core.types import PepperpyClientProtocol
from pepperpy.memory.base import BaseMemoryStore, MemoryEntry, MemoryQuery, MemoryType
from pepperpy.memory.stores.memory import InMemoryStore

if TYPE_CHECKING:
    from pepperpy.agents.factory import AgentFactory

# Configure logging
logger = get_logger(__name__)

# Type aliases for better readability
ProviderErrorType = type[ProviderError]
ExceptionType = type[BaseException]

# Valid hook event types
VALID_HOOK_EVENTS = ["before_request", "after_request", "on_error"]


# Type alias for lifecycle hooks
class HookCallback(Protocol):
    """Protocol for lifecycle hooks."""

    def __call__(self, client: "PepperpyClient") -> None: ...


AgentType = TypeVar("AgentType", bound=BaseAgent)


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
    provider_config: dict[str, Any] = Field(default_factory=dict)
    memory_config: dict[str, Any] = Field(default_factory=dict)
    prompt_config: dict[str, Any] = Field(default_factory=dict)


class PepperpyClient(PepperpyClientProtocol, Lifecycle):
    """Main client interface for the Pepperpy framework.

    This class provides a high-level interface for:
    - Zero-config setup with automatic configuration
    - Simple agent and workflow execution
    - Built-in caching and monitoring
    - Plugin/hook system for customization
    """

    def __init__(self, config: dict[str, Any]) -> None:
        """Initialize the client."""
        self._raw_config = config
        self._provider: BaseProvider | None = None
        self._initialized = False
        self._lifecycle_hooks: dict[str, set[HookCallback]] = {
            "before_request": set(),
            "after_request": set(),
            "on_error": set(),
        }
        self._agent_factory: AgentFactory | None = None
        self._cache_enabled = True
        self._cache_store = "memory"
        self._agents: dict[UUID, BaseAgent] = {}
        self._memory: BaseMemoryStore[dict[str, Any]] | None = None
        self._prompt: PromptTemplate | None = None
        self._updated_at = time.time()
        self._manager = ProviderManager()

    @classmethod
    async def auto(cls) -> "PepperpyClient":
        """Create and initialize a client automatically."""
        client = cls({})  # Initialize with empty config
        await client.initialize()
        return client

    async def initialize(self) -> None:
        """Initialize the client."""
        if self._initialized:
            raise StateError("Client already initialized")

        try:
            # Get provider instance
            provider_type = self._raw_config.get("provider_type", "openrouter")
            provider_config = self._raw_config.get("provider_config", {})
            provider_config_obj = ProviderConfig(
                id=uuid4(),
                type=provider_type,
                config=provider_config,
            )
            self._provider = await self._manager.get_provider(
                provider_type,
                provider_config_obj.config,
            )

            # Initialize components
            await self._initialize_components()
            self._initialized = True
            self._updated_at = time.time()

        except Exception:
            logger.error("Failed to initialize client", exc_info=True)
            raise

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

            # Clean up manager and provider
            if self._manager:
                await self._manager.cleanup()

            self._agents.clear()
            self._provider = None
            self._memory = None
            self._prompt = None
            self._initialized = False
            self._updated_at = time.time()

        except Exception:
            logger.error("Failed to cleanup client", exc_info=True)
            raise

    def add_lifecycle_hook(self, event: str, callback: HookCallback) -> None:
        """Add a lifecycle hook.

        Args:
            event: Event to hook
            callback: Function to call on event
        """
        if event not in self._lifecycle_hooks:
            raise ValueError(f"Invalid event: {event}")
        self._lifecycle_hooks[event].add(callback)

    def remove_lifecycle_hook(self, event: str, callback: HookCallback) -> None:
        """Remove a lifecycle hook.

        Args:
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
        if not self._agent_factory:
            raise StateError("Agent factory not configured")

        try:
            agent = await self._agent_factory.execute(
                agent_type=agent_type,
                **kwargs,
            )
            if not hasattr(agent, action):
                raise ValueError(f"Action not found: {action}")

            method = getattr(agent, action)
            result = await method(**kwargs)
            await agent.cleanup()
            return result

        except Exception as e:
            logger.error(
                "Failed to run agent action",
                exc_info=True,
                extra={
                    "agent_type": agent_type,
                    "action": action,
                    "error": str(e),
                },
            )
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
            logger.error(
                "Workflow execution failed",
                exc_info=True,
                extra={
                    "workflow_name": workflow_name,
                    "error": str(e),
                    **kwargs,
                },
            )
            raise

    def set_agent_factory(self, factory: "AgentFactory") -> None:
        """Set the agent factory.

        Args:
            factory: Factory instance for creating agents
        """
        self._agent_factory = factory

    async def _initialize_components(self) -> None:
        """Initialize client components."""
        try:
            self._memory = InMemoryStore(
                name="client_memory", config=self._raw_config.get("memory_config", {})
            )
            await self._memory.initialize()
            self._prompt = await create_prompt_template(
                self._raw_config.get("prompt_config", {})
            )

        except Exception:
            logger.error("Failed to initialize components", exc_info=True)
            raise

    async def _cleanup_components(self) -> None:
        """Clean up client components."""
        for hook in self._lifecycle_hooks.get("cleanup", set()):
            hook(self)

        for agent in self._agents.values():
            await agent.cleanup()

        if self._manager:
            await self._manager.cleanup()

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

        try:
            provider_type = self._raw_config.get("provider_type", "openrouter")
            provider_config = self._raw_config.get("provider_config", {})
            provider_config_obj = ProviderConfig(
                id=uuid4(),
                type=provider_type,
                config=provider_config,
            )
            self._provider = await self._manager.get_provider(
                provider_type,
                provider_config_obj.config,
            )

            provider_message = ProviderMessage(
                content=message,
                provider_type=provider_type,
                provider_id=self._provider.id if self._provider else None,
            )
            response = await self._provider.process_message(provider_message)
            if isinstance(response, AsyncGenerator):
                raise TypeError("Provider returned a streaming response")
            if isinstance(response, ProviderResponse):
                return str(response.content)
            return str(response)
        except Exception:
            logger.error("Failed to send message", exc_info=True)
            raise

    async def chat(self, message: str, **kwargs: Any) -> str:
        """Send a chat message and get a response.

        This method provides direct access to the language model for
        simple chat interactions.

        Args:
            message: The message to send
            **kwargs: Additional parameters like temperature, max_tokens etc.

        Returns:
            The text response from the provider

        Raises:
            StateError: If client is not initialized
            TypeError: If provider returns a streaming response
            ConfigurationError: If provider configuration is invalid
            TimeoutError: If operation times out
        """
        if not self._initialized:
            await self.initialize()

        if not self._provider:
            raise StateError("Provider not initialized")

        try:
            provider_message = ProviderMessage(
                content=message,
                provider_type=self._provider.type,
                provider_id=self._provider.id,
            )
            response = await self._provider.process_message(provider_message)
            if isinstance(response, AsyncGenerator):
                raise TypeError("Provider returned a streaming response")
            if isinstance(response, ProviderResponse):
                return str(response.content)
            return str(response)
        except Exception as e:
            if isinstance(
                e, (StateError, ProviderNotFoundError, TimeoutError, TypeError)
            ):
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
        if not self._provider:
            raise StateError("Provider not initialized")

        try:
            provider_message = ProviderMessage(
                content=message,
                provider_type=self._provider.type,
                provider_id=self._provider.id,
            )
            response = await self._provider.process_message(provider_message)
            if isinstance(response, AsyncGenerator):
                async for chunk in response:
                    if isinstance(chunk, ProviderResponse):
                        yield Response(
                            id=uuid4(),
                            content=str(chunk.content),
                            metadata={"original_id": str(chunk.id)},
                        )
            elif isinstance(response, ProviderResponse):
                yield Response(
                    id=uuid4(),
                    content=str(response.content),
                    metadata={"original_id": str(response.id)},
                )
        except Exception as e:
            if isinstance(e, (StateError, ProviderNotFoundError, TimeoutError)):
                raise
            raise ConfigurationError(f"Streaming chat completion failed: {e!s}") from e

    async def create_agent(self, agent_type: str) -> BaseAgent:
        """Create a new agent instance.

        Args:
            agent_type: Type of agent to create

        Returns:
            Created agent instance

        Raises:
            ConfigurationError: If agent factory is not set
            AgentError: If agent creation fails
        """
        if not self._agent_factory:
            raise ConfigurationError("Agent factory not set")

        try:
            # Create and initialize the agent
            agent = await self._agent_factory.execute(agent_type=agent_type)
            agent_id = uuid4()
            self._agents[agent_id] = agent
            await agent.initialize()
            return agent

        except Exception as e:
            logger.error(
                "Failed to create agent",
                extra={
                    "agent_type": agent_type,
                    "error": str(e),
                },
            )
            raise

    async def get_agent(self, agent_id: str | UUID) -> BaseAgent:
        """Get an existing agent instance by ID.

        Args:
            agent_id: Agent identifier (string or UUID)

        Returns:
            The agent instance

        Raises:
            ValueError: If agent not found
        """
        if isinstance(agent_id, str):
            # Try to convert string to UUID
            try:
                agent_id = UUID(agent_id)
            except ValueError:
                # If not a valid UUID, try to create agent by type
                return await self.create_agent(agent_id)

        if agent_id not in self._agents:
            raise ValueError(f"Agent not found: {agent_id}")
        return self._agents[agent_id]

    def list_agents(self) -> Sequence[BaseAgent]:
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

        agent = await self.get_agent(agent_id)
        try:
            # Cleanup agent
            if hasattr(agent, "cleanup"):
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

        Returns:
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
            key: Cache key

        Returns:
            Cached result if found and valid, None otherwise
        """
        if not self._cache_enabled or not self._memory:
            return None

        try:
            query = MemoryQuery(query=key)
            async for result in self._memory.retrieve(query):
                if result.entry.key == key:
                    return result.entry.value
        except Exception as e:
            logger.warning(f"Failed to get cached result: {e}")
        return None

    async def _cache_result(self, key: str, value: Any) -> None:
        """Cache a result.

        Args:
            key: Cache key
            value: Value to cache
        """
        if not self._cache_enabled or not self._memory:
            return

        try:
            entry = MemoryEntry(
                key=key, value={"result": value}, type=MemoryType.SHORT_TERM
            )
            await self._memory.store(entry)
        except Exception as e:
            logger.warning(f"Failed to cache result: {e}")

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

    def _create_provider_config(
        self,
        *,
        api_key: str | None = None,
        model: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        timeout: float | None = None,
        max_retries: int | None = None,
        base_url: str | None = None,
        extra: dict[str, dict[str, str | int | float | bool]] | None = None,
    ) -> ProviderConfig:
        """Create provider configuration."""
        if api_key is None:
            raise ConfigurationError("API key is required")

        # Create base config with required fields
        config = ProviderConfig(
            id=uuid4(),
            type="openai",  # Default provider
            config={
                "api_key": api_key,
                "model": model or "gpt-4-turbo-preview",
                "temperature": temperature or 0.7,
                "max_tokens": max_tokens or 1000,
                "timeout": int(timeout or 30),  # Convert to int
                "max_retries": max_retries or 3,
                "base_url": base_url,  # Can be None
            },
        )

        # Add extra parameters if provided
        if extra:
            config.config.update(extra)

        return config

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
            # Convert dict messages to provider messages
            provider_messages = [
                ProviderMessage(
                    content=msg.get("content", ""),
                    provider_type=self._provider.type,
                    provider_id=self._provider.id,
                    metadata={"role": msg.get("role", "user")},
                )
                for msg in messages
            ]

            # Use provider's process_message interface
            response = await self._provider.process_message(provider_messages[0])
            if isinstance(response, AsyncGenerator):
                async for chunk in response:
                    if isinstance(chunk, ProviderResponse):
                        yield chunk
            elif isinstance(response, ProviderResponse):
                yield response

        except Exception as e:
            if isinstance(e, (StateError, ProviderNotFoundError, TimeoutError)):
                raise
            raise ConfigurationError(f"Streaming chat completion failed: {e!s}") from e

    async def stream(
        self, messages: Sequence[Message], **kwargs: Any
    ) -> AsyncGenerator[Response, None]:
        """Stream responses from the provider.

        Args:
            messages: List of messages to send
            **kwargs: Additional provider-specific arguments

        Yields:
            Response tokens as they are generated

        Raises:
            ConfigurationError: If client is not initialized
            ProviderError: If provider fails to generate response
        """
        if not self._initialized:
            raise ConfigurationError("Client not initialized")

        if not self._provider:
            raise StateError("Provider not initialized")

        provider_messages = [
            ProviderMessage(
                content=msg.content,
                provider_type=self._provider.type,
                provider_id=self._provider.id,
                metadata={"role": "user"},
            )
            for msg in messages
        ]

        try:
            response = await self._provider.process_message(provider_messages[0])
            if isinstance(response, AsyncGenerator):
                async for chunk in response:
                    if isinstance(chunk, ProviderResponse):
                        yield Response(
                            id=uuid4(),
                            content=str(chunk.content),
                            metadata={"original_id": str(chunk.id)},
                        )
            elif isinstance(response, ProviderResponse):
                yield Response(
                    id=uuid4(),
                    content=str(response.content),
                    metadata={"original_id": str(response.id)},
                )
        except Exception as e:
            raise ProviderError(f"Failed to stream response: {e!s}") from e

    async def clear_history(self) -> None:
        """Clear the conversation history.

        This method resets the conversation state, removing all previous
        messages and context.

        Example:
            >>> await client.clear_history()  # Reset conversation
        """
        self._ensure_initialized()
        if self._memory:
            await self._memory.cleanup()
