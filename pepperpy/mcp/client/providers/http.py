"""
HTTP client provider for MCP.

This module provides an HTTP client implementation for the MCP protocol.
"""

import json
from collections.abc import AsyncGenerator
from typing import Any

import aiohttp

from pepperpy.core.logging import get_logger
from pepperpy.mcp.client.base import MCPClientProvider
from pepperpy.mcp.protocol import MCPRequest, MCPResponse

logger = get_logger(__name__)


class HTTPClientProvider(MCPClientProvider):
    """HTTP client implementation for MCP."""

    def __init__(self, **kwargs: Any) -> None:
        """Initialize with configuration."""
        super().__init__(**kwargs)
        self.timeout = self.config.get("timeout", 60)
        self.session: aiohttp.ClientSession | None = None

    async def initialize(self) -> None:
        """Initialize the provider."""
        if self.initialized:
            return

        logger.info("Initializing HTTP MCP client")
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.timeout),
            headers={"Content-Type": "application/json"},
        )
        self.initialized = True

    async def cleanup(self) -> None:
        """Clean up resources."""
        if not self.initialized:
            return

        logger.info("Cleaning up HTTP MCP client")
        if self.session:
            await self.session.close()
            self.session = None

        self.initialized = False
        self.connected = False

    async def connect(self, server_url: str | None = None) -> None:
        """Connect to an MCP server."""
        await super().connect(server_url)

        if not self.initialized:
            await self.initialize()

        # Test the connection with a ping
        if not self.session:
            raise RuntimeError("HTTP session not initialized")

        try:
            async with self.session.get(f"{self.server_url}/health") as response:
                if response.status != 200:
                    raise ConnectionError(
                        f"Failed to connect to MCP server: {response.status}"
                    )

            self.connected = True
            logger.info(f"Connected to MCP server: {self.server_url}")
        except aiohttp.ClientError as e:
            logger.error(f"Failed to connect to MCP server: {e}")
            self.connected = False
            raise ConnectionError(f"Failed to connect to MCP server: {e}")

    async def disconnect(self) -> None:
        """Disconnect from the MCP server."""
        await super().disconnect()

    async def request(self, request: MCPRequest) -> MCPResponse:
        """Send a request to the MCP server."""
        if not self.connected:
            raise ConnectionError("Not connected to MCP server")

        if not self.session:
            raise RuntimeError("HTTP session not initialized")

        try:
            # Convert request to dict for serialization
            request_data = request.to_dict()

            # Send the request
            logger.debug(f"Sending request to {self.server_url}/api/v1/request")
            async with self.session.post(
                f"{self.server_url}/api/v1/request",
                json=request_data,
                timeout=self.timeout,
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(
                        f"Error from MCP server: {response.status} - {error_text}"
                    )
                    return MCPResponse.error_response(
                        request_id=request.request_id,
                        model_id=request.model_id,
                        error_message=f"HTTP error: {response.status} - {error_text}",
                    )

                # Parse the response
                response_data = await response.json()
                return MCPResponse.from_dict(response_data)

        except TimeoutError:
            logger.error("Timeout while sending request to MCP server")
            return MCPResponse.error_response(
                request_id=request.request_id,
                model_id=request.model_id,
                error_message="Request timed out",
            )
        except aiohttp.ClientError as e:
            logger.error(f"Error sending request to MCP server: {e}")
            return MCPResponse.error_response(
                request_id=request.request_id,
                model_id=request.model_id,
                error_message=f"HTTP client error: {e}",
            )
        except Exception as e:
            logger.exception(f"Unexpected error: {e}")
            return MCPResponse.error_response(
                request_id=request.request_id,
                model_id=request.model_id,
                error_message=f"Unexpected error: {e}",
            )

    async def stream(self, request: MCPRequest) -> AsyncGenerator[MCPResponse, None]:
        """Stream responses from the MCP server."""
        if not self.connected:
            raise ConnectionError("Not connected to MCP server")

        if not self.session:
            raise RuntimeError("HTTP session not initialized")

        try:
            # Convert request to dict for serialization
            request_data = request.to_dict()

            # Send the request for streaming
            logger.debug(
                f"Sending streaming request to {self.server_url}/api/v1/stream"
            )
            async with self.session.post(
                f"{self.server_url}/api/v1/stream",
                json=request_data,
                timeout=self.timeout,
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(
                        f"Error from MCP server: {response.status} - {error_text}"
                    )
                    yield MCPResponse.error_response(
                        request_id=request.request_id,
                        model_id=request.model_id,
                        error_message=f"HTTP error: {response.status} - {error_text}",
                    )
                    return

                # Stream the response chunks
                async for line in response.content:
                    line = line.strip()
                    if not line:
                        continue

                    try:
                        # Parse the line as JSON
                        chunk_data = json.loads(line)
                        chunk_response = MCPResponse.from_dict(chunk_data)
                        yield chunk_response
                    except json.JSONDecodeError as e:
                        logger.error(f"Error parsing JSON from server: {e}")
                        yield MCPResponse.error_response(
                            request_id=request.request_id,
                            model_id=request.model_id,
                            error_message=f"Error parsing server response: {e}",
                        )
                    except Exception as e:
                        logger.exception(f"Error processing response chunk: {e}")
                        yield MCPResponse.error_response(
                            request_id=request.request_id,
                            model_id=request.model_id,
                            error_message=f"Error processing response: {e}",
                        )

        except TimeoutError:
            logger.error("Timeout while streaming from MCP server")
            yield MCPResponse.error_response(
                request_id=request.request_id,
                model_id=request.model_id,
                error_message="Stream timed out",
            )
        except aiohttp.ClientError as e:
            logger.error(f"Error streaming from MCP server: {e}")
            yield MCPResponse.error_response(
                request_id=request.request_id,
                model_id=request.model_id,
                error_message=f"HTTP client error: {e}",
            )
        except Exception as e:
            logger.exception(f"Unexpected error during streaming: {e}")
            yield MCPResponse.error_response(
                request_id=request.request_id,
                model_id=request.model_id,
                error_message=f"Unexpected error: {e}",
            )
