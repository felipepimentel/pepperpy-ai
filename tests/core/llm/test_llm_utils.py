"""Tests for LLM utility functions."""

from datetime import datetime
from typing import Dict, List, cast

import pytest

from pepperpy.errors.core import PepperPyError
from pepperpy.llm.utils import (
    Message,
    Prompt,
    Response,
    calculate_token_usage,
    convert_messages_to_text,
    format_prompt_for_provider,
    get_system_message,
    truncate_prompt,
    validate_prompt,
)


def test_message_dataclass():
    """Test Message dataclass creation and validation."""
    # Test valid message creation
    message = Message(role="user", content="Hello")
    assert message.role == "user"
    assert message.content == "Hello"

    # Test invalid role
    with pytest.raises(PepperPyError):
        Message(role="invalid", content="Hello")


def test_prompt_dataclass():
    """Test Prompt dataclass creation and validation."""
    messages = [
        Message(role="system", content="You are a helpful assistant."),
        Message(role="user", content="Hello"),
    ]
    prompt = Prompt(messages=messages)
    assert len(prompt.messages) == 2
    assert prompt.messages[0].role == "system"
    assert prompt.messages[1].role == "user"


def test_response_dataclass():
    """Test Response dataclass creation and validation."""
    response = Response(
        text="Hello!",
        usage={"total_tokens": 10, "prompt_tokens": 5, "completion_tokens": 5},
        metadata={"finish_reason": "stop", "created_at": datetime.now().isoformat()},
    )
    assert response.text == "Hello!"
    assert response.usage["total_tokens"] == 10
    assert response.metadata["finish_reason"] == "stop"
    assert isinstance(response.metadata["created_at"], str)


def test_validate_prompt():
    """Test prompt validation function."""
    # Test valid prompt
    messages = [
        Message(role="system", content="You are a helpful assistant."),
        Message(role="user", content="Hello"),
    ]
    prompt = Prompt(messages=messages)
    assert validate_prompt(prompt) is True

    # Test invalid prompt (no user message)
    messages = [Message(role="system", content="You are a helpful assistant.")]
    prompt = Prompt(messages=messages)
    with pytest.raises(PepperPyError):
        validate_prompt(prompt)

    # Test invalid prompt (empty content)
    messages = [Message(role="user", content="")]
    prompt = Prompt(messages=messages)
    with pytest.raises(PepperPyError):
        validate_prompt(prompt)


def test_get_system_message():
    """Test getting system message from prompt."""
    # Test with system message
    messages = [
        Message(role="system", content="You are a helpful assistant."),
        Message(role="user", content="Hello"),
    ]
    prompt = Prompt(messages=messages)
    system_message = get_system_message(prompt.messages)
    assert system_message == "You are a helpful assistant."

    # Test without system message
    messages = [Message(role="user", content="Hello")]
    prompt = Prompt(messages=messages)
    system_message = get_system_message(prompt.messages)
    assert system_message is None


def test_convert_messages_to_text():
    """Test converting messages to text format."""
    messages = [
        Message(role="system", content="You are a helpful assistant."),
        Message(role="user", content="Hello"),
        Message(role="assistant", content="Hi! How can I help you?"),
        Message(role="user", content="What's the weather?"),
    ]
    prompt = Prompt(messages=messages)

    # Test default format
    text = convert_messages_to_text(prompt.messages)
    assert "System: You are a helpful assistant." in text
    assert "User: Hello" in text
    assert "Assistant: Hi! How can I help you?" in text
    assert "User: What's the weather?" in text

    # Test chat format
    text = convert_messages_to_text(prompt.messages, format="chat")
    assert "[System]" in text
    assert "[User]" in text
    assert "[Assistant]" in text

    # Test minimal format
    text = convert_messages_to_text(prompt.messages, format="minimal")
    assert "You are a helpful assistant." in text
    assert "Hello" in text
    assert "Hi! How can I help you?" in text
    assert "What's the weather?" in text


def test_format_prompt_for_provider():
    """Test formatting prompt for different providers."""
    messages = [
        Message(role="system", content="You are a helpful assistant."),
        Message(role="user", content="Hello"),
    ]
    prompt = Prompt(messages=messages)

    # Test OpenAI format
    openai_format = format_prompt_for_provider(prompt, "openai")
    assert isinstance(openai_format, list)
    assert len(openai_format) == 2
    messages_dict = cast(List[Dict[str, str]], openai_format)
    assert messages_dict[0]["role"] == "system"
    assert messages_dict[1]["role"] == "user"

    # Test Anthropic format
    anthropic_format = format_prompt_for_provider(prompt, "anthropic")
    assert isinstance(anthropic_format, str)
    assert "\n\nHuman: " in anthropic_format
    assert "\n\nAssistant: " in anthropic_format

    # Test unknown provider
    with pytest.raises(PepperPyError):
        format_prompt_for_provider(prompt, "unknown")


def test_calculate_token_usage():
    """Test token usage calculation."""
    messages = [
        Message(role="system", content="You are a helpful assistant."),
        Message(role="user", content="Hello"),
    ]
    prompt = Prompt(messages=messages)
    prompt_text = convert_messages_to_text(prompt.messages)

    # Test token calculation
    token_count = calculate_token_usage(
        prompt_text, completion_text="Hi!", provider="test", model="test-model"
    )
    assert isinstance(token_count, int)
    assert token_count > 0

    # Test with specific provider
    token_count = calculate_token_usage(
        prompt_text, completion_text="Hi!", provider="openai", model="gpt-3.5-turbo"
    )
    assert isinstance(token_count, int)
    assert token_count > 0


def test_truncate_prompt():
    """Test prompt truncation."""
    long_content = " ".join(["test"] * 1000)  # Create a long message
    messages = [
        Message(role="system", content="You are a helpful assistant."),
        Message(role="user", content=long_content),
    ]
    prompt = Prompt(messages=messages)

    # Test truncation with max tokens
    truncated = truncate_prompt(
        prompt, max_tokens=100, provider="test", model="test-model"
    )
    truncated_text = convert_messages_to_text(truncated.messages)
    token_usage = calculate_token_usage(
        truncated_text, completion_text="", provider="test", model="test-model"
    )
    assert isinstance(token_usage, int)
    assert token_usage <= 100

    # Test truncation with keep_system_message=True (default behavior)
    truncated = truncate_prompt(
        prompt, max_tokens=50, provider="test", model="test-model"
    )
    assert truncated.messages[0].content == "You are a helpful assistant."
    truncated_text = convert_messages_to_text(truncated.messages)
    token_usage = calculate_token_usage(
        truncated_text, completion_text="", provider="test", model="test-model"
    )
    assert isinstance(token_usage, int)
    assert token_usage <= 50

    # Test truncation with keep_system_message=False
    truncated = truncate_prompt(
        prompt,
        max_tokens=50,
        keep_system_message=False,
        provider="test",
        model="test-model",
    )
    truncated_text = convert_messages_to_text(truncated.messages)
    token_usage = calculate_token_usage(
        truncated_text, completion_text="", provider="test", model="test-model"
    )
    assert isinstance(token_usage, int)
    assert token_usage <= 50

    # Test truncation with too small max_tokens
    with pytest.raises(PepperPyError):
        truncate_prompt(prompt, max_tokens=10, provider="test", model="test-model")
