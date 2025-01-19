"""Tests for conversation functionality."""

from uuid import UUID

import pytest

from pepperpy.memory.conversation import Conversation, Message, MessageRole


@pytest.fixture
def conversation() -> Conversation:
    """Create test conversation."""
    return Conversation(max_messages=5)


def test_add_message(conversation: Conversation) -> None:
    """Test message addition."""
    message = conversation.add_message(
        content="Test message",
        role=MessageRole.USER,
        metadata={"test": True}
    )

    assert isinstance(message, Message)
    assert message.content == "Test message"
    assert message.role == MessageRole.USER
    assert message.metadata["test"] is True
    assert isinstance(message.message_id, UUID)


def test_message_limit(conversation: Conversation) -> None:
    """Test message limit enforcement."""
    # Add 6 messages
    for i in range(6):
        conversation.add_message(
            content=f"Message {i+1}",
            role=MessageRole.USER
        )

    # Should only keep the last 5 messages
    assert len(conversation.messages) == 5
    assert conversation.messages[0].content == "Message 2"
    assert conversation.messages[-1].content == "Message 6"


def test_context_window(conversation: Conversation) -> None:
    """Test context window retrieval."""
    conversation.add_message(
        content="Message 1",
        role=MessageRole.USER,
        metadata={"test": True}
    )

    # Get context with metadata
    context = conversation.get_context_window(include_metadata=True)
    assert len(context) == 1
    assert context[0]["content"] == "Message 1"
    assert context[0]["metadata"]["test"] is True

    # Get context without metadata
    context = conversation.get_context_window(include_metadata=False)
    assert len(context) == 1
    assert context[0]["content"] == "Message 1"
    assert "metadata" not in context[0]


def test_clear_history(conversation: Conversation) -> None:
    """Test history clearing."""
    conversation.add_message(
        content="Test message",
        role=MessageRole.USER
    )
    assert len(conversation.messages) == 1

    # Clear history
    conversation.clear_history()
    assert len(conversation.messages) == 0


def test_serialization(conversation: Conversation) -> None:
    """Test conversation serialization."""
    conversation.add_message(
        content="Test message",
        role=MessageRole.USER,
        metadata={"test": True}
    )

    # Convert to dict
    data = conversation.to_dict()
    assert isinstance(data, dict)
    assert len(data["messages"]) == 1
    assert isinstance(data["conversation_id"], str)

    # Create from dict
    new_conversation = Conversation.from_dict(data)
    assert isinstance(new_conversation, Conversation)
    assert len(new_conversation.messages) == 1
    assert new_conversation.messages[0].content == "Test message"
    assert new_conversation.messages[0].role == MessageRole.USER
    assert new_conversation.messages[0].metadata["test"] is True 