"""
MCP client interfaces.

This module defines the interfaces for MCP clients.
"""

import uuid
from abc import abstractmethod
from collections.abc import AsyncGenerator
from typing import Any

from pepperpy.core.logging import get_logger
from pepperpy.mcp.base import MCPProvider
from pepperpy.mcp.protocol import (
    MCPOperationType,
    MCPRequest,
    MCPResponse,
    MCPStatusCode,
)

logger = get_logger(__name__)


class MCPClientProvider(MCPProvider):
    """Client interface for MCP providers."""

    def __init__(self, **kwargs: Any) -> None:
        """Initialize with configuration.

        Args:
            **kwargs: Provider configuration
        """
        self.config = kwargs
        self.server_url = self.config.get("server_url", "")
        self.initialized = False
        self.connected = False

    @abstractmethod
    async def connect(self, server_url: str | None = None) -> None:
        """Connect to an MCP server.

        Args:
            server_url: The URL of the MCP server to connect to.
                        If None, use the URL from initialization.

        Raises:
            ConnectionError: If connection fails
        """
        # Set the server URL if provided
        if server_url:
            self.server_url = server_url

        # Default implementation logs the connection attempt
        logger.info(f"Connecting to MCP server: {self.server_url}")

    @abstractmethod
    async def disconnect(self) -> None:
        """Disconnect from the MCP server.

        Raises:
            ConnectionError: If disconnection fails
        """
        logger.info("Disconnecting from MCP server")
        self.connected = False

    @abstractmethod
    async def request(self, request: MCPRequest) -> MCPResponse:
        """Send a request to the MCP server.

        Args:
            request: The request to send

        Returns:
            The server's response

        Raises:
            ConnectionError: If not connected to a server
            ValueError: If the request is invalid
            TimeoutError: If the server does not respond in time
        """
        ...

    @abstractmethod
    async def stream(self, request: MCPRequest) -> AsyncGenerator[MCPResponse, None]:
        """Stream responses from the MCP server.

        Args:
            request: The request to send

        Yields:
            Response chunks from the server

        Raises:
            ConnectionError: If not connected to a server
            ValueError: If the request is invalid
            TimeoutError: If the server does not respond in time
        """
        ...

    # Convenience methods for common operations
    async def complete(self, prompt: str, model_id: str, **params) -> str:
        """Request a completion from the server.

        Args:
            prompt: The prompt text
            model_id: The model to use
            **params: Additional parameters

        Returns:
            The completion text

        Raises:
            ConnectionError: If not connected to a server
            ValueError: If parameters are invalid
            RuntimeError: If the completion fails
        """
        request = MCPRequest(
            request_id=self._generate_id(),
            model_id=model_id,
            operation=MCPOperationType.COMPLETION,
            inputs={"prompt": prompt},
            parameters=params,
        )

        logger.info(f"Requesting completion from model {model_id}")
        response = await self.request(request)

        if response.status != MCPStatusCode.SUCCESS:
            error_msg = f"Completion error: {response.error}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)

        return response.outputs.get("text", "")

    async def stream_complete(
        self, prompt: str, model_id: str, **params
    ) -> AsyncGenerator[str, None]:
        """Stream a completion from the server.

        Args:
            prompt: The prompt text
            model_id: The model to use
            **params: Additional parameters

        Yields:
            Completion text chunks

        Raises:
            ConnectionError: If not connected to a server
            ValueError: If parameters are invalid
        """
        request = MCPRequest(
            request_id=self._generate_id(),
            model_id=model_id,
            operation=MCPOperationType.COMPLETION,
            inputs={"prompt": prompt},
            parameters=params,
        )

        logger.info(f"Streaming completion from model {model_id}")
        async for response in self.stream(request):
            if response.status == MCPStatusCode.ERROR:
                error_msg = f"Completion error: {response.error}"
                logger.error(error_msg)
                raise RuntimeError(error_msg)

            if "text" in response.outputs:
                yield response.outputs["text"]

    async def embed(self, text: str, model_id: str, **params) -> list[float]:
        """Request embeddings from the server.

        Args:
            text: The text to embed
            model_id: The model to use
            **params: Additional parameters

        Returns:
            The embedding vector

        Raises:
            ConnectionError: If not connected to a server
            ValueError: If parameters are invalid
            RuntimeError: If the embedding fails
        """
        request = MCPRequest(
            request_id=self._generate_id(),
            model_id=model_id,
            operation=MCPOperationType.EMBEDDING,
            inputs={"text": text},
            parameters=params,
        )

        logger.info(f"Requesting embedding from model {model_id}")
        response = await self.request(request)

        if response.status != MCPStatusCode.SUCCESS:
            error_msg = f"Embedding error: {response.error}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)

        embedding = response.outputs.get("embedding", [])
        logger.debug(f"Received embedding with {len(embedding)} dimensions")
        return embedding

    def _generate_id(self) -> str:
        """Generate a unique request ID."""
        return str(uuid.uuid4())
