"""
Tests for the MCP plugin.

This module tests the MCP plugin's integration with the official MCP library.
"""

import asyncio
import pytest
from unittest.mock import MagicMock, patch

from pepperpy import PepperPy
from pepperpy.communication import Message, TextPart
from plugins.communication.mcp.adapter import MCPCommunicationAdapter


@pytest.mark.asyncio
async def test_mcp_adapter_initialization():
    """Test MCP adapter initialization."""
    adapter = MCPCommunicationAdapter(base_url="http://localhost:8000")
    
    # Mock the MCP ClientSession to avoid actual network connections
    with patch("plugins.communication.mcp.adapter.MCPClientSession") as mock_session_class:
        # Mock initialize and close methods
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        
        # Initialize the adapter
        await adapter.initialize()
        
        # Verify the session was initialized
        assert adapter._initialized is True
        assert adapter.mcp_session is not None
        mock_session.initialize.assert_called_once()
        
        # Clean up
        await adapter.cleanup()
        mock_session.close.assert_called_once()


@pytest.mark.asyncio
async def test_mcp_message_conversion():
    """Test conversion between Message and MCP format."""
    adapter = MCPCommunicationAdapter()
    
    # Create a test message
    message = Message(sender="test_sender", receiver="test_receiver")
    message.add_part(TextPart("Hello, MCP world!"))
    message.metadata = {"key": "value"}
    
    # Convert to MCP format
    mcp_message = adapter._convert_to_mcp_message(message)
    
    # Verify conversion
    assert mcp_message["sender"] == "test_sender"
    assert mcp_message["recipient"] == "test_receiver"
    assert mcp_message["text"] == "Hello, MCP world!"
    assert mcp_message["metadata"] == {"key": "value"}
    
    # Convert back
    result_message = adapter._convert_from_mcp_response(mcp_message)
    
    # Verify reconversion
    text_parts = result_message.get_text_parts()
    assert len(text_parts) == 1
    assert text_parts[0].text == "Hello, MCP world!"
    assert result_message.metadata == {"key": "value"}


@pytest.mark.asyncio
async def test_pepperpy_mcp_integration():
    """Test PepperPy integration with MCP adapter."""
    # Create PepperPy instance with mocked MCP adapter
    with patch("pepperpy.core.provider_registry.create_provider") as mock_create_provider:
        # Setup mock adapter
        mock_adapter = MagicMock()
        mock_adapter._initialized = False
        mock_create_provider.return_value = mock_adapter
        
        # Initialize PepperPy with MCP
        pepperpy = PepperPy().with_communication("mcp", 
                                             base_url="http://test-server:8000")
        
        # Initialize (should call adapter.initialize)
        await pepperpy.initialize()
        mock_adapter.initialize.assert_called_once()
        
        # Test sending a message
        test_message = Message(receiver="test_receiver")
        test_message.add_part(TextPart("Test message"))
        
        mock_adapter.send_message.return_value = "test_message_id"
        message_id = await pepperpy.communication.send_message(test_message)
        
        assert message_id == "test_message_id"
        mock_adapter.send_message.assert_called_once()
        
        # Clean up
        await pepperpy.cleanup()
        mock_adapter.cleanup.assert_called_once() 