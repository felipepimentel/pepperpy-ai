"""Main PepperPy module.

This module provides the main PepperPy class with a fluent API for
interacting with the framework's components.
"""

import os
from typing import Any, Dict, List, Optional, Union

from pepperpy.core.config import Config
from pepperpy.llm import LLMProvider, Message, MessageRole
from pepperpy.llm import create_provider as create_llm_provider


class ChatBuilder:
    """Fluent builder for chat interactions."""

    def __init__(self, llm: LLMProvider) -> None:
        """Initialize chat builder.

        Args:
            llm: LLM provider to use
        """
        self._llm = llm
        self._messages: List[Message] = []

    def with_system(self, content: str) -> "ChatBuilder":
        """Add a system message.

        Args:
            content: Message content

        Returns:
            Self for chaining
        """
        self._messages.append(Message(role=MessageRole.SYSTEM, content=content))
        return self

    def with_user(self, content: str) -> "ChatBuilder":
        """Add a user message.

        Args:
            content: Message content

        Returns:
            Self for chaining
        """
        self._messages.append(Message(role=MessageRole.USER, content=content))
        return self

    def with_assistant(self, content: str) -> "ChatBuilder":
        """Add an assistant message.

        Args:
            content: Message content

        Returns:
            Self for chaining
        """
        self._messages.append(Message(role=MessageRole.ASSISTANT, content=content))
        return self

    def with_message(self, role: Union[str, MessageRole], content: str) -> "ChatBuilder":
        """Add a message with specific role.

        Args:
            role: Message role
            content: Message content

        Returns:
            Self for chaining
        """
        if isinstance(role, str):
            role = MessageRole(role)
        self._messages.append(Message(role=role, content=content))
        return self

    async def generate(self, **kwargs: Any) -> Any:
        """Generate response from messages.

        Args:
            **kwargs: Additional generation options

        Returns:
            Generation result
        """
        return await self._llm.generate(self._messages, **kwargs)

    async def stream(self, **kwargs: Any) -> Any:
        """Stream response from messages.

        Args:
            **kwargs: Additional generation options

        Returns:
            AsyncIterator of generation chunks
        """
        return self._llm.stream(self._messages, **kwargs)


class PepperPy:
    """Main PepperPy class with fluent API."""

    def __init__(self, config: Optional[Union[Dict[str, Any], Config]] = None) -> None:
        """Initialize PepperPy.

        Args:
            config: Optional configuration dictionary or Config instance
        """
        self.config = config if isinstance(config, Config) else Config(config)
        self._llm: Optional[LLMProvider] = None

    def with_config(self, config: Union[Dict[str, Any], Config]) -> "PepperPy":
        """Configure PepperPy.

        Args:
            config: Configuration dictionary or Config instance

        Returns:
            Self for chaining
        """
        self.config = config if isinstance(config, Config) else Config(config)
        return self

    def with_llm(
        self, provider: Optional[Union[str, LLMProvider]] = None, **kwargs: Any
    ) -> "PepperPy":
        """Configure LLM provider.

        Args:
            provider: LLM provider instance or type name
            **kwargs: Additional provider options

        Returns:
            Self for chaining
        """
        if isinstance(provider, LLMProvider):
            self._llm = provider
        else:
            provider_type = provider or os.getenv("PEPPERPY_LLM__PROVIDER", "openai")
            provider_config = self.config.get("llm.config", {})
            provider_config.update(kwargs)
            self._llm = create_llm_provider(provider_type=provider_type, **provider_config)
        return self

    @property
    def llm(self) -> LLMProvider:
        """Get LLM provider."""
        if not self._llm:
            raise ValueError("LLM provider not configured. Call with_llm() first.")
        return self._llm

    @property
    def chat(self) -> ChatBuilder:
        """Get chat builder."""
        return ChatBuilder(self.llm)

    async def __aenter__(self) -> "PepperPy":
        """Enter async context."""
        if self._llm:
            await self._llm.initialize()
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Exit async context."""
        if self._llm:
            await self._llm.cleanup()
