"""
PepperPy LLM Providers.

Provider interfaces and base classes for language model operations.
"""

import abc
import argparse
import asyncio
import enum
from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Any

from rich.console import Console
from rich.panel import Panel

from pepperpy.core.errors import PepperpyError
from pepperpy.plugin.provider import BasePluginProvider
from pepperpy.workflow.base import WorkflowComponent


class MessageRole(str, enum.Enum):
    """Role of a message in a conversation."""

    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    FUNCTION = "function"


@dataclass
class Message:
    """A message in a conversation.

    Attributes:
        role: Role of the message sender
        content: Message content
        name: Optional name of the sender
        function_call: Optional function call details
    """

    role: MessageRole
    content: str
    name: str | None = None
    function_call: dict[str, Any] | None = None


@dataclass
class GenerationResult:
    """Result of a text generation request.

    Attributes:
        content: Generated text content
        messages: Full conversation history
        usage: Token usage statistics
        metadata: Additional provider-specific metadata
    """

    content: str
    messages: list[Message]
    usage: dict[str, int] | None = None
    metadata: dict[str, Any] | None = None


@dataclass
class GenerationChunk:
    """A chunk of generated text from a streaming response.

    Attributes:
        content: Generated text content
        finish_reason: Reason for finishing (if any)
        metadata: Additional provider-specific metadata
    """

    content: str
    finish_reason: str | None = None
    metadata: dict[str, Any] | None = None


class LLMError(PepperpyError):
    """Base error for the LLM module."""

    pass


class LLMConfigError(LLMError):
    """Error related to configuration of LLM providers."""

    def __init__(
        self, message: str, provider: str | None = None, cause: Exception | None = None
    ) -> None:
        """Initialize a new LLM configuration error.

        Args:
            message: Error message.
            provider: The LLM provider name.
            cause: Optional original exception
        """
        self.provider = provider
        super().__init__(message, cause=cause)

    def __str__(self) -> str:
        """Return the string representation of the error."""
        if self.provider:
            return f"Configuration error for provider '{self.provider}': {self.message}"
        return f"Configuration error: {self.message}"


class LLMProcessError(LLMError):
    """Error related to the LLM process."""

    def __init__(
        self, message: str, prompt: str | None = None, cause: Exception | None = None
    ) -> None:
        """Initialize a new LLM process error.

        Args:
            message: Error message.
            prompt: The prompt that failed to be processed.
            cause: Optional original exception
        """
        self.prompt = prompt
        super().__init__(message, cause=cause)

    def __str__(self) -> str:
        """Return the string representation of the error."""
        if self.prompt:
            # Truncate prompt if too long
            prompt = self.prompt[:50] + "..." if len(self.prompt) > 50 else self.prompt
            return f"LLM process error for prompt '{prompt}': {self.message}"
        return f"LLM process error: {self.message}"


class LLMProvider(BasePluginProvider, abc.ABC):
    """Base class for LLM providers.

    This class defines the interface that all LLM providers must implement.
    It includes methods for text generation, streaming, and embeddings.
    """

    name: str = "base"

    def __init__(
        self,
        name: str = "base",
        config: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize LLM provider.

        Args:
            name: Provider name
            config: Optional configuration dictionary
            **kwargs: Additional provider-specific configuration
        """
        super().__init__(**(config or {}), **kwargs)
        self.name = name
        self.last_used = None

    @property
    def api_key(self) -> str | None:
        """Get the API key for the provider.

        Returns:
            The API key if set, None otherwise.
        """
        return self.get_config("api_key")

    @abc.abstractmethod
    async def generate(
        self,
        messages: str | list[Message],
        **kwargs: Any,
    ) -> GenerationResult:
        """Generate text based on input messages.

        Args:
            messages: String prompt or list of messages
            **kwargs: Additional generation options

        Returns:
            GenerationResult containing the response

        Raises:
            LLMError: If generation fails
        """
        raise NotImplementedError("generate must be implemented by provider")

    @abc.abstractmethod
    async def stream(
        self,
        messages: str | list[Message],
        **kwargs: Any,
    ) -> AsyncIterator[GenerationChunk]:
        """Generate text in a streaming fashion.

        Args:
            messages: String prompt or list of messages
            **kwargs: Additional generation options

        Returns:
            AsyncIterator yielding GenerationChunk objects

        Raises:
            LLMError: If generation fails
        """
        raise NotImplementedError("stream must be implemented by provider")

    async def get_embeddings(
        self,
        texts: str | list[str],
        **kwargs: Any,
    ) -> list[list[float]]:
        """Generate embeddings for input texts.

        Args:
            texts: String or list of strings to embed
            **kwargs: Additional embedding options

        Returns:
            List of embedding vectors

        Raises:
            LLMError: If embedding generation fails
        """
        raise NotImplementedError("get_embeddings must be implemented by provider")

    def get_capabilities(self) -> dict[str, Any]:
        """Get provider capabilities.

        Returns:
            Dictionary of provider capabilities
        """
        return {
            "streaming": True,
            "embeddings": True,
            "function_calling": True,
            "max_tokens": 4096,
            "max_messages": 100,
        }

    async def initialize(self) -> None:
        """Initialize the provider."""
        pass

    async def cleanup(self) -> None:
        """Clean up provider resources."""
        pass

    async def summarize(
        self,
        text: str,
        max_length: int | None = None,
        **kwargs: Any,
    ) -> str:
        """Summarize text.

        Args:
            text: Text to summarize
            max_length: Maximum length of summary
            **kwargs: Additional generation options

        Returns:
            Generated summary

        Raises:
            LLMError: If generation fails
        """
        prompt = "Summarize the following text"
        if max_length:
            prompt += f" in {max_length} words or less"
        prompt += f":\n\n{text}"

        result = await self.generate(prompt, **kwargs)
        return result.content

    async def classify(
        self,
        text: str,
        categories: list[str],
        **kwargs: Any,
    ) -> str:
        """Classify text into categories.

        Args:
            text: Text to classify
            categories: List of categories
            **kwargs: Additional generation options

        Returns:
            Selected category

        Raises:
            LLMError: If generation fails
        """
        categories_str = ", ".join(categories)
        prompt = f"Classify the following text into one of these categories: {categories_str}\n\nText: {text}\n\nCategory:"

        result = await self.generate(prompt, **kwargs)
        return result.content.strip()

    # Async methods for chat completion

    async def get_chat_completion(
        self,
        messages: list[dict[str, str]],
        model: str | None = None,
        temperature: float = 0.7,
        top_p: float = 0.95,
        stream: bool = False,
        stop: list[str] | None = None,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Get a chat completion for a list of messages.

        This is the core method for interacting with the language model in a chat context.
        It takes a list of messages and returns a completion.

        Args:
            messages: List of message dictionaries with role and content
            model: Language model to use (overrides provider default)
            temperature: Sampling temperature (0-1)
            top_p: Nucleus sampling parameter (0-1)
            stream: Whether to stream the response
            stop: Optional list of stop sequences
            max_tokens: Maximum number of tokens to generate
            **kwargs: Additional provider-specific parameters

        Returns:
            Dictionary containing the response and other metadata
        """
        # Convert dictionaries to Message objects
        msg_objects = []
        for msg in messages:
            # Handle function_call safely
            function_call_dict = None
            if "function_call" in msg and msg["function_call"] is not None:
                if isinstance(msg["function_call"], dict):
                    function_call_dict = msg["function_call"]
                else:
                    # If it's not a dict, convert or ignore it
                    try:
                        function_call_dict = {"name": str(msg["function_call"])}
                    except:
                        pass

            msg_obj = Message(
                role=MessageRole(msg["role"]),
                content=msg["content"],
                name=msg.get("name"),
                function_call=function_call_dict,
            )
            msg_objects.append(msg_obj)

        # Generate response
        result = await self.generate(msg_objects, **kwargs)

        # Format response in OpenAI-like format
        return {
            "choices": [
                {
                    "message": {"role": "assistant", "content": result.content},
                    "finish_reason": "stop",
                }
            ],
            "usage": result.usage or {},
            "model": model or "default",
        }

    async def stream_chat_completion(
        self,
        messages: list[dict[str, str]],
        model: str | None = None,
        temperature: float = 0.7,
        top_p: float = 0.95,
        stop: list[str] | None = None,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> AsyncIterator[dict[str, Any]]:
        """Stream a chat completion for a list of messages.

        This method streams the response token by token instead of waiting for
        the complete response.

        Args:
            messages: List of message dictionaries with role and content
            model: Language model to use (overrides provider default)
            temperature: Sampling temperature (0-1)
            top_p: Nucleus sampling parameter (0-1)
            stop: Optional list of stop sequences
            max_tokens: Maximum number of tokens to generate
            **kwargs: Additional provider-specific parameters

        Yields:
            Dictionaries containing partial responses and other metadata
        """
        # Default implementation is to call get_chat_completion and yield once
        response = await self.get_chat_completion(
            messages=messages,
            model=model,
            temperature=temperature,
            top_p=top_p,
            stream=False,
            stop=stop,
            max_tokens=max_tokens,
            **kwargs,
        )
        yield response

    # Simple helper methods (these have default implementations)

    async def chat(
        self,
        prompt: str,
        system_prompt: str | None = None,
        model: str | None = None,
        temperature: float = 0.7,
        **kwargs: Any,
    ) -> str:
        """Simple chat method for single-turn interaction.

        This is a convenience method that wraps get_chat_completion for simple use cases.

        Args:
            prompt: User's prompt/question
            system_prompt: Optional system prompt
            model: Language model to use (overrides provider default)
            temperature: Sampling temperature (0-1)
            **kwargs: Additional provider-specific parameters

        Returns:
            Model's response as a string
        """
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})

        messages.append({"role": "user", "content": prompt})

        response = await self.get_chat_completion(
            messages=messages,
            model=model,
            temperature=temperature,
            **kwargs,
        )

        return response["choices"][0]["message"]["content"]

    # Analysis methods

    async def estimate_tokens(self, text: str) -> int:
        """Estimate the number of tokens in a text.

        Args:
            text: Text to analyze

        Returns:
            Estimated token count
        """
        # Naive implementation that can be overridden by providers
        # with more accurate token counting
        return len(text.split()) + len(text) // 4

    # Metadata methods

    async def get_available_models(self) -> list[str]:
        """Get a list of available models from the provider.

        Returns:
            List of model identifiers
        """
        raise NotImplementedError("Not implemented for this provider")

    # CLI Interface

    @classmethod
    def add_cli_args(cls, parser: argparse.ArgumentParser) -> None:
        """Add provider-specific command line arguments.

        Args:
            parser: ArgumentParser to add arguments to
        """
        parser.add_argument(
            "--model",
            type=str,
            help="Model to use",
        )
        parser.add_argument(
            "--temperature",
            type=float,
            default=0.7,
            help="Temperature (0-1)",
        )
        parser.add_argument(
            "--system",
            type=str,
            help="System prompt",
        )

    @classmethod
    def add_cli_commands(cls, subparsers) -> None:
        """Add provider-specific CLI commands.

        Args:
            subparsers: Subparsers object from argparse
        """
        chat_parser = subparsers.add_parser("chat", help="Chat with the model")
        cls.add_cli_args(chat_parser)
        chat_parser.add_argument("prompt", nargs="?", help="Initial prompt")
        chat_parser.set_defaults(func=lambda args: cls.cli_chat(args))

        complete_parser = subparsers.add_parser(
            "complete", help="Get completion for a prompt"
        )
        cls.add_cli_args(complete_parser)
        complete_parser.add_argument("prompt", help="Prompt to complete")
        complete_parser.set_defaults(func=lambda args: cls.cli_complete(args))

    @staticmethod
    async def _run_chat_session(
        provider: "LLMProvider", args: argparse.Namespace
    ) -> None:
        """Run an interactive chat session.

        Args:
            provider: Provider instance
            args: Command line arguments
        """
        console = Console()
        messages = []

        # Add system message if provided
        if args.system:
            messages.append({"role": "system", "content": args.system})
            console.print(Panel(args.system, title="System", border_style="cyan"))

        # Add initial prompt if provided
        if args.prompt:
            messages.append({"role": "user", "content": args.prompt})
            console.print(Panel(args.prompt, title="You", border_style="green"))

            # Get response
            response = await provider.get_chat_completion(
                messages=messages,
                model=args.model,
                temperature=args.temperature,
            )
            assistant_message = response["choices"][0]["message"]
            messages.append(assistant_message)
            console.print(
                Panel(
                    assistant_message["content"], title="Assistant", border_style="blue"
                )
            )

        # Interactive loop
        while True:
            try:
                # Get user input
                user_input = console.input("[bold green]You:[/] ")
                if user_input.lower() in ("exit", "quit", "q"):
                    break

                # Add user message
                messages.append({"role": "user", "content": user_input})

                # Get response (streaming if available)
                try:
                    console.print("[bold blue]Assistant:[/] ", end="")
                    full_content = ""

                    async for chunk in provider.stream_chat_completion(
                        messages=messages,
                        model=args.model,
                        temperature=args.temperature,
                    ):
                        delta = (
                            chunk.get("choices", [{}])[0]
                            .get("delta", {})
                            .get("content", "")
                        )
                        if delta:
                            console.print(delta, end="")
                            full_content += delta

                    console.print()  # Newline after streaming

                    # Add assistant message to history
                    messages.append({"role": "assistant", "content": full_content})

                except NotImplementedError:
                    # Fallback to non-streaming
                    response = await provider.get_chat_completion(
                        messages=messages,
                        model=args.model,
                        temperature=args.temperature,
                    )
                    assistant_message = response["choices"][0]["message"]
                    messages.append(assistant_message)
                    console.print(
                        Panel(
                            assistant_message["content"],
                            title="Assistant",
                            border_style="blue",
                        )
                    )

            except KeyboardInterrupt:
                console.print("\nExiting chat...")
                break
            except Exception as e:
                console.print(f"[bold red]Error:[/] {e}")

    @classmethod
    def cli_chat(cls, args: argparse.Namespace) -> None:
        """CLI command to start a chat session.

        Args:
            args: Command line arguments
        """

        async def run():
            # Initialize provider
            provider = cls()
            await provider.initialize()
            try:
                await cls._run_chat_session(provider, args)
            finally:
                await provider.cleanup()

        asyncio.run(run())

    @classmethod
    def cli_complete(cls, args: argparse.Namespace) -> None:
        """CLI command to complete a prompt.

        Args:
            args: Command line arguments
        """

        async def run():
            # Initialize provider
            provider = cls()
            await provider.initialize()
            try:
                console = Console()
                response = await provider.chat(
                    prompt=args.prompt,
                    system_prompt=args.system,
                    model=args.model,
                    temperature=args.temperature,
                )
                console.print(response)
            finally:
                await provider.cleanup()

        asyncio.run(run())


class LLMComponent(WorkflowComponent):
    """Component for using LLM in workflows."""

    def __init__(
        self,
        component_id: str,
        name: str,
        component_type: str,
        provider: LLMProvider,
        config: dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Initialize LLM component.

        Args:
            component_id: Component identifier
            name: Component name
            component_type: Component type (always "llm" for this component)
            provider: LLM provider instance
            config: Optional component configuration
            metadata: Optional component metadata
        """
        super().__init__(
            component_id, name, component_type, config or {}, metadata or {}
        )
        self.provider = provider

    async def process(self, data: str | list[Message]) -> GenerationResult:
        """Process input with LLM.

        Args:
            data: Input text or messages

        Returns:
            Generation result

        Raises:
            LLMError: If processing fails
        """
        try:
            # Use the provider to generate text
            return await self.provider.generate(data, **self.config)
        except Exception as e:
            if isinstance(e, LLMError):
                raise
            raise LLMProcessError(
                f"Error during LLM processing: {e!s}",
                prompt=str(data) if isinstance(data, str) else None,
                cause=e,
            )

    async def cleanup(self) -> None:
        """Clean up component resources."""
        await self.provider.cleanup()
