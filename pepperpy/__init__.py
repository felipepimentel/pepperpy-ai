"""Pepperpy - A Python library for building AI-powered research assistants.

This module provides a high-level API for creating and managing AI agents
specialized in research tasks, including topic analysis, source discovery,
and information synthesis.
"""

import asyncio
import os
from pathlib import Path
from typing import Any, AsyncIterator, Dict, Optional, Union
from uuid import uuid4

from pepperpy.core.client import PepperpyClient
from pepperpy.core.config import PepperpyConfig
from pepperpy.core.types import Message, MessageType, Response
from pepperpy.hub import PepperpyHub
from pepperpy.hub.agents import ResearchAssistantAgent

__version__ = "0.1.0"


class Pepperpy:
    """Main entry point for the Pepperpy library.

    This class provides a simplified interface for using Pepperpy's capabilities.

    Examples:
        Basic usage:
        >>> pepper = await Pepperpy.create()  # Auto-configura do .env
        >>> result = await pepper.ask("What is AI?")
        >>> print(result)

        With custom settings:
        >>> pepper = await Pepperpy.create(api_key="my-key")  # Configuração mínima
        >>> result = await pepper.research("Impact of AI")
        >>> print(result.tldr)  # Short summary

        Interactive setup:
        >>> pepper = Pepperpy.quick_start()  # Guia interativo de configuração
        >>> async with pepper as p:
        ...     result = await p.ask("What is AI?")

    """

    def __init__(self, client: Optional[PepperpyClient] = None):
        """Initialize Pepperpy with an optional client."""
        self._client: Optional[PepperpyClient] = client
        self._initialized = False
        self._interactive = False

    @classmethod
    async def create(
        cls,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        **kwargs: Any,
    ) -> "Pepperpy":
        """Create a new Pepperpy instance with minimal configuration.

        Args:
            api_key: Optional API key. If not provided, will try to read from PEPPERPY_API_KEY env var
            model: Optional model name. If not provided, will use default from config
            **kwargs: Additional configuration options

        Returns:
            A configured Pepperpy instance ready to use

        Example:
            >>> pepper = await Pepperpy.create(api_key="my-key")
            >>> result = await pepper.ask("What is AI?")
            >>> print(result)

            # Or with environment variables:
            >>> pepper = await Pepperpy.create()  # Uses PEPPERPY_API_KEY
            >>> result = await pepper.research("AI in Healthcare")
            >>> print(result.tldr)

        """
        # Create instance
        instance = cls()

        # Setup config with smart defaults
        config = PepperpyConfig.auto()

        # Override with provided values
        if api_key:
            config.provider_config["api_key"] = api_key
        if model:
            config.provider_config["model"] = model

        # Add any additional config
        for key, value in kwargs.items():
            config.provider_config[key] = value

        # Create and initialize client
        client = PepperpyClient(config=config.model_dump())
        await client.initialize()

        # Store client
        instance._client = client
        instance._initialized = True

        return instance

    @classmethod
    async def quick_start(cls) -> "Pepperpy":
        """Start an interactive setup process.

        This method launches a CLI wizard to help configure Pepperpy
        with a friendly step-by-step guide.

        Returns:
            A configured Pepperpy instance

        Example:
            >>> pepper = await Pepperpy.quick_start()
            >>> # Follow the interactive prompts...
            >>> async with pepper as p:
            ...     result = await p.ask("What is AI?")

        """
        from pepperpy.cli.setup import setup_wizard

        return await setup_wizard()

    async def ask(self, question: str, **kwargs: Any) -> str:
        """Ask a question and get a response.

        This is the simplest way to interact with Pepperpy. Just ask
        a question and get a direct response.

        Args:
            question: The question to ask
            **kwargs: Additional parameters like temperature, max_tokens etc.

        Returns:
            The AI's response

        Example:
            >>> result = await pepper.ask("What is AI?")
            >>> print(result)

            # With parameters
            >>> result = await pepper.ask(
            ...     "Explain quantum computing",
            ...     temperature=0.7,
            ...     max_tokens=500
            ... )

        Raises:
            RuntimeError: If Pepperpy is not initialized

        """
        if not self._initialized or not self._client:
            raise RuntimeError("Pepperpy not initialized. Call create() first.")
        return await self._client.chat(question, **kwargs)

    async def research(self, topic: str, **kwargs: Any) -> "ResearchResult":
        """Perform in-depth research on a topic.

        This method provides a complete research workflow, including:
        - Topic analysis
        - Source discovery
        - Information synthesis
        - Citation management

        Args:
            topic: The topic to research
            **kwargs: Additional research parameters like:
                - depth: "basic" | "detailed" | "comprehensive" (default: "detailed")
                - style: "academic" | "business" | "casual" (default: "business")
                - format: "report" | "summary" | "bullets" (default: "report")
                - max_sources: int (default: 5)

        Returns:
            A ResearchResult containing the findings

        Example:
            >>> result = await pepper.research(
            ...     "Impact of AI in Healthcare",
            ...     depth="comprehensive",
            ...     style="academic"
            ... )
            >>> print(result.tldr)  # Short summary
            >>> print(result.full)  # Full report
            >>> print(result.bullets)  # Key points
            >>> print(result.references)  # Sources

        """
        if not self._initialized or not self._client:
            raise RuntimeError("Pepperpy not initialized. Call create() first.")

        # Set smart defaults
        kwargs.setdefault("depth", "detailed")
        kwargs.setdefault("style", "business")
        kwargs.setdefault("format", "report")
        kwargs.setdefault("max_sources", 5)

        result = await self._client.run(
            "research_assistant", "research", topic=topic, **kwargs
        )
        return ResearchResult(result)

    @property
    def hub(self) -> "PepperpyHub":
        """Access the Pepperpy Hub for agents and workflows.

        The hub provides easy access to:
        - Pre-configured agents
        - Workflow templates
        - Team compositions
        - Shared resources

        Returns:
            A PepperpyHub instance for managing components

        Example:
            >>> researcher = await pepper.hub.agent("researcher")
            >>> team = await pepper.hub.team("research-team")
            >>> flow = await pepper.hub.workflow("research-flow")

        """
        if not self._initialized or not self._client:
            raise RuntimeError("Pepperpy not initialized. Call create() first.")
        from pepperpy.hub import PepperpyHub

        return PepperpyHub(self._client)

    async def __aenter__(self) -> "Pepperpy":
        """Support async context manager for automatic resource cleanup."""
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Clean up resources when exiting context."""
        if self._client:
            await self._client.cleanup()

    def chat(self, initial_message: Optional[str] = None) -> None:
        """Start an interactive chat session.

        This method provides a simple interactive chat interface in the terminal.
        Just type your messages and get responses in real-time.

        Args:
            initial_message: Optional message to start the conversation

        Example:
            >>> pepper.chat()  # Start interactive chat
            >>> pepper.chat("Tell me about AI")  # Start with initial message

            # During chat:
            # - Press Ctrl+C to exit
            # - Type /help for commands
            # - Type /clear to clear history
            # - Type /save to save conversation

        """
        if not self._initialized or not self._client:
            raise RuntimeError("Pepperpy not initialized. Call create() first.")

        try:
            asyncio.run(self._interactive_chat(initial_message))
        except KeyboardInterrupt:
            print("\nChat session ended.")

    async def stream_response(self, message: str) -> AsyncIterator[str]:
        """Stream a response token by token.

        Args:
            message: The message to send

        Yields:
            Response tokens as they are generated

        Example:
            >>> async for token in pepper.stream_response("Tell me about AI"):
            ...     print(token, end="", flush=True)

        """
        if not self._initialized or not self._client:
            raise RuntimeError("Pepperpy not initialized. Call create() first.")

        # Stream response
        async for response in self._client.stream_chat([
            {"role": "user", "content": message}
        ]):
            if isinstance(response.content, dict):
                yield response.content.get("text", "")
            else:
                yield str(response.content)

    async def _interactive_chat(self, initial_message: Optional[str] = None) -> None:
        """Internal method for interactive chat session."""
        print("\nPepperpy Chat (Ctrl+C to exit)")
        print("Commands: /help, /clear, /save")
        print("-" * 50)

        if initial_message:
            print("\nYou:", initial_message)
            print("\nAI:", end=" ", flush=True)
            async for token in self.stream_response(initial_message):
                print(token, end="", flush=True)
            print("\n")

        while True:
            try:
                message = input("\nYou: ").strip()
                if not message:
                    continue

                # Handle commands
                if message.startswith("/"):
                    if message == "/help":
                        print("\nCommands:")
                        print("  /help  - Show this help")
                        print("  /clear - Clear chat history")
                        print("  /save  - Save conversation")
                        continue
                    elif message == "/clear":
                        if self._client:
                            await self._client.clear_history()
                        print("\nChat history cleared.")
                        continue
                    elif message == "/save":
                        # TODO: Implement conversation saving
                        print("\nSaving conversation... (Not implemented yet)")
                        continue

                print("\nAI:", end=" ", flush=True)
                async for token in self.stream_response(message):
                    print(token, end="", flush=True)
                print("\n")

            except (KeyboardInterrupt, EOFError):
                print("\nChat session ended.")
                break
            except Exception as e:
                print(f"\nError: {str(e)}")
                break


class ResearchResult:
    """Container for research results with convenient access methods.

    This class provides intuitive access to research results in various formats:
    - tldr: Quick summary
    - full: Complete report
    - bullets: Key points
    - references: Sources used
    """

    def __init__(self, data: dict):
        self._data = data

    @property
    def tldr(self) -> str:
        """Get a short summary of the research."""
        return self._data.get("summary", "")

    @property
    def full(self) -> str:
        """Get the full research report."""
        return self._data.get("full_report", "")

    @property
    def bullets(self) -> list[str]:
        """Get key points as bullet points."""
        return self._data.get("key_points", [])

    @property
    def references(self) -> list[dict]:
        """Get cited references with metadata."""
        return self._data.get("references", [])


__all__ = [
    "Pepperpy",
    "PepperpyClient",
    "PepperpyConfig",
    "ResearchAssistantAgent",
    "ResearchResult",
    "Response",
    "Message",
    "MessageType",
]
