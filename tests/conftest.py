"""Common test fixtures and utilities."""

import pytest

from pepperpy_ai.providers.mock import MockProvider
from pepperpy_ai.responses import AIResponse
from pepperpy_ai.types import Message, MessageRole


@pytest.fixture
def mock_provider():
    """Fixture that provides a mock provider."""
    return MockProvider()


@pytest.fixture
def mock_message():
    """Fixture that provides a mock message."""
    return Message(
        role=MessageRole.USER,
        content="Test message",
        metadata={"test": "value"}
    )


@pytest.fixture
def mock_response():
    """Fixture that provides a mock AI response."""
    return AIResponse(
        content="Test response",
        metadata={"test": "value"}
    ) 