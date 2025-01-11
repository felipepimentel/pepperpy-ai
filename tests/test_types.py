"""Tests for core types module."""

import pytest

from pepperpy_ai.types import Message, MessageRole


def test_message_role():
    """Test MessageRole enum."""
    assert MessageRole.SYSTEM.name == "SYSTEM"
    assert MessageRole.USER.name == "USER"
    assert MessageRole.ASSISTANT.name == "ASSISTANT"
    assert len(MessageRole) == 3


def test_message():
    """Test Message class."""
    # Test without metadata
    msg = Message(role=MessageRole.USER, content="Hello")
    assert msg.role == MessageRole.USER
    assert msg.content == "Hello"
    assert msg.metadata is None

    # Test with metadata
    metadata = {"key": "value"}
    msg = Message(role=MessageRole.ASSISTANT, content="Hi", metadata=metadata)
    assert msg.role == MessageRole.ASSISTANT
    assert msg.content == "Hi"
    assert msg.metadata == metadata 