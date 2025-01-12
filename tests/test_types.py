"""Test types module."""

import pytest

from pepperpy_ai.ai_types import MessageRole


def test_message_role_values() -> None:
    """Test message role values."""
    assert MessageRole.SYSTEM == "system"
    assert MessageRole.USER == "user"
    assert MessageRole.ASSISTANT == "assistant"
    assert MessageRole.FUNCTION == "function"


def test_message_role_from_str() -> None:
    """Test message role from string."""
    assert MessageRole("system") == MessageRole.SYSTEM
    assert MessageRole("user") == MessageRole.USER
    assert MessageRole("assistant") == MessageRole.ASSISTANT
    assert MessageRole("function") == MessageRole.FUNCTION

    with pytest.raises(ValueError):
        MessageRole("invalid")


def test_message_role_str() -> None:
    """Test message role string representation."""
    assert MessageRole.SYSTEM.value == "system"
    assert MessageRole.USER.value == "user"
    assert MessageRole.ASSISTANT.value == "assistant"
    assert MessageRole.FUNCTION.value == "function"
