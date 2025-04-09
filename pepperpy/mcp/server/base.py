"""
MCP server interfaces.

This module defines the interfaces for MCP servers.
"""

from abc import abstractmethod
from collections.abc import AsyncGenerator, Callable
from typing import Any, Union

from pepperpy.core.logging import get_logger
from pepperpy.mcp.base import MCPProvider
from pepperpy.mcp.protocol import (
    MCPOperationType,
    MCPRequest,
    MCPResponse,
    MCPStatusCode,
)

logger = get_logger(__name__)

# Type definitions for handlers
RequestHandler = Callable[[MCPRequest], MCPResponse]
AsyncRequestHandler = Callable[[MCPRequest], AsyncGenerator[MCPResponse, None]]
ModelHandler = Union[Any, RequestHandler, AsyncRequestHandler]


class MCPServerProvider(MCPProvider):
    """Server interface for MCP providers."""

    def __init__(self, **kwargs: Any) -> None:
        """Initialize with configuration.

        Args:
            **kwargs: Provider configuration
        """
        self.config = kwargs
        self.host = self.config.get("host", "0.0.0.0")
        self.port = self.config.get("port", 8000)
        self.initialized = False
        self.running = False

        # Storage for registered models and handlers
        self._models: dict[str, Any] = {}
        self._handlers: dict[str, RequestHandler] = {}
        self._stream_handlers: dict[str, AsyncRequestHandler] = {}

    @abstractmethod
    async def start(self, host: str | None = None, port: int | None = None) -> None:
        """Start the MCP server.

        Args:
            host: The host to bind to (if None, use the host from initialization)
            port: The port to bind to (if None, use the port from initialization)

        Raises:
            RuntimeError: If the server cannot be started
        """
        # Set host and port if provided
        if host:
            self.host = host
        if port:
            self.port = port

        logger.info(f"Starting MCP server on {self.host}:{self.port}")
        self.running = True

    @abstractmethod
    async def stop(self) -> None:
        """Stop the MCP server.

        Raises:
            RuntimeError: If the server cannot be stopped
        """
        logger.info("Stopping MCP server")
        self.running = False

    @abstractmethod
    async def register_model(self, model_id: str, model: Any) -> None:
        """Register a model with the server.

        Args:
            model_id: The ID to register the model under
            model: The model handler (typically an LLM provider)

        Raises:
            ValueError: If the model ID is already registered or model is invalid
        """
        if model_id in self._models:
            raise ValueError(f"Model ID already registered: {model_id}")

        self._models[model_id] = model
        logger.info(f"Registered model: {model_id}")

    @abstractmethod
    async def unregister_model(self, model_id: str) -> None:
        """Unregister a model from the server.

        Args:
            model_id: The ID of the model to unregister

        Raises:
            ValueError: If the model ID is not registered
        """
        if model_id not in self._models:
            raise ValueError(f"Model ID not registered: {model_id}")

        del self._models[model_id]
        logger.info(f"Unregistered model: {model_id}")

    @abstractmethod
    async def register_handler(
        self, operation: str, handler: RequestHandler, is_stream: bool = False
    ) -> None:
        """Register a custom handler for an operation.

        Args:
            operation: The operation to handle
            handler: The handler function
            is_stream: Whether the handler is for streaming responses

        Raises:
            ValueError: If the operation is already registered
        """
        if is_stream:
            if operation in self._stream_handlers:
                raise ValueError(
                    f"Stream handler already registered for operation: {operation}"
                )
            self._stream_handlers[operation] = handler
            logger.info(f"Registered stream handler for operation: {operation}")
        else:
            if operation in self._handlers:
                raise ValueError(
                    f"Handler already registered for operation: {operation}"
                )
            self._handlers[operation] = handler
            logger.info(f"Registered handler for operation: {operation}")

    @abstractmethod
    async def handle_request(self, request: MCPRequest) -> MCPResponse:
        """Handle a request.

        Args:
            request: The request to handle

        Returns:
            The response to the request
        """
        logger.info(
            f"Handling request: {request.operation} for model {request.model_id}"
        )

        # Check if model exists
        if request.model_id not in self._models:
            error_msg = f"Model not found: {request.model_id}"
            logger.error(error_msg)
            return MCPResponse.error_response(
                request_id=request.request_id,
                model_id=request.model_id,
                error_message=error_msg,
            )

        # Check if we have a custom handler for this operation
        operation = (
            request.operation.value
            if isinstance(request.operation, MCPOperationType)
            else request.operation
        )
        if operation in self._handlers:
            try:
                logger.debug(f"Using custom handler for operation: {operation}")
                return await self._handlers[operation](request)
            except Exception as e:
                error_msg = f"Error in custom handler: {e!s}"
                logger.exception(error_msg)
                return MCPResponse.error_response(
                    request_id=request.request_id,
                    model_id=request.model_id,
                    error_message=error_msg,
                )

        # Otherwise, use the model to handle the request
        try:
            # Default implementation based on operation type
            model = self._models[request.model_id]

            if operation == MCPOperationType.COMPLETION.value:
                return await self._handle_completion(request, model)
            elif operation == MCPOperationType.EMBEDDING.value:
                return await self._handle_embedding(request, model)
            elif operation == MCPOperationType.CHAT.value:
                return await self._handle_chat(request, model)
            else:
                error_msg = f"Unsupported operation: {operation}"
                logger.error(error_msg)
                return MCPResponse.error_response(
                    request_id=request.request_id,
                    model_id=request.model_id,
                    error_message=error_msg,
                )
        except Exception as e:
            error_msg = f"Error handling request: {e!s}"
            logger.exception(error_msg)
            return MCPResponse.error_response(
                request_id=request.request_id,
                model_id=request.model_id,
                error_message=error_msg,
            )

    @abstractmethod
    async def handle_stream_request(
        self, request: MCPRequest
    ) -> AsyncGenerator[MCPResponse, None]:
        """Handle a streaming request.

        Args:
            request: The request to handle

        Yields:
            Response chunks
        """
        logger.info(
            f"Handling stream request: {request.operation} for model {request.model_id}"
        )

        # Check if model exists
        if request.model_id not in self._models:
            error_msg = f"Model not found: {request.model_id}"
            logger.error(error_msg)
            yield MCPResponse.error_response(
                request_id=request.request_id,
                model_id=request.model_id,
                error_message=error_msg,
            )
            return

        # Check if we have a custom handler for this operation
        operation = (
            request.operation.value
            if isinstance(request.operation, MCPOperationType)
            else request.operation
        )
        if operation in self._stream_handlers:
            try:
                logger.debug(f"Using custom stream handler for operation: {operation}")
                async for response in self._stream_handlers[operation](request):
                    yield response
            except Exception as e:
                error_msg = f"Error in custom stream handler: {e!s}"
                logger.exception(error_msg)
                yield MCPResponse.error_response(
                    request_id=request.request_id,
                    model_id=request.model_id,
                    error_message=error_msg,
                )
            return

        # Otherwise, use the model to handle the request
        try:
            # Default implementation based on operation type
            model = self._models[request.model_id]

            if operation == MCPOperationType.COMPLETION.value:
                async for response in self._handle_stream_completion(request, model):
                    yield response
            elif operation == MCPOperationType.CHAT.value:
                async for response in self._handle_stream_chat(request, model):
                    yield response
            else:
                error_msg = f"Unsupported streaming operation: {operation}"
                logger.error(error_msg)
                yield MCPResponse.error_response(
                    request_id=request.request_id,
                    model_id=request.model_id,
                    error_message=error_msg,
                )
        except Exception as e:
            error_msg = f"Error handling stream request: {e!s}"
            logger.exception(error_msg)
            yield MCPResponse.error_response(
                request_id=request.request_id,
                model_id=request.model_id,
                error_message=error_msg,
            )

    async def get_models(self) -> dict[str, dict[str, Any]]:
        """Get information about registered models.

        Returns:
            A dictionary of model information
        """
        result = {}
        for model_id, model in self._models.items():
            # Get capabilities based on model type
            capabilities = []
            if hasattr(model, "generate") or hasattr(model, "complete"):
                capabilities.append(MCPOperationType.COMPLETION.value)
            if hasattr(model, "chat"):
                capabilities.append(MCPOperationType.CHAT.value)
            if hasattr(model, "embed"):
                capabilities.append(MCPOperationType.EMBEDDING.value)

            # Get provider information if available
            provider = "unknown"
            if hasattr(model, "provider_name"):
                provider = model.provider_name
            elif hasattr(model, "provider_type"):
                provider = model.provider_type

            result[model_id] = {"provider": provider, "capabilities": capabilities}

        return result

    # Helper methods for handling different operation types
    async def _handle_completion(self, request: MCPRequest, model: Any) -> MCPResponse:
        """Handle a completion request.

        Args:
            request: The request to handle
            model: The model to use

        Returns:
            The completion response
        """
        prompt = request.inputs.get("prompt", "")
        params = request.parameters

        # Check which method the model has
        if hasattr(model, "generate"):
            # LLM provider style
            result = await model.generate(prompt, **params)
            return MCPResponse(
                request_id=request.request_id,
                model_id=request.model_id,
                status=MCPStatusCode.SUCCESS,
                outputs={"text": result},
            )
        elif hasattr(model, "complete"):
            # Custom complete method
            result = await model.complete(prompt, **params)
            return MCPResponse(
                request_id=request.request_id,
                model_id=request.model_id,
                status=MCPStatusCode.SUCCESS,
                outputs={"text": result},
            )
        else:
            error_msg = "Model does not support completion"
            logger.error(error_msg)
            return MCPResponse.error_response(
                request_id=request.request_id,
                model_id=request.model_id,
                error_message=error_msg,
            )

    async def _handle_embedding(self, request: MCPRequest, model: Any) -> MCPResponse:
        """Handle an embedding request.

        Args:
            request: The request to handle
            model: The model to use

        Returns:
            The embedding response
        """
        text = request.inputs.get("text", "")
        params = request.parameters

        if hasattr(model, "embed"):
            embedding = await model.embed(text, **params)
            return MCPResponse(
                request_id=request.request_id,
                model_id=request.model_id,
                status=MCPStatusCode.SUCCESS,
                outputs={"embedding": embedding},
            )
        else:
            error_msg = "Model does not support embeddings"
            logger.error(error_msg)
            return MCPResponse.error_response(
                request_id=request.request_id,
                model_id=request.model_id,
                error_message=error_msg,
            )

    async def _handle_chat(self, request: MCPRequest, model: Any) -> MCPResponse:
        """Handle a chat request.

        Args:
            request: The request to handle
            model: The model to use

        Returns:
            The chat response
        """
        messages = request.inputs.get("messages", [])
        params = request.parameters

        if hasattr(model, "chat"):
            result = await model.chat(messages, **params)
            return MCPResponse(
                request_id=request.request_id,
                model_id=request.model_id,
                status=MCPStatusCode.SUCCESS,
                outputs={"message": result},
            )
        else:
            error_msg = "Model does not support chat"
            logger.error(error_msg)
            return MCPResponse.error_response(
                request_id=request.request_id,
                model_id=request.model_id,
                error_message=error_msg,
            )

    async def _handle_stream_completion(
        self, request: MCPRequest, model: Any
    ) -> AsyncGenerator[MCPResponse, None]:
        """Handle a streaming completion request.

        Args:
            request: The request to handle
            model: The model to use

        Yields:
            Completion response chunks
        """
        prompt = request.inputs.get("prompt", "")
        params = request.parameters

        # Check which streaming method the model has
        if hasattr(model, "stream_generate"):
            # LLM provider style
            async for chunk in model.stream_generate(prompt, **params):
                yield MCPResponse(
                    request_id=request.request_id,
                    model_id=request.model_id,
                    status=MCPStatusCode.PARTIAL,
                    outputs={"text": chunk},
                )
        elif hasattr(model, "stream_complete"):
            # Custom stream_complete method
            async for chunk in model.stream_complete(prompt, **params):
                yield MCPResponse(
                    request_id=request.request_id,
                    model_id=request.model_id,
                    status=MCPStatusCode.PARTIAL,
                    outputs={"text": chunk},
                )
        else:
            error_msg = "Model does not support streaming completion"
            logger.error(error_msg)
            yield MCPResponse.error_response(
                request_id=request.request_id,
                model_id=request.model_id,
                error_message=error_msg,
            )

    async def _handle_stream_chat(
        self, request: MCPRequest, model: Any
    ) -> AsyncGenerator[MCPResponse, None]:
        """Handle a streaming chat request.

        Args:
            request: The request to handle
            model: The model to use

        Yields:
            Chat response chunks
        """
        messages = request.inputs.get("messages", [])
        params = request.parameters

        if hasattr(model, "stream_chat"):
            async for chunk in model.stream_chat(messages, **params):
                yield MCPResponse(
                    request_id=request.request_id,
                    model_id=request.model_id,
                    status=MCPStatusCode.PARTIAL,
                    outputs={"message": chunk},
                )
        else:
            error_msg = "Model does not support streaming chat"
            logger.error(error_msg)
            yield MCPResponse.error_response(
                request_id=request.request_id,
                model_id=request.model_id,
                error_message=error_msg,
            )
