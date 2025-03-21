"""Integration tests for HTTP API and LLM providers."""

import json

import pytest

from pepperpy.core.http import (
    format_headers,
    is_json_content,
    parse_json,
)
from pepperpy.llm.utils import (
    Message,
    Prompt,
    Response,
    format_prompt_for_provider,
)


def test_api_request_processing():
    """Test processing of API requests with LLM integration."""
    # Test request headers
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "X-API-Key": "test-key",
    }
    formatted_headers = format_headers(headers)
    assert is_json_content(formatted_headers)

    # Test request body
    request_body = {
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Hello!"},
        ]
    }
    request_json = json.dumps(request_body)

    # Parse and validate request
    parsed_body = parse_json(request_json)
    assert isinstance(parsed_body, dict)
    assert "messages" in parsed_body

    # Convert to LLM format
    messages = [
        Message(role=m["role"], content=m["content"]) for m in parsed_body["messages"]
    ]
    prompt = Prompt(messages=messages)

    # Format for provider
    provider_format = format_prompt_for_provider(prompt, "openai")
    assert isinstance(provider_format, list)
    assert len(provider_format) == 2


def test_api_response_handling():
    """Test handling of LLM responses in API context."""
    # Create a mock LLM response
    response = Response(
        text="Hello! How can I help you?",
        usage={"total_tokens": 10, "prompt_tokens": 5, "completion_tokens": 5},
        metadata={"finish_reason": "stop"},
    )

    # Convert to API response format
    api_response = {
        "response": response.text,
        "usage": response.usage,
        "metadata": response.metadata,
    }

    # Serialize response
    response_json = json.dumps(api_response)
    assert json.loads(response_json)  # Verify valid JSON


def test_api_error_handling():
    """Test error handling in API and LLM integration."""
    # Test invalid JSON request
    with pytest.raises(Exception):
        parse_json("{invalid json}")

    # Test invalid content type
    headers = {"content-type": "text/plain"}
    assert not is_json_content(headers)

    # Test missing required fields
    request_body = {"invalid": "request"}
    with pytest.raises(Exception):
        messages = [Message(role="invalid", content="test")]
        Prompt(messages=messages)

    # Test invalid provider
    messages = [Message(role="user", content="test")]
    prompt = Prompt(messages=messages)
    with pytest.raises(Exception):
        format_prompt_for_provider(prompt, "invalid_provider")
