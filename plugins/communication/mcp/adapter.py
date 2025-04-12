"""
MCP Protocol Adapter.

This module adapts the Message Communication Protocol to the PepperPy communication interface.
"""

import uuid
from collections.abc import AsyncGenerator
from typing import Any, Dict, List, Optional, TypedDict, cast

import aiohttp
from aiohttp import ClientSession, FormData

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
    """Adapter for Message Communication Protocol."""

    def __init__(self, **config: Any) -> None:
        """Initialize MCP adapter.

        Args:
            **config: Configuration options
        """
        super().__init__(**config)
        self.base_url = self.config.get("base_url", "http://localhost:8000/api")
        self.api_key = self.config.get("api_key", "")
        self.timeout = int(self.config.get("timeout", 30))
        self.session: Optional[ClientSession] = None

    @property
    def protocol_type(self) -> CommunicationProtocol:
        """Get the protocol type.

        Returns:
            Communication protocol type
        """
        return CommunicationProtocol.MCP

    async def _initialize_resources(self) -> None:
        """Initialize HTTP session."""
        try:
            self.session = aiohttp.ClientSession(
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                }
            )
            logger.info(f"Initialized MCP adapter with URL: {self.base_url}")
        except Exception as e:
            logger.error(f"Failed to initialize MCP adapter: {e}")
            raise CommunicationError(f"Failed to initialize MCP adapter: {e}") from e

    async def _cleanup_resources(self) -> None:
        """Clean up HTTP session."""
        if self.session:
            await self.session.close()
            self.session = None
            logger.info("Cleaned up MCP adapter")

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
        """Send a message to a recipient.

        Args:
            message: Message to send

        Returns:
            Message ID

        Raises:
            CommunicationError: If message sending fails
        """
        if not self._initialized:
            await self.initialize()

        if not self.session:
            raise CommunicationError("MCP adapter not initialized")

        if not message.receiver:
            raise ValidationError("Message must have a receiver")

        try:
            mcp_message = self._convert_to_mcp_message(message)
            message_id = mcp_message["request_id"]

            async with self.session.post(
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
        """Receive a message by ID.

        Args:
            message_id: Message ID

        Returns:
            Received message

        Raises:
            CommunicationError: If message retrieval fails
        """
        if not self._initialized:
            await self.initialize()

        if not self.session:
            raise CommunicationError("MCP adapter not initialized")

        try:
            async with self.session.get(
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
        """Stream messages based on filter criteria.

        Args:
            filter_criteria: Optional filtering criteria

        Yields:
            Messages matching the criteria

        Raises:
            CommunicationError: If streaming fails
        """
        if not self._initialized:
            await self.initialize()

        if not self.session:
            raise CommunicationError("MCP adapter not initialized")

        try:
            # Convert filter criteria to query parameters
            params = filter_criteria or {}

            async with self.session.get(
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
