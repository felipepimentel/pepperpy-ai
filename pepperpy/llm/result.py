"""
PepperPy LLM Results.

Result classes for language model operations.
"""

from datetime import datetime
from typing import Any

from pepperpy.core.results import TextResult


class LLMResult(TextResult):
    """Result of a language model operation."""

    def __init__(
        self,
        content: str,
        model: str,
        prompt: str,
        usage: dict[str, int],
        metadata: dict[str, Any] | None = None,
    ):
        """Initialize LLM result.

        Args:
            content: Generated content
            model: Model used
            prompt: Prompt used
            usage: Token usage information
            metadata: Additional metadata
        """
        super().__init__(content=content, metadata=metadata or {})
        self.model = model
        self.prompt = prompt
        self.usage = usage
        self.created_at = datetime.now()

        # Add to metadata
        self.metadata["model"] = model
        self.metadata["usage"] = usage
        self.metadata["created_at"] = self.created_at

    @property
    def total_tokens(self) -> int:
        """Get total tokens used.

        Returns:
            Total token count
        """
        return self.usage.get("total_tokens", 0)

    @property
    def prompt_tokens(self) -> int:
        """Get prompt tokens used.

        Returns:
            Prompt token count
        """
        return self.usage.get("prompt_tokens", 0)

    @property
    def completion_tokens(self) -> int:
        """Get completion tokens used.

        Returns:
            Completion token count
        """
        return self.usage.get("completion_tokens", 0)


class ChatResult(LLMResult):
    """Result of a chat completion."""

    def __init__(
        self,
        content: str,
        model: str,
        messages: list[dict[str, str]],
        usage: dict[str, int],
        metadata: dict[str, Any] | None = None,
    ):
        """Initialize chat result.

        Args:
            content: Generated content
            model: Model used
            messages: Chat messages
            usage: Token usage information
            metadata: Additional metadata
        """
        # Reconstruct prompt from messages
        prompt = "\n".join([f"{msg['role']}: {msg['content']}" for msg in messages])

        super().__init__(
            content=content,
            model=model,
            prompt=prompt,
            usage=usage,
            metadata=metadata or {},
        )

        self.messages = messages
        self.metadata["messages"] = messages


class CompletionResult(LLMResult):
    """Result of a text completion."""

    def __init__(
        self,
        content: str,
        model: str,
        prompt: str,
        usage: dict[str, int],
        parameters: dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None,
    ):
        """Initialize completion result.

        Args:
            content: Generated content
            model: Model used
            prompt: Prompt used
            usage: Token usage information
            parameters: Generation parameters used
            metadata: Additional metadata
        """
        super().__init__(
            content=content,
            model=model,
            prompt=prompt,
            usage=usage,
            metadata=metadata or {},
        )

        self.parameters = parameters or {}
        self.metadata["parameters"] = self.parameters


class StreamResult(TextResult):
    """Result of a streaming LLM operation."""

    def __init__(
        self,
        content: str,
        model: str,
        chunks: list[str],
        usage: dict[str, int] | None = None,
        metadata: dict[str, Any] | None = None,
    ):
        """Initialize a stream result.

        Args:
            content: Complete generated text
            model: Name of the model used
            chunks: List of text chunks received
            usage: Token usage information (optional)
            metadata: Additional metadata
        """
        metadata = metadata or {}
        metadata["model"] = model
        metadata["chunk_count"] = len(chunks)
        if usage:
            metadata["usage"] = usage

        super().__init__(content=content, metadata=metadata)
        self.model = model
        self.chunks = chunks
        self.usage = usage or {}

    @property
    def chunk_count(self) -> int:
        """Get number of chunks.

        Returns:
            Number of chunks
        """
        return len(self.chunks)
