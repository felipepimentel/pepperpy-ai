"""Test domain models used by providers.

This module contains tests for the domain models used by providers.
"""

from datetime import datetime
from enum import Enum

import pytest
from pydantic import SecretStr, ValidationError

from pepperpy.providers.domain import (
    Conversation,
    Message,
    ProviderAPIError,
    ProviderConfigError,
    ProviderError,
    ProviderInitError,
    ProviderNotFoundError,
    ProviderRateLimitError,
)
from pepperpy.providers.provider import ProviderConfig


class Role(str, Enum):
    """Message role types."""

    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


def test_message_creation() -> None:
    """Test message model creation and validation."""
    timestamp = datetime.utcnow()
    metadata = {"source": "test"}

    message = Message(
        role="user", content="Hello, world!", timestamp=timestamp, metadata=metadata
    )

    assert message.role == "user"
    assert message.content == "Hello, world!"
    assert message.timestamp == timestamp
    assert message.metadata == metadata


def test_message_defaults() -> None:
    """Test message model default values."""
    message = Message(role="user", content="test")

    assert isinstance(message.timestamp, datetime)
    assert isinstance(message.metadata, dict)
    assert len(message.metadata) == 0


def test_conversation_creation() -> None:
    """Test conversation model creation."""
    conversation = Conversation()
    assert len(conversation.messages) == 0
    assert isinstance(conversation.metadata, dict)


def test_conversation_add_message() -> None:
    """Test adding messages to conversation."""
    conversation = Conversation()

    # Add a user message
    conversation.add_message(role="user", content="Hello!", source="test")

    assert len(conversation.messages) == 1
    message = conversation.messages[0]
    assert message.role == "user"
    assert message.content == "Hello!"
    assert message.metadata["source"] == "test"

    # Add an assistant message
    conversation.add_message(role="assistant", content="Hi there!", model="test-model")

    assert len(conversation.messages) == 2
    message = conversation.messages[1]
    assert message.role == "assistant"
    assert message.content == "Hi there!"
    assert message.metadata["model"] == "test-model"


def test_provider_error() -> None:
    """Test base provider error."""
    error = ProviderError(
        "Test error", provider_type="test", details={"reason": "testing"}
    )

    assert str(error) == "Test error"
    assert error.provider_type == "test"
    assert error.details == {"reason": "testing"}


def test_provider_not_found_error() -> None:
    """Test provider not found error."""
    error = ProviderNotFoundError("Provider 'test' not found", provider_type="test")

    assert isinstance(error, ProviderError)
    assert error.provider_type == "test"


def test_provider_init_error() -> None:
    """Test provider initialization error."""
    error = ProviderInitError(
        "Failed to initialize",
        provider_type="test",
        details={"reason": "connection failed"},
    )

    assert isinstance(error, ProviderError)
    assert error.provider_type == "test"
    assert error.details["reason"] == "connection failed"


def test_provider_config_error() -> None:
    """Test provider configuration error."""
    error = ProviderConfigError(
        "Invalid configuration",
        provider_type="test",
        details={"field": "api_key", "error": "missing"},
    )

    assert isinstance(error, ProviderError)
    assert error.provider_type == "test"
    assert error.details["field"] == "api_key"


def test_provider_api_error() -> None:
    """Test provider API error."""
    error = ProviderAPIError(
        "API request failed",
        provider_type="test",
        details={"status": 500, "message": "Internal error"},
    )

    assert isinstance(error, ProviderError)
    assert error.provider_type == "test"
    assert error.details["status"] == 500


def test_provider_rate_limit_error() -> None:
    """Test provider rate limit error."""
    error = ProviderRateLimitError(
        "Rate limit exceeded", provider_type="test", details={"retry_after": 60}
    )

    assert isinstance(error, ProviderAPIError)
    assert error.provider_type == "test"
    assert error.details["retry_after"] == 60


def test_create_message() -> None:
    """Test creating a message."""
    message = Message(role=Role.USER, content="Hello")
    assert message.role == Role.USER
    assert message.content == "Hello"


def test_create_message_with_name() -> None:
    """Test creating a message with a name."""
    message = Message(role=Role.USER, content="Hello", name="John")
    assert message.role == Role.USER
    assert message.content == "Hello"
    assert message.name == "John"


def test_create_message_with_invalid_role() -> None:
    """Test creating a message with an invalid role."""
    with pytest.raises(ValidationError):
        Message(role="invalid", content="Hello")


def test_create_message_with_empty_content() -> None:
    """Test creating a message with empty content."""
    with pytest.raises(ValidationError):
        Message(role=Role.USER, content="")


def test_provider_config_creation() -> None:
    """Test creating a provider config."""
    config = ProviderConfig(
        provider_type="openai",
        api_key=SecretStr("test-key"),
        model="gpt-4",
        timeout=30,
        max_retries=3,
    )
    assert config.provider_type == "openai"
    assert config.api_key.get_secret_value() == "test-key"
    assert config.model == "gpt-4"
    assert config.timeout == 30
    assert config.max_retries == 3


def test_provider_config_with_custom_values() -> None:
    """Test creating a provider config with custom values."""
    config = ProviderConfig(
        provider_type="openai",
        api_key=SecretStr("test-key"),
        model="gpt-4",
        timeout=60,
        max_retries=5,
    )
    assert config.provider_type == "openai"
    assert config.api_key.get_secret_value() == "test-key"
    assert config.model == "gpt-4"
    assert config.timeout == 60
    assert config.max_retries == 5


def test_provider_config_validation() -> None:
    """Test provider config validation."""
    with pytest.raises(ValidationError):
        ProviderConfig(
            provider_type="openai",
            api_key=SecretStr("test-key"),
            model="gpt-4",
            timeout=0,  # invalid value
            max_retries=3,
        )

    with pytest.raises(ValidationError):
        ProviderConfig(
            provider_type="openai",
            api_key=SecretStr("test-key"),
            model="gpt-4",
            timeout=30,
            max_retries=-1,  # invalid value
        )
