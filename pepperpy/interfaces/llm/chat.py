"""Public interface for chat functionality.

This module provides a stable public interface for chat functionality
with language models. It exposes the core chat abstractions and implementations
that are considered part of the public API.

Classes:
    ChatSession: Manages a conversation session with an LLM
    ChatMessage: Represents a message in a chat conversation
    ChatResponse: Represents a response from an LLM in a chat conversation
    ChatOptions: Configuration options for chat sessions
"""

from typing import Any, AsyncGenerator, List, Optional

from pepperpy.llm.base import LLMMessage, LLMResponse


class ChatMessage:
    """Represents a message in a chat conversation.

    This is a convenience wrapper around LLMMessage with additional
    functionality specific to chat interactions.

    Attributes:
        role: The role of the message sender (system, user, assistant)
        content: The content of the message
        name: Optional name for the message sender
    """

    def __init__(self, role: str, content: str, name: Optional[str] = None):
        """Initialize a chat message.

        Args:
            role: The role of the message sender
            content: The content of the message
            name: Optional name for the message sender
        """
        self.role = role
        self.content = content
        self.name = name

    def to_llm_message(self) -> LLMMessage:
        """Convert to an LLMMessage.

        Returns:
            An LLMMessage representation of this chat message
        """
        return LLMMessage(role=self.role, content=self.content, name=self.name)

    @classmethod
    def from_llm_message(cls, message: LLMMessage) -> "ChatMessage":
        """Create a ChatMessage from an LLMMessage.

        Args:
            message: The LLMMessage to convert

        Returns:
            A ChatMessage representation of the LLMMessage
        """
        return cls(role=message.role, content=message.content, name=message.name)

    @classmethod
    def system(cls, content: str) -> "ChatMessage":
        """Create a system message.

        Args:
            content: The content of the message

        Returns:
            A ChatMessage with the system role
        """
        return cls(role="system", content=content)

    @classmethod
    def user(cls, content: str) -> "ChatMessage":
        """Create a user message.

        Args:
            content: The content of the message

        Returns:
            A ChatMessage with the user role
        """
        return cls(role="user", content=content)

    @classmethod
    def assistant(cls, content: str) -> "ChatMessage":
        """Create an assistant message.

        Args:
            content: The content of the message

        Returns:
            A ChatMessage with the assistant role
        """
        return cls(role="assistant", content=content)


class ChatOptions:
    """Configuration options for chat sessions.

    Attributes:
        model: The model to use for the chat session
        temperature: Controls randomness in the response
        max_tokens: Maximum number of tokens to generate
        stream: Whether to stream the response
    """

    def __init__(
        self,
        model: str,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        stream: bool = False,
        **kwargs: Any,
    ):
        """Initialize chat options.

        Args:
            model: The model to use for the chat session
            temperature: Controls randomness in the response
            max_tokens: Maximum number of tokens to generate
            stream: Whether to stream the response
            **kwargs: Additional provider-specific options
        """
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.stream = stream
        self.additional_options = kwargs


class ChatSession:
    """Manages a conversation session with an LLM.

    This class provides a high-level interface for chat interactions
    with language models, maintaining conversation history and handling
    message formatting.

    Attributes:
        messages: The conversation history
        options: Configuration options for the chat session
    """

    def __init__(self, options: Optional[ChatOptions] = None):
        """Initialize a chat session.

        Args:
            options: Configuration options for the chat session
        """
        self.messages: List[ChatMessage] = []
        self.options = options or ChatOptions(model="default")

    def add_message(self, message: ChatMessage) -> None:
        """Add a message to the conversation history.

        Args:
            message: The message to add
        """
        self.messages.append(message)

    def add_system_message(self, content: str) -> None:
        """Add a system message to the conversation history.

        Args:
            content: The content of the message
        """
        self.add_message(ChatMessage.system(content))

    def add_user_message(self, content: str) -> None:
        """Add a user message to the conversation history.

        Args:
            content: The content of the message
        """
        self.add_message(ChatMessage.user(content))

    def add_assistant_message(self, content: str) -> None:
        """Add an assistant message to the conversation history.

        Args:
            content: The content of the message
        """
        self.add_message(ChatMessage.assistant(content))

    def clear_history(self) -> None:
        """Clear the conversation history."""
        self.messages = []

    async def generate_response(self, provider: Any) -> LLMResponse:
        """Generate a response from the language model.

        Args:
            provider: The LLM provider to use

        Returns:
            The generated response

        Raises:
            ValueError: If no messages are in the conversation history
        """
        if not self.messages:
            raise ValueError("No messages in conversation history")

        llm_messages = [msg.to_llm_message() for msg in self.messages]

        # Convert options to kwargs for the provider
        kwargs = {
            "temperature": self.options.temperature,
            **self.options.additional_options,
        }

        if self.options.max_tokens:
            kwargs["max_tokens"] = self.options.max_tokens

        response = await provider.generate(llm_messages, **kwargs)

        # Add the response to the conversation history
        self.add_assistant_message(response.content)

        return response

    async def generate_stream(self, provider: Any) -> AsyncGenerator[LLMResponse, None]:
        """Generate a streaming response from the language model.

        Args:
            provider: The LLM provider to use

        Returns:
            An async generator of response chunks

        Raises:
            ValueError: If no messages are in the conversation history
        """
        if not self.messages:
            raise ValueError("No messages in conversation history")

        llm_messages = [msg.to_llm_message() for msg in self.messages]

        # Convert options to kwargs for the provider
        kwargs = {
            "temperature": self.options.temperature,
            "stream": True,
            **self.options.additional_options,
        }

        if self.options.max_tokens:
            kwargs["max_tokens"] = self.options.max_tokens

        # Collect the full response content
        full_content = ""

        async for chunk in provider.process_message(llm_messages[-1], **kwargs):
            full_content += chunk.content
            yield chunk

        # Add the complete response to the conversation history
        self.add_assistant_message(full_content)


# Export public classes
__all__ = [
    "ChatMessage",
    "ChatOptions",
    "ChatSession",
]
