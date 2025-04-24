"""
MCP Protocol Adapter.

This module adapts the Model Context Protocol to the PepperPy communication interface
using the official MCP library as a backend.
"""

import asyncio
import uuid
from collections.abc import AsyncGenerator
from typing import Any, Dict, List, Optional, TypedDict, cast

import aiohttp
from aiohttp import ClientSession, FormData
from mcp import ClientSession as MCPClientSession, SSEServer, types

from pepperpy.communication import (
    BaseCommunicationProvider,
    CommunicationError,
    CommunicationProtocol,
    DataPart,
    FilePart,
    Message,
    TextPart,
)
from pepperpy.core.errors import ValidationError
from pepperpy.core.logging import get_logger
from pepperpy.plugin.plugin import ProviderPlugin

logger = get_logger(__name__)


class MCPStatusCode(int):
    """MCP status codes."""

    OK = 200
    ACCEPTED = 202
    BAD_REQUEST = 400
    UNAUTHORIZED = 401
    FORBIDDEN = 403
    NOT_FOUND = 404
    INTERNAL_ERROR = 500


class MCPResponse(TypedDict, total=False):
    """MCP response type."""

    status: MCPStatusCode
    message: str
    data: Dict[str, Any]
    error: str


class MCPCommunicationAdapter(BaseCommunicationProvider, ProviderPlugin):
    """Adapter for Model Context Protocol using the official MCP library."""

    def __init__(self, **config: Any) -> None:
        """Initialize MCP adapter.

        Args:
            **config: Configuration options
        """
        super().__init__(**config)
        self.base_url = self.config.get("base_url", "http://localhost:8000")
        self.api_key = self.config.get("api_key", "")
        self.timeout = int(self.config.get("timeout", 30))
        self.http_session: Optional[ClientSession] = None
        self.mcp_session: Optional[MCPClientSession] = None

    @property
    def protocol_type(self) -> CommunicationProtocol:
        """Get the protocol type.

        Returns:
            Communication protocol type
        """
        return CommunicationProtocol.MCP

    async def _initialize_resources(self) -> None:
        """Initialize HTTP and MCP sessions."""
        try:
            # Initialize the HTTP session for PepperPy compatibility
            self.http_session = aiohttp.ClientSession(
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                }
            )
            
            # Initialize the MCP session using the official library
            server = SSEServer(self.base_url)
            self.mcp_session = MCPClientSession(server)
            await self.mcp_session.initialize()
            
            logger.info(f"Initialized MCP adapter with URL: {self.base_url}")
        except Exception as e:
            logger.error(f"Failed to initialize MCP adapter: {e}")
            raise CommunicationError(f"Failed to initialize MCP adapter: {e}") from e

    async def _cleanup_resources(self) -> None:
        """Clean up HTTP and MCP sessions."""
        try:
            if self.http_session:
                await self.http_session.close()
                self.http_session = None
            
            if self.mcp_session:
                await self.mcp_session.close()
                self.mcp_session = None
                
            logger.info("Cleaned up MCP adapter")
        except Exception as e:
            logger.error(f"Error during MCP adapter cleanup: {e}")

    def _convert_to_mcp_message(self, message: Message) -> Dict[str, Any]:
        """Convert generic message to MCP message.

        Args:
            message: Generic message

        Returns:
            MCP message dict
        """
        mcp_message = {
            "sender": message.sender or "user",
            "recipient": message.receiver,
            "request_id": str(uuid.uuid4()),
            "timestamp": "",  # Will be set by server
        }

        # Convert text parts
        text_content = ""
        for text_part in message.get_text_parts():
            text_content += text_part.text + "\n"
            
        if text_content:
            mcp_message["text"] = text_content.strip()

        # Convert data parts
        if data_parts := message.get_data_parts():
            # Use first data part as primary data
            mcp_message["data"] = data_parts[0].data
            
        # Add metadata
        if message.metadata:
            mcp_message["metadata"] = message.metadata

        return mcp_message

    def _convert_from_mcp_response(self, response: Dict[str, Any]) -> Message:
        """Convert MCP response to generic message.

        Args:
            response: MCP response dict

        Returns:
            Generic message
        """
        message = Message(
            sender=response.get("sender"),
            task_id=response.get("request_id"),
            metadata=response.get("metadata", {})
        )

        # Add text if present
        if "text" in response and response["text"]:
            message.add_part(TextPart(response["text"], role=response.get("sender")))

        # Add data if present
        if "data" in response and response["data"]:
            message.add_part(DataPart(response["data"], format_="json"))

        return message

    async def send_message(self, message: Message) -> str:
        """Send a message to a recipient using the MCP library.

        Args:
            message: Message to send

        Returns:
            Message ID

        Raises:
            CommunicationError: If message sending fails
        """
        if not self._initialized:
            await self.initialize()

        if not self.http_session or not self.mcp_session:
            raise CommunicationError("MCP adapter not initialized")

        if not message.receiver:
            raise ValidationError("Message must have a receiver")

        try:
            # Convert to MCP format
            mcp_message = self._convert_to_mcp_message(message)
            message_id = mcp_message["request_id"]
            
            # Use MCP session to call a tool for sending messages if available
            # If the server doesn't support messaging directly, fall back to HTTP
            try:
                if self.mcp_session:
                    # Try using MCP session for message sending
                    result = await self.mcp_session.call_tool(
                        "send_message", 
                        {"message": mcp_message}
                    )
                    if result and "message_id" in result:
                        return result["message_id"]
            except Exception as mcp_error:
                logger.debug(f"MCP-native message sending failed, falling back to HTTP: {mcp_error}")
            
            # Fallback to HTTP if MCP tool is not available
            async with self.http_session.post(
                f"{self.base_url}/messages", json=mcp_message, timeout=self.timeout
            ) as response:
                data = await response.json()
                if response.status >= 400:
                    raise CommunicationError(
                        f"Failed to send message: {data.get('error', response.reason)}"
                    )

                logger.debug(f"Message sent with ID: {message_id}")
                return message_id

        except aiohttp.ClientError as e:
            logger.error(f"HTTP error sending message: {e}")
            raise CommunicationError(f"HTTP error sending message: {e}") from e
        except Exception as e:
            logger.error(f"Failed to send message: {e}")
            raise CommunicationError(f"Failed to send message: {e}") from e

    async def receive_message(self, message_id: str) -> Message:
        """Receive a message by ID using the MCP library.

        Args:
            message_id: Message ID

        Returns:
            Received message

        Raises:
            CommunicationError: If message retrieval fails
        """
        if not self._initialized:
            await self.initialize()

        if not self.http_session or not self.mcp_session:
            raise CommunicationError("MCP adapter not initialized")

        try:
            # Try using MCP session for message retrieval
            try:
                if self.mcp_session:
                    result = await self.mcp_session.call_tool(
                        "get_message",
                        {"message_id": message_id}
                    )
                    if result:
                        return self._convert_from_mcp_response(result)
            except Exception as mcp_error:
                logger.debug(f"MCP-native message retrieval failed, falling back to HTTP: {mcp_error}")
            
            # Fallback to HTTP if MCP tool is not available
            async with self.http_session.get(
                f"{self.base_url}/messages/{message_id}", timeout=self.timeout
            ) as response:
                if response.status >= 400:
                    data = await response.json()
                    raise CommunicationError(
                        f"Failed to receive message: {data.get('error', response.reason)}"
                    )

                data = await response.json()
                return self._convert_from_mcp_response(data)
                
        except aiohttp.ClientError as e:
            logger.error(f"HTTP error receiving message: {e}")
            raise CommunicationError(f"HTTP error receiving message: {e}") from e
        except Exception as e:
            logger.error(f"Failed to receive message: {e}")
            raise CommunicationError(f"Failed to receive message: {e}") from e

    async def stream_messages(
        self, filter_criteria: Dict[str, Any] | None = None
    ) -> AsyncGenerator[Message, None]:
        """Stream messages based on filter criteria using the MCP library when possible.

        Args:
            filter_criteria: Optional filtering criteria

        Yields:
            Messages matching the criteria

        Raises:
            CommunicationError: If streaming fails
        """
        if not self._initialized:
            await self.initialize()

        if not self.http_session or not self.mcp_session:
            raise CommunicationError("MCP adapter not initialized")

        try:
            # Try using MCP subscription capability if available
            try:
                if self.mcp_session:
                    # Check if server has a message subscription tool
                    tools = await self.mcp_session.list_tools()
                    has_subscribe_tool = any(tool.name == "subscribe_messages" for tool in tools)
                    
                    if has_subscribe_tool:
                        # Use the tool to subscribe to messages
                        subscription_result = await self.mcp_session.call_tool(
                            "subscribe_messages", 
                            filter_criteria or {}
                        )
                        
                        if subscription_result and "subscription_id" in subscription_result:
                            subscription_id = subscription_result["subscription_id"]
                            
                            # Poll for messages on the subscription
                            while True:
                                result = await self.mcp_session.call_tool(
                                    "get_subscription_messages",
                                    {"subscription_id": subscription_id}
                                )
                                
                                if result and "messages" in result:
                                    for msg_data in result["messages"]:
                                        yield self._convert_from_mcp_response(msg_data)
                                
                                # If no more messages or subscription ended, break
                                if not result or result.get("status") == "ended":
                                    break
                                    
                                # Sleep briefly before polling again
                                await asyncio.sleep(0.5)
                            
                            # Successfully used subscription, return
                            return
            except Exception as mcp_error:
                logger.debug(f"MCP-native message streaming failed, falling back to HTTP: {mcp_error}")
            
            # Fallback to HTTP if subscription is not available
            # Convert filter criteria to query parameters
            params = filter_criteria or {}

            async with self.http_session.get(
                f"{self.base_url}/messages", params=params, timeout=self.timeout
            ) as response:
                if response.status >= 400:
                    data = await response.json()
                    raise CommunicationError(
                        f"Failed to stream messages: {data.get('error', response.reason)}"
                    )

                data = await response.json()
                for msg_data in data.get("messages", []):
                    yield self._convert_from_mcp_response(msg_data)

        except aiohttp.ClientError as e:
            logger.error(f"HTTP error streaming messages: {e}")
            raise CommunicationError(f"HTTP error streaming messages: {e}") from e
        except Exception as e:
            logger.error(f"Failed to stream messages: {e}")
            raise CommunicationError(f"Failed to stream messages: {e}") from e
