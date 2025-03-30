"""Tests for the PepperPy class."""

from unittest.mock import AsyncMock, patch

import pytest

from pepperpy import PepperPy
from pepperpy.llm import MessageRole


@pytest.mark.asyncio
async def test_pepperpy_with_llm():
    """Test PepperPy with LLM provider."""
    # This internally uses the plugin system
    pepper = PepperPy().with_llm("openai", api_key="fake_key")

    # Check that provider was created correctly
    assert pepper._llm_provider is not None
    assert pepper._llm_provider.name == "openai"


@pytest.mark.asyncio
async def test_pepperpy_chat():
    """Test PepperPy chat builder."""
    pepper = PepperPy().with_llm("openai", api_key="fake_key")

    # Access chat builder
    chat = pepper.chat
    assert chat is not None

    # Build a chat session
    chat = chat.with_system("You are helpful.").with_user("Tell me about Python.")

    # Check messages
    assert len(chat._messages) == 2
    assert chat._messages[0].role == MessageRole.SYSTEM
    assert chat._messages[0].content == "You are helpful."
    assert chat._messages[1].role == MessageRole.USER
    assert chat._messages[1].content == "Tell me about Python."


@pytest.mark.asyncio
async def test_pepperpy_chat_no_provider():
    """Test PepperPy chat builder without provider."""
    pepper = PepperPy()

    # Try to access chat builder without provider
    with pytest.raises(ValueError) as exc:
        _ = pepper.chat
    assert "LLM provider not configured" in str(exc.value)


@pytest.mark.asyncio
async def test_pepperpy_context_manager():
    """Test PepperPy context manager."""
    # Create a mock provider
    mock_provider = AsyncMock()

    with patch("pepperpy.plugin_manager.plugin_manager.create_provider") as mock_create:
        mock_create.return_value = mock_provider

        # Use context manager
        async with PepperPy().with_llm("openai", api_key="fake_key") as pepper:
            assert pepper._llm_provider is mock_provider
            mock_provider.initialize.assert_called_once()

        # Check cleanup
        mock_provider.cleanup.assert_called_once()
