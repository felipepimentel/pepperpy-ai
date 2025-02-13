"""Pepperpy - A Python library for building AI-powered research assistants.

This module provides a high-level API for creating and managing AI agents
specialized in research tasks, including topic analysis, source discovery,
and information synthesis.
"""

import asyncio
import os
from pathlib import Path
from typing import Any, AsyncIterator, Dict, Optional, Union, cast
from uuid import uuid4

from structlog import get_logger

from pepperpy.core.base import BaseAgent
from pepperpy.core.client import PepperpyClient
from pepperpy.core.config import PepperpyConfig
from pepperpy.core.types import Message, MessageType, Response
from pepperpy.hub import PepperpyHub
from pepperpy.hub.agents import ResearchAssistantAgent
from pepperpy.hub.agents.researcher import ResearcherAgent
from pepperpy.hub.agents.writer import WriterAgent
from pepperpy.hub.protocols import WorkflowProtocol
from pepperpy.hub.teams import Team
from pepperpy.hub.workflows import Workflow, WorkflowConfig

__version__ = "0.1.0"

# Configure logger
logger = get_logger()


class Pepperpy:
    """Main entry point for the Pepperpy library.

    This class provides a simplified interface for using Pepperpy's capabilities.

    Examples:
        Basic usage:
        >>> pepper = await Pepperpy.create()  # Auto-configure from .env
        >>> result = await pepper.ask("What is AI?")
        >>> print(result)

        Research workflow:
        >>> result = await pepper.research("Impact of AI")
        >>> print(result.tldr)  # Quick summary
        >>> print(result.bullets)  # Key points
        >>> print(result.references)  # Sources

        Team collaboration:
        >>> team = await pepper.team("research")
        >>> async with team.run("Research AI") as session:
        ...     print(session.progress)
        ...     print(session.thoughts)

        Interactive chat:
        >>> pepper.chat("Tell me about AI")  # Start interactive chat

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
            **kwargs: Additional parameters like:
                - style: "concise" | "detailed" | "technical" (default: "detailed")
                - format: "text" | "markdown" | "json" (default: "text")
                - temperature: Controls randomness (0.0-1.0)
                - max_tokens: Maximum response length

        Returns:
            The AI's response

        Example:
            >>> result = await pepper.ask("What is AI?")
            >>> print(result)

            # With style options:
            >>> result = await pepper.ask(
            ...     "Explain quantum computing",
            ...     style="technical",
            ...     format="markdown"
            ... )

        """
        if not self._initialized or not self._client:
            raise RuntimeError("Pepperpy not initialized. Call create() first.")

        # Validate input
        if not question or not question.strip():
            raise ValueError("Question cannot be empty")

        # Set smart defaults
        kwargs.setdefault("temperature", 0.7)
        kwargs.setdefault("max_tokens", 2048)

        # Handle style parameter
        style = kwargs.pop("style", None)
        if style:
            if style == "concise":
                kwargs["max_tokens"] = 500
                question = f"Please provide a concise answer: {question}"
            elif style == "detailed":
                kwargs["max_tokens"] = 4096
                question = f"Please provide a detailed answer: {question}"
            elif style == "technical":
                kwargs["max_tokens"] = 4096
                question = f"Please provide a technical explanation: {question}"

        # Handle format parameter
        output_format = kwargs.pop("format", None)
        if output_format:
            if output_format == "markdown":
                question = f"Please format your response in markdown: {question}"
            elif output_format == "json":
                question = f"Please format your response as JSON: {question}"

        try:
            return await self._client.chat(question, **kwargs)
        except Exception as e:
            # Log error with context
            logger.error(
                "Failed to get response",
                error=str(e),
                question=question[:100],
                **kwargs,
            )
            raise

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

    async def chat(self, initial_message: Optional[str] = None) -> None:
        """Start an interactive chat session.

        This method starts a real-time chat session with the AI. If an initial
        message is provided, it will be sent to start the conversation.

        The chat session supports:
        - Real-time streaming responses
        - Special commands (type /help to see all)
        - Style customization
        - Conversation saving

        Args:
            initial_message: Optional message to start the conversation

        Example:
            >>> pepper = await Pepperpy.create()
            >>> await pepper.chat()  # Start blank chat
            >>> # Or with initial message:
            >>> await pepper.chat("Tell me about AI")

        """
        if not self._initialized or not self._client:
            raise RuntimeError("Pepperpy not initialized. Call create() first.")

        from rich.console import Console
        from rich.panel import Panel

        console = Console()

        # Show welcome message
        console.print(
            Panel.fit(
                "[bold blue]Pepperpy Chat[/]\n\n"
                "Type your messages and press Enter. Available commands:\n"
                "  [green]/help[/]   - Show this help\n"
                "  [green]/clear[/]  - Clear chat history\n"
                "  [green]/save[/]   - Save conversation\n"
                "  [green]/style[/]  - Change response style (concise/detailed/technical)\n"
                "  [green]/format[/] - Change output format (text/markdown/json)\n"
                "  [green]Ctrl+C[/]  - Exit chat"
            )
        )

        try:
            # Send initial message if provided
            if initial_message:
                console.print("\n[bold blue]You:[/] " + initial_message)
                console.print("\n[bold green]Assistant:[/] ", end="")
                async for token in self.stream_response(initial_message):
                    console.print(token, end="", flush=True)
                console.print("\n")

            # Start interactive session
            self._interactive = True
            settings = {
                "style": "detailed",
                "format": "text",
                "temperature": 0.7,
            }

            while self._interactive:
                try:
                    # Get user input
                    user_input = console.input("\n[bold blue]You:[/] ").strip()
                    if not user_input:
                        continue

                    # Process special commands
                    if user_input.startswith("/"):
                        parts = user_input.split()
                        command = parts[0]

                        if command == "/help":
                            console.print(
                                Panel.fit(
                                    "[bold]Available Commands[/]\n\n"
                                    "/help   - Show this help\n"
                                    "/clear  - Clear chat history\n"
                                    "/save   - Save conversation\n"
                                    "/style  - Change style (concise/detailed/technical)\n"
                                    "/format - Change format (text/markdown/json)\n"
                                    "Ctrl+C  - Exit chat"
                                )
                            )
                            continue
                        elif command == "/clear":
                            if self._client:
                                await self._client.clear_history()
                            console.print("[green]Chat history cleared.[/]")
                            continue
                        elif command == "/save":
                            # TODO[v2.0]: Implement conversation saving
                            console.print(
                                "[yellow]Saving conversation... (Not implemented yet)[/]"
                            )
                            continue
                        elif command == "/style":
                            if len(parts) < 2:
                                console.print(
                                    "[red]Usage: /style <concise|detailed|technical>[/]"
                                )
                                continue
                            style = parts[1].lower()
                            if style not in ["concise", "detailed", "technical"]:
                                console.print(
                                    "[red]Invalid style. Use: concise, detailed, or technical[/]"
                                )
                                continue
                            settings["style"] = style
                            console.print(f"[green]Style changed to: {style}[/]")
                            continue
                        elif command == "/format":
                            if len(parts) < 2:
                                console.print(
                                    "[red]Usage: /format <text|markdown|json>[/]"
                                )
                                continue
                            fmt = parts[1].lower()
                            if fmt not in ["text", "markdown", "json"]:
                                console.print(
                                    "[red]Invalid format. Use: text, markdown, or json[/]"
                                )
                                continue
                            settings["format"] = fmt
                            console.print(f"[green]Format changed to: {fmt}[/]")
                            continue
                        elif command in ["/exit", "/quit"]:
                            break

                    # Get and print response with streaming
                    console.print("\n[bold green]Assistant:[/] ", end="")
                    async for token in self.stream_response(
                        user_input,
                        style=settings["style"],
                        format=settings["format"],
                        temperature=settings["temperature"],
                    ):
                        console.print(token, end="", flush=True)
                    console.print("\n")

                except KeyboardInterrupt:
                    break
                except Exception as e:
                    console.print(f"\n[red]Error:[/] {str(e)}")
                    logger.error("Chat error", error=str(e))
                    if console.input("\n[yellow]Continue? (y/n):[/] ").lower() != "y":
                        break
                    continue

        finally:
            self._interactive = False
            console.print("\n[yellow]Chat session ended.[/]")

    async def stream_response(
        self,
        message: str,
        *,
        style: Optional[str] = None,
        format: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> AsyncIterator[str]:
        """Stream a response token by token.

        Args:
            message: The message to send
            style: Optional response style ("concise", "detailed", "technical")
            format: Optional output format ("text", "markdown", "json")
            temperature: Optional temperature value (0.0-1.0)
            max_tokens: Optional maximum tokens to generate

        Yields:
            Response tokens as they are generated

        Example:
            >>> async for token in pepper.stream_response(
            ...     "Tell me about AI",
            ...     style="technical",
            ...     format="markdown"
            ... ):
            ...     print(token, end="")

        """
        if not self._initialized or not self._client:
            raise RuntimeError("Pepperpy not initialized. Call create() first.")

        # Apply style and format to message
        if style:
            if style == "concise":
                message = f"Please provide a concise answer: {message}"
            elif style == "detailed":
                message = f"Please provide a detailed answer: {message}"
            elif style == "technical":
                message = f"Please provide a technical explanation: {message}"

        if format:
            if format == "markdown":
                message = f"Please format your response in markdown: {message}"
            elif format == "json":
                message = f"Please format your response as JSON: {message}"

        # Stream response with parameters
        kwargs = {}
        if temperature is not None:
            kwargs["temperature"] = temperature
        if max_tokens is not None:
            kwargs["max_tokens"] = max_tokens

        try:
            async for response in self._client.stream_chat(
                [{"role": "user", "content": message}], **kwargs
            ):
                if isinstance(response.content, dict):
                    yield response.content.get("text", "")
                else:
                    yield str(response.content)
        except Exception as e:
            logger.error(
                "Failed to stream response",
                error=str(e),
                message=message[:100],
                **kwargs,
            )
            raise

    # Intuitive aliases for common operations
    async def explain(self, topic: str, **kwargs: Any) -> str:
        """Get a detailed explanation of a topic.

        This is an alias for ask() with style="detailed".

        Args:
            topic: The topic to explain
            **kwargs: Additional parameters (same as ask)

        Returns:
            Detailed explanation

        Example:
            >>> explanation = await pepper.explain("How does AI work?")
            >>> print(explanation)

        """
        kwargs.setdefault("style", "detailed")
        return await self.ask(f"Explain {topic}", **kwargs)

    async def summarize(self, text: str, **kwargs: Any) -> str:
        """Generate a concise summary of text.

        Args:
            text: The text to summarize
            **kwargs: Additional parameters like:
                - length: "short" | "medium" | "long" (default: "short")
                - style: "bullet" | "paragraph" (default: "paragraph")

        Returns:
            Generated summary

        Example:
            >>> text = "Long article..."
            >>> summary = await pepper.summarize(text, length="short")
            >>> print(summary)

        """
        kwargs.setdefault("style", "concise")
        return await self.ask(f"Summarize this text: {text}", **kwargs)

    async def team(self, name: str) -> "Team":
        """Create or load a team of agents.

        This is a shortcut for pepper.hub.team().

        Args:
            name: Name of the team to load

        Returns:
            The configured team

        Example:
            >>> team = await pepper.team("research")
            >>> result = await team.run("Research AI")

        """
        return await self.hub.team(name)

    async def agent(self, name: str, **kwargs: Any) -> "BaseAgent":
        """Create or load an agent.

        This is a shortcut for pepper.hub.agent().

        Args:
            name: Name of the agent to load
            **kwargs: Additional agent configuration

        Returns:
            The configured agent

        Example:
            >>> researcher = await pepper.agent("researcher")
            >>> result = await researcher.research("AI")

        """
        return await self.hub.agent(name, **kwargs)

    async def workflow(self, name: str) -> "Workflow":
        """Load a workflow.

        This is a shortcut for pepper.hub.workflow().

        Args:
            name: Name of the workflow to load

        Returns:
            The configured workflow

        Example:
            >>> flow = await pepper.workflow("research")
            >>> result = await flow.run("Research AI")

        """
        return await self.hub.workflow(name)

    async def analyze(
        self,
        text: str,
        *,
        focus: str | None = None,
        depth: str = "detailed",
    ) -> dict[str, Any]:
        """Analyze text with optional focus areas."""
        researcher = cast(ResearcherAgent, await self.agent("researcher"))
        return await researcher.analyze(
            text,
            focus=focus,
            depth=depth,
        )

    async def write(
        self,
        topic: str,
        *,
        style: str = "professional",
        format: str = "article",
        tone: str = "neutral",
        length: str = "medium",
        outline: list[str] | None = None,
    ) -> dict[str, Any]:
        """Write content on a given topic.

        This is a shortcut for using the writer agent.

        Args:
            topic: The topic to write about
            style: Writing style ("professional", "casual", "technical")
            format: Content format ("article", "blog", "report")
            tone: Writing tone ("neutral", "positive", "critical")
            length: Content length ("short", "medium", "long")
            outline: Optional content outline

        Returns:
            Generated content including:
            - title: Content title
            - content: Main content
            - summary: Brief summary
            - metadata: Additional information

        Example:
            >>> result = await pepper.write(
            ...     "Future of AI",
            ...     style="technical",
            ...     format="article"
            ... )
            >>> print(result["content"])

        """
        writer = cast(WriterAgent, await self.agent("writer"))
        return await writer.write(
            topic,
            style=style,
            format=format,
            tone=tone,
            length=length,
            outline=outline,
        )

    async def edit(
        self,
        text: str,
        *,
        focus: str | None = None,
        style: str | None = None,
        improve: list[str] | None = None,
    ) -> dict[str, Any]:
        """Edit and improve text.

        This is a shortcut for using the writer agent's edit method.

        Args:
            text: The text to edit
            focus: Optional focus areas
            style: Optional target style
            improve: Aspects to improve (clarity, conciseness, etc.)

        Returns:
            Edited content including:
            - content: Edited content
            - changes: List of changes made
            - suggestions: Additional suggestions

        Example:
            >>> result = await pepper.edit(
            ...     "Draft text...",
            ...     focus="clarity",
            ...     improve=["conciseness", "grammar"]
            ... )
            >>> print(result["content"])

        """
        writer = cast(WriterAgent, await self.agent("writer"))
        return await writer.edit(
            text,
            focus=focus,
            style=style,
            improve=improve or [],
        )

    async def adapt(
        self,
        text: str,
        target_style: str,
        *,
        preserve: list[str] | None = None,
    ) -> str:
        """Adapt text to a different style.

        This is a shortcut for using the writer agent's adapt method.

        Args:
            text: The text to adapt
            target_style: Target writing style
            preserve: Elements to preserve (tone, structure, etc.)

        Returns:
            The adapted text

        Example:
            >>> result = await pepper.adapt(
            ...     "Technical text...",
            ...     target_style="casual",
            ...     preserve=["key_points"]
            ... )
            >>> print(result)

        """
        writer = cast(WriterAgent, await self.agent("writer"))
        return await writer.adapt(
            text,
            target_style,
            preserve=preserve or [],
        )

    async def collaborate(
        self,
        task: str,
        *,
        team_name: str | None = None,
        workflow_name: str | None = None,
        **kwargs: Any,
    ) -> Any:
        """Collaborate with a team of agents on a task.

        This is a high-level method that combines team and workflow capabilities.
        It will either use an existing team/workflow or create an appropriate one
        based on the task.

        Args:
            task: The task to perform
            team_name: Optional name of pre-configured team to use
            workflow_name: Optional name of pre-configured workflow to use
            **kwargs: Additional task parameters

        Returns:
            The collaboration result

        Example:
            >>> result = await pepper.collaborate(
            ...     "Research and write about AI",
            ...     team_name="research-team"
            ... )
            >>> print(result)

            # Or let Pepperpy choose the team:
            >>> result = await pepper.collaborate(
            ...     "Research and write about AI"
            ... )

        """
        if team_name:
            team = await self.team(team_name)
        else:
            # Auto-select appropriate team based on task
            team = await self.hub.team("research-team")  # Default for now

        if workflow_name:
            workflow = cast(WorkflowProtocol, await self.workflow(workflow_name))
            return await workflow.run(task, **kwargs)
        else:
            return await team.run(task, **kwargs)


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
    "WorkflowConfig",
]
