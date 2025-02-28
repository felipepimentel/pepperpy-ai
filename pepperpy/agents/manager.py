"""Agent manager for coordinating agent creation and execution."""

import asyncio
import logging
from typing import Any, Dict, List, Type
from uuid import UUID

from pepperpy.agents.base import (
    AgentConfig,
    AgentError,
    AgentMessage,
    AgentProvider,
    AgentResponse,
)
from pepperpy.agents.chains.base import Chain, ChainConfig, ChainError, ChainResult
from pepperpy.core.errors import ConfigurationError

logger = logging.getLogger(__name__)


class AgentManager:
    """Manager for coordinating agents and chains."""

    def __init__(self) -> None:
        """Initialize the agent manager."""
        self._providers: Dict[str, AgentProvider] = {}
        self._chains: Dict[UUID, Chain] = {}
        self._lock = asyncio.Lock()

    async def register_provider(
        self,
        name: str,
        provider: Type[AgentProvider],
        **config: Any,
    ) -> None:
        """Register an agent provider.

        Args:
            name: Provider name
            provider: Provider class
            **config: Provider configuration

        Raises:
            ConfigurationError: If provider already registered
        """
        if name in self._providers:
            raise ConfigurationError(f"Provider {name} already registered")

        try:
            instance = provider(**config)
            self._providers[name] = instance
            logger.info("Registered agent provider", extra={"provider": name})
        except Exception as e:
            raise ConfigurationError(f"Failed to initialize provider: {e}")

    async def create_agent(
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
            ConfigurationError: If provider not found
            AgentError: If creation fails
        """
        if config.provider not in self._providers:
            raise ConfigurationError(f"Provider {config.provider} not found")

        try:
            provider = self._providers[config.provider]
            agent_id = await provider.create(config, **kwargs)
            logger.info(
                "Created agent",
                extra={
                    "agent_id": agent_id,
                    "provider": config.provider,
                },
            )
            return agent_id
        except Exception as e:
            raise AgentError(f"Failed to create agent: {e}")

    async def execute_agent(
        self,
        agent_id: str,
        messages: List[AgentMessage],
        provider_name: str,
        **kwargs: Any,
    ) -> AgentResponse:
        """Execute an agent.

        Args:
            agent_id: Agent ID to execute
            messages: Messages to process
            provider_name: Provider to use
            **kwargs: Additional provider-specific parameters

        Returns:
            Agent response

        Raises:
            ConfigurationError: If provider not found
            AgentError: If execution fails
        """
        if provider_name not in self._providers:
            raise ConfigurationError(f"Provider {provider_name} not found")

        try:
            provider = self._providers[provider_name]
            response = await provider.execute(agent_id, messages, **kwargs)
            logger.info(
                "Executed agent",
                extra={
                    "agent_id": agent_id,
                    "provider": provider_name,
                },
            )
            return response
        except Exception as e:
            raise AgentError(f"Failed to execute agent: {e}")

    async def create_chain(
        self,
        config: ChainConfig,
        chain_type: Type[Chain],
        **kwargs: Any,
    ) -> UUID:
        """Create a new chain.

        Args:
            config: Chain configuration
            chain_type: Chain implementation class
            **kwargs: Additional chain-specific parameters

        Returns:
            Chain ID

        Raises:
            ConfigurationError: If chain already exists
            ChainError: If creation fails
        """
        if config.id in self._chains:
            raise ConfigurationError(f"Chain {config.id} already exists")

        try:
            chain = chain_type(config, **kwargs)
            self._chains[config.id] = chain
            logger.info(
                "Created chain",
                extra={
                    "chain_id": str(config.id),
                    "type": chain_type.__name__,
                },
            )
            return config.id
        except Exception as e:
            raise ChainError(f"Failed to create chain: {e}")

    async def execute_chain(
        self,
        chain_id: UUID,
        messages: List[AgentMessage],
        **kwargs: Any,
    ) -> ChainResult:
        """Execute a chain.

        Args:
            chain_id: Chain ID to execute
            messages: Initial messages
            **kwargs: Additional execution parameters

        Returns:
            Chain execution result

        Raises:
            ConfigurationError: If chain not found
            ChainError: If execution fails
        """
        if chain_id not in self._chains:
            raise ConfigurationError(f"Chain {chain_id} not found")

        try:
            chain = self._chains[chain_id]
            result = await chain.execute(messages, **kwargs)
            logger.info(
                "Executed chain",
                extra={
                    "chain_id": str(chain_id),
                    "steps": len(result.steps),
                },
            )
            return result
        except Exception as e:
            raise ChainError(f"Failed to execute chain: {e}")

    async def cleanup(self) -> None:
        """Clean up all providers and chains."""
        async with self._lock:
            # Clean up providers
            for name, provider in self._providers.items():
                try:
                    await provider.cleanup()
                    logger.info(
                        "Cleaned up provider",
                        extra={"provider": name},
                    )
                except Exception as e:
                    logger.error(
                        "Failed to clean up provider",
                        extra={
                            "provider": name,
                            "error": str(e),
                        },
                    )

            # Clear tracking
            self._providers.clear()
            self._chains.clear()
