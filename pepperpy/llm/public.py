"""
Public Interface for LLM (Language Model) providers

This module provides a stable public interface for the LLM functionality.
It exposes the core LLM abstractions and implementations that are
considered part of the public API.

Core Components:
    LLMProvider: Base class for all LLM providers
    LLMMessage: Standard message format for LLM interactions
    LLMResponse: Standard response format from LLM providers
    ChatSession: Manages a conversation session with an LLM
    ChatMessage: Represents a message in a chat conversation
    ChatOptions: Configuration options for chat sessions
    ModelInfo: Information about an LLM model
    ModelCapability: Enumeration of model capabilities
    ModelRegistry: Registry of available models
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Any, Dict, List, Optional


class ModelCapability(Enum):
    """Capabilities supported by LLM models."""

    TEXT_GENERATION = auto()
    CHAT = auto()
    CODE_GENERATION = auto()
    EMBEDDINGS = auto()
    IMAGE_GENERATION = auto()
    AUDIO_TRANSCRIPTION = auto()
    FUNCTION_CALLING = auto()
    TOOL_USE = auto()
    VISION = auto()


@dataclass
class ModelInfo:
    """Information about an LLM model.

    Attributes:
        id: Unique identifier for the model
        name: Human-readable name for the model
        provider: Provider of the model
        capabilities: Capabilities supported by the model
        context_window: Maximum context window size in tokens
        max_tokens: Maximum number of tokens in a response
        token_limit: Maximum number of tokens in a request
    """

    id: str
    name: str
    provider: str
    capabilities: List[ModelCapability] = field(default_factory=list)
    context_window: Optional[int] = None
    max_tokens: Optional[int] = None
    token_limit: Optional[int] = None


class ModelRegistry:
    """Registry of available models.

    This class provides functionality for registering, retrieving,
    and managing models.
    """

    def __init__(self):
        """Initialize a model registry."""
        self.models: Dict[str, ModelInfo] = {}

    def register(self, model: ModelInfo) -> None:
        """Register a model.

        Args:
            model: Model to register
        """
        self.models[model.id] = model

    def get(self, model_id: str) -> Optional[ModelInfo]:
        """Get a model by ID.

        Args:
            model_id: Model ID

        Returns:
            Model info or None if not found
        """
        return self.models.get(model_id)

    def list_models(self) -> List[ModelInfo]:
        """List all registered models.

        Returns:
            List of registered models
        """
        return list(self.models.values())


@dataclass
class LLMMessage:
    """Standard message format for LLM interactions.

    Attributes:
        role: Role of the message sender (system, user, assistant)
        content: Content of the message
        name: Optional name of the sender
        function_call: Optional function call information
    """

    role: str
    content: str
    name: Optional[str] = None
    function_call: Optional[Dict[str, Any]] = None


@dataclass
class LLMResponse:
    """Standard response format from LLM providers.

    Attributes:
        content: Content of the response
        model: Model that generated the response
        usage: Token usage information
        finish_reason: Reason the generation finished
        created_at: Timestamp when the response was created
    """

    content: str
    model: str
    usage: Dict[str, int] = field(default_factory=dict)
    finish_reason: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)


class LLMProvider:
    """Base class for all LLM providers.

    This class defines the interface for LLM providers used in the system.
    Subclasses should implement the generate and chat methods to provide
    specific provider functionality.
    """

    def __init__(self, name: str):
        """Initialize the LLM provider.

        Args:
            name: Provider name
        """
        self.name = name

    async def generate(self, prompt: str, **kwargs) -> LLMResponse:
        """Generate text from a prompt.

        Args:
            prompt: The prompt to generate from
            **kwargs: Additional provider-specific parameters

        Returns:
            Generated response

        Raises:
            NotImplementedError: If the subclass does not implement this method
        """
        raise NotImplementedError("Subclasses must implement generate method")

    async def chat(self, messages: List[LLMMessage], **kwargs) -> LLMResponse:
        """Generate a response from a chat history.

        Args:
            messages: The chat history
            **kwargs: Additional provider-specific parameters

        Returns:
            Generated response

        Raises:
            NotImplementedError: If the subclass does not implement this method
        """
        raise NotImplementedError("Subclasses must implement chat method")


@dataclass
class ChatMessage:
    """Represents a message in a chat conversation.

    Attributes:
        role: Role of the message sender (system, user, assistant)
        content: Content of the message
        timestamp: Timestamp when the message was created
        metadata: Additional metadata about the message
    """

    role: str
    content: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ChatOptions:
    """Configuration options for chat sessions.

    Attributes:
        model: Model to use for the chat
        temperature: Temperature for generation
        max_tokens: Maximum number of tokens to generate
        stop_sequences: Sequences that stop generation
        presence_penalty: Presence penalty for generation
        frequency_penalty: Frequency penalty for generation
    """

    model: str
    temperature: float = 0.7
    max_tokens: Optional[int] = None
    stop_sequences: List[str] = field(default_factory=list)
    presence_penalty: float = 0.0
    frequency_penalty: float = 0.0


class ChatSession:
    """Manages a conversation session with an LLM.

    This class provides functionality for managing a conversation with an LLM,
    including message history, context management, and response generation.
    """

    def __init__(self, provider: LLMProvider, options: ChatOptions):
        """Initialize a chat session.

        Args:
            provider: LLM provider to use
            options: Chat options
        """
        self.provider = provider
        self.options = options
        self.messages: List[ChatMessage] = []

    def add_message(self, message: ChatMessage) -> None:
        """Add a message to the chat history.

        Args:
            message: Message to add
        """
        self.messages.append(message)

    async def generate_response(self) -> ChatMessage:
        """Generate a response from the LLM.

        Returns:
            Generated response message
        """
        # Convert ChatMessage to LLMMessage
        llm_messages = [
            LLMMessage(role=msg.role, content=msg.content) for msg in self.messages
        ]

        # Generate response
        response = await self.provider.chat(llm_messages, **self.options.__dict__)

        # Create response message
        message = ChatMessage(
            role="assistant",
            content=response.content,
            metadata={"model": response.model, "usage": response.usage},
        )

        # Add to history
        self.add_message(message)

        return message


# Export public classes
__all__ = [
    "LLMMessage",
    "LLMProvider",
    "LLMResponse",
    "ChatMessage",
    "ChatOptions",
    "ChatSession",
    "ModelCapability",
    "ModelInfo",
    "ModelRegistry",
]
