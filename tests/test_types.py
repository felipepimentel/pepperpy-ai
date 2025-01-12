"""Tests for core types module."""

import pytest
from typing import cast
from pepperpy_ai.types import JsonDict, Message, MessageRole


def test_message_role() -> None:
    """Test MessageRole enum."""
    assert MessageRole.USER.name == "USER"
    assert MessageRole.ASSISTANT.name == "ASSISTANT"
    assert MessageRole.SYSTEM.name == "SYSTEM"


def test_message_without_metadata() -> None:
    """Test Message class without metadata."""
    message = Message(
        role=MessageRole.USER,
        content="Test message"
    )
    assert message.role == MessageRole.USER
    assert message.content == "Test message"
    assert message.metadata is None


def test_message_with_metadata() -> None:
    """Test Message class with metadata."""
    metadata = cast(JsonDict, {"key": "value"})
    message = Message(
        role=MessageRole.USER,
        content="Test message",
        metadata=metadata
    )
    assert message.role == MessageRole.USER
    assert message.content == "Test message"
    assert message.metadata == metadata
