"""Interactive agent module for the Pepperpy framework.

This module provides the interactive agent implementation that can engage in conversations.
It defines the interactive agent class, configuration, and conversation capabilities.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from pepperpy.agents.base import AgentConfig, BaseAgent
from pepperpy.common.errors import AgentError


@dataclass
class Message:
    """Message in a conversation."""

    content: str
    role: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Conversation:
    """Conversation history."""

    messages: List[Message] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class InteractiveAgentConfig(AgentConfig):
    """Interactive agent configuration."""

    conversation_types: List[str] = field(default_factory=list)
    max_history_length: int = 100
    max_message_length: int = 4096
    response_timeout: float = 60.0
    conversation_timeout: float = 3600.0


class InteractiveAgent(BaseAgent):
    """Interactive agent that can engage in conversations.

    This agent type is designed for tasks that require user interaction
    and natural language communication.
    """

    def __init__(
        self,
        config: Optional[InteractiveAgentConfig] = None,
    ) -> None:
        """Initialize interactive agent.

        Args:
            config: Optional interactive agent configuration
        """
        super().__init__(config or InteractiveAgentConfig(name=self.__class__.__name__))
        self._conversations: Dict[str, Conversation] = {}
        self._active_conversation: Optional[str] = None

    @property
    def conversation_types(self) -> List[str]:
        """Get supported conversation types."""
        if isinstance(self.config, InteractiveAgentConfig):
            return self.config.conversation_types
        return []

    @property
    def active_conversation(self) -> Optional[Conversation]:
        """Get active conversation."""
        if self._active_conversation:
            return self._conversations.get(self._active_conversation)
        return None

    async def _initialize(self) -> None:
        """Initialize interactive agent."""
        # Validate conversation types
        if not self.conversation_types:
            raise AgentError("No conversation types configured")

        # Initialize conversation metrics
        for conv_type in self.conversation_types:
            await self._metrics_manager.create_counter(
                name=f"{self.config.name}_conversation_{conv_type}_total",
                description=f"Total number of {conv_type} conversations",
                labels={"status": "success"},
            )
            await self._metrics_manager.create_histogram(
                name=f"{self.config.name}_conversation_{conv_type}_seconds",
                description=f"Duration in seconds for {conv_type} conversations",
                labels={"status": "success"},
                buckets=[1.0, 5.0, 10.0, 30.0, 60.0],
            )
            await self._metrics_manager.create_histogram(
                name=f"{self.config.name}_conversation_{conv_type}_messages",
                description=f"Number of messages in {conv_type} conversations",
                labels={"status": "success"},
                buckets=[2, 5, 10, 20, 50],
            )

    async def start_conversation(
        self,
        conversation_id: str,
        conversation_type: str,
        initial_message: Optional[Union[str, Message]] = None,
    ) -> None:
        """Start a new conversation.

        Args:
            conversation_id: Unique conversation identifier
            conversation_type: Type of conversation
            initial_message: Optional initial message

        Raises:
            AgentError: If conversation cannot be started
        """
        if conversation_type not in self.conversation_types:
            raise AgentError(f"Unsupported conversation type: {conversation_type}")

        if conversation_id in self._conversations:
            raise AgentError(f"Conversation already exists: {conversation_id}")

        # Create conversation
        conversation = Conversation(
            metadata={"type": conversation_type, "start_time": datetime.utcnow()}
        )

        # Add initial message if provided
        if initial_message:
            if isinstance(initial_message, str):
                message = Message(content=initial_message, role="user")
            else:
                message = initial_message
            conversation.messages.append(message)

        # Store conversation
        self._conversations[conversation_id] = conversation
        self._active_conversation = conversation_id

    async def end_conversation(self, conversation_id: str) -> None:
        """End a conversation.

        Args:
            conversation_id: Conversation identifier

        Raises:
            AgentError: If conversation cannot be ended
        """
        conversation = self._conversations.get(conversation_id)
        if not conversation:
            raise AgentError(f"Conversation not found: {conversation_id}")

        # Update conversation metadata
        conversation.metadata["end_time"] = datetime.utcnow()
        conversation.metadata["duration"] = (
            conversation.metadata["end_time"] - conversation.metadata["start_time"]
        ).total_seconds()

        # Update metrics
        conv_type = conversation.metadata["type"]
        await self._metrics_manager.create_counter(
            name=f"{self.config.name}_conversation_{conv_type}_total",
            description=f"Total number of {conv_type} conversations",
            labels={"status": "completed"},
        ).inc()
        await self._metrics_manager.create_histogram(
            name=f"{self.config.name}_conversation_{conv_type}_seconds",
            description=f"Duration in seconds for {conv_type} conversations",
            labels={"status": "completed"},
            buckets=[1.0, 5.0, 10.0, 30.0, 60.0],
        ).observe(conversation.metadata["duration"])
        await self._metrics_manager.create_histogram(
            name=f"{self.config.name}_conversation_{conv_type}_messages",
            description=f"Number of messages in {conv_type} conversations",
            labels={"status": "completed"},
            buckets=[2, 5, 10, 20, 50],
        ).observe(len(conversation.messages))

        # Clear conversation
        if self._active_conversation == conversation_id:
            self._active_conversation = None
        del self._conversations[conversation_id]

    async def _execute(self, message: Union[str, Message], **kwargs: Any) -> Message:
        """Process a message in the active conversation.

        Args:
            message: Message to process
            **kwargs: Processing parameters

        Returns:
            Response message

        Raises:
            AgentError: If message processing fails
        """
        if not self.active_conversation:
            raise AgentError("No active conversation")

        # Convert string to Message
        if isinstance(message, str):
            message = Message(content=message, role="user")

        # Validate message length
        if isinstance(self.config, InteractiveAgentConfig):
            if len(message.content) > self.config.max_message_length:
                raise AgentError("Message exceeds maximum length")

        # Add message to conversation
        self.active_conversation.messages.append(message)

        try:
            # Generate response based on conversation type
            conv_type = self.active_conversation.metadata["type"]
            if conv_type == "general":
                response = await self._handle_general_conversation(message)
            elif conv_type == "task":
                response = await self._handle_task_conversation(message)
            elif conv_type == "code":
                response = await self._handle_code_conversation(message)
            else:
                raise AgentError(f"Conversation type not implemented: {conv_type}")

            # Add response to conversation
            self.active_conversation.messages.append(response)
            return response

        except Exception as e:
            raise AgentError(f"Failed to process message: {e}") from e

    async def _handle_general_conversation(self, message: Message) -> Message:
        """Handle general conversation.

        Args:
            message: User message

        Returns:
            Response message
        """
        # TODO: Implement general conversation handling
        return Message(
            content="I understand your message.",
            role="assistant",
        )

    async def _handle_task_conversation(self, message: Message) -> Message:
        """Handle task-oriented conversation.

        Args:
            message: User message

        Returns:
            Response message
        """
        # TODO: Implement task conversation handling
        return Message(
            content="I'll help you with that task.",
            role="assistant",
        )

    async def _handle_code_conversation(self, message: Message) -> Message:
        """Handle code-related conversation.

        Args:
            message: User message

        Returns:
            Response message
        """
        # TODO: Implement code conversation handling
        return Message(
            content="Let me help you with the code.",
            role="assistant",
        )

    async def _cleanup(self) -> None:
        """Clean up interactive agent."""
        # End all active conversations
        for conversation_id in list(self._conversations.keys()):
            try:
                await self.end_conversation(conversation_id)
            except Exception:
                pass
