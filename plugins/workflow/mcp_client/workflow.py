"""MCP Client Workflow.

This module provides a workflow for connecting to and using an MCP server.
"""

import uuid
from typing import Any

from pepperpy.core.logging import get_logger
from pepperpy.core.workflow import WorkflowProvider
from pepperpy.mcp.protocol import MCPOperationType, MCPRequest
from pepperpy.plugin import BasePluginProvider


class MCPClientWorkflow(WorkflowProvider, BasePluginProvider):
    """Workflow for using MCP clients."""

    def __init__(self) -> None:
        """Initialize MCP client workflow."""
        super().__init__()
        self.logger = get_logger("workflow.mcp_client")
        self.client = None
        self.initialized = False

    async def initialize(self, config: dict[str, Any]) -> bool:
        """Initialize the workflow with the given configuration.

        Args:
            config: The configuration to use.

        Returns:
            True if initialization succeeded, False otherwise.
        """
        if self.initialized:
            return True

        self.logger.info("Initializing MCP client workflow")

        # Get the MCP client provider based on the configuration
        provider_type = config.get("provider_type", "http")
        self.logger.info(f"Using MCP client provider: {provider_type}")

        try:
            # Import the provider dynamically to avoid circular imports
            if provider_type == "http":
                from pepperpy.mcp.client.providers.http import HTTPClientProvider

                self.client = HTTPClientProvider(
                    url=config.get("url", "http://localhost:8000"),
                    timeout=config.get("timeout", 30),
                    retries=config.get("retries", 3),
                    auth_token=config.get("auth_token", ""),
                )
            elif provider_type == "websocket":
                from pepperpy.mcp.client.providers.websocket import (
                    WebSocketClientProvider,
                )

                self.client = WebSocketClientProvider(
                    url=config.get("url", "ws://localhost:8000"),
                    timeout=config.get("timeout", 30),
                    auth_token=config.get("auth_token", ""),
                )
            elif provider_type == "grpc":
                from pepperpy.mcp.client.providers.grpc import GRPCClientProvider

                self.client = GRPCClientProvider(
                    url=config.get("url", "localhost:50051"),
                    timeout=config.get("timeout", 30),
                    auth_token=config.get("auth_token", ""),
                )
            else:
                self.logger.error(f"Unknown provider type: {provider_type}")
                return False

            # Initialize the client
            await self.client.initialize()
            self.initialized = True
            return True
        except Exception as e:
            self.logger.error(f"Failed to initialize MCP client: {e}")
            return False

    async def cleanup(self) -> None:
        """Clean up resources used by the workflow."""
        self.logger.info("Cleaning up MCP client workflow")
        if self.client:
            await self.client.cleanup()
            self.client = None
        self.initialized = False

    async def execute(self, params: dict[str, Any] | None = None) -> dict[str, Any]:
        """Execute the workflow with the given parameters.

        Args:
            params: Additional parameters for the workflow execution.
                task: The task to execute (chat, completion, embedding, stream_chat)
                model_id: The model ID to use
                messages: List of messages for chat
                prompt: Text prompt for completion
                text: Text to embed
                stream: Whether to stream the response
                temperature: Temperature for sampling
                max_tokens: Maximum tokens to generate

        Returns:
            The result of the workflow execution.
        """
        if not params:
            return {"status": "error", "message": "No parameters provided"}

        if not self.initialized or not self.client:
            await self.initialize({})
            if not self.initialized:
                return {"status": "error", "message": "Client not initialized"}

        task = params.get("task", "chat")
        self.logger.info(f"Executing MCP client task: {task}")

        try:
            if task == "chat":
                return await self._execute_chat(params)
            elif task == "completion":
                return await self._execute_completion(params)
            elif task == "embedding":
                return await self._execute_embedding(params)
            elif task == "stream_chat":
                return await self._execute_stream_chat(params)
            else:
                return {
                    "status": "error",
                    "message": f"Unknown task: {task}",
                }
        except Exception as e:
            self.logger.error(f"Error executing task {task}: {e}")
            return {
                "status": "error",
                "message": f"Failed to execute task {task}: {e}",
            }

    async def _execute_chat(self, params: dict[str, Any]) -> dict[str, Any]:
        """Execute a chat task.

        Args:
            params: Task parameters.

        Returns:
            Chat results.
        """
        model_id = params.get("model_id", "gpt-3.5-turbo")
        messages = params.get("messages", [])
        temperature = params.get("temperature", 0.7)
        max_tokens = params.get("max_tokens")

        if not messages:
            return {"status": "error", "message": "No messages provided"}

        # Create the MCP request
        request = MCPRequest(
            request_id=str(uuid.uuid4()),
            model_id=model_id,
            operation=MCPOperationType.CHAT,
            parameters={
                "temperature": temperature,
                "max_tokens": max_tokens,
            },
            inputs={"messages": messages},
        )

        # Send the request
        response = await self.client.request(request)

        if response.status == "error":
            return {
                "status": "error",
                "message": response.error,
            }

        # Extract the result
        return {
            "status": "success",
            "content": response.outputs.get("content", ""),
            "model": model_id,
            "usage": response.metadata.get("usage", {}),
        }

    async def _execute_completion(self, params: dict[str, Any]) -> dict[str, Any]:
        """Execute a completion task.

        Args:
            params: Task parameters.

        Returns:
            Completion results.
        """
        model_id = params.get("model_id", "gpt-3.5-turbo")
        prompt = params.get("prompt", "")
        temperature = params.get("temperature", 0.7)
        max_tokens = params.get("max_tokens")

        if not prompt:
            return {"status": "error", "message": "No prompt provided"}

        # Create the MCP request
        request = MCPRequest(
            request_id=str(uuid.uuid4()),
            model_id=model_id,
            operation=MCPOperationType.COMPLETION,
            parameters={
                "temperature": temperature,
                "max_tokens": max_tokens,
            },
            inputs={"prompt": prompt},
        )

        # Send the request
        response = await self.client.request(request)

        if response.status == "error":
            return {
                "status": "error",
                "message": response.error,
            }

        # Extract the result
        return {
            "status": "success",
            "content": response.outputs.get("content", ""),
            "model": model_id,
            "usage": response.metadata.get("usage", {}),
        }

    async def _execute_embedding(self, params: dict[str, Any]) -> dict[str, Any]:
        """Execute an embedding task.

        Args:
            params: Task parameters.

        Returns:
            Embedding results.
        """
        model_id = params.get("model_id", "text-embedding-ada-002")
        text = params.get("text", "")

        if not text:
            return {"status": "error", "message": "No text provided"}

        # Create the MCP request
        request = MCPRequest(
            request_id=str(uuid.uuid4()),
            model_id=model_id,
            operation=MCPOperationType.EMBEDDING,
            inputs={"text": text},
        )

        # Send the request
        response = await self.client.request(request)

        if response.status == "error":
            return {
                "status": "error",
                "message": response.error,
            }

        # Extract the result
        return {
            "status": "success",
            "embedding": response.outputs.get("embedding", []),
            "model": model_id,
            "usage": response.metadata.get("usage", {}),
        }

    async def _execute_stream_chat(self, params: dict[str, Any]) -> dict[str, Any]:
        """Execute a streaming chat task.

        Args:
            params: Task parameters.

        Returns:
            Chat results.
        """
        model_id = params.get("model_id", "gpt-3.5-turbo")
        messages = params.get("messages", [])
        temperature = params.get("temperature", 0.7)
        max_tokens = params.get("max_tokens")

        if not messages:
            return {"status": "error", "message": "No messages provided"}

        # Create the MCP request
        request = MCPRequest(
            request_id=str(uuid.uuid4()),
            model_id=model_id,
            operation=MCPOperationType.CHAT,
            parameters={
                "temperature": temperature,
                "max_tokens": max_tokens,
                "stream": True,
            },
            inputs={"messages": messages},
        )

        # Send the streaming request
        chunks = []
        async for chunk in self.client.stream(request):
            chunks.append(chunk.outputs.get("content", ""))

        # Combine all chunks
        full_content = "".join(chunks)

        # Return the full response
        return {
            "status": "success",
            "content": full_content,
            "model": model_id,
        }
