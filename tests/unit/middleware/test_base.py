"""
Unit tests for middleware functionality.
"""

import pytest
from typing import Any

from pepperpy.core.utils.errors import ValidationError
from pepperpy.middleware.base import (
    Middleware,
    MiddlewareChain,
    LoggingMiddleware,
    ValidationMiddleware,
)


class TestMiddleware(Middleware):
    """Test middleware implementation."""
    
    def __init__(self, *args, **kwargs) -> None:
        """Initialize the middleware."""
        super().__init__(*args, **kwargs)
        self.processed = False
    
    async def process(self, request: Any, next_handler: Any) -> Any:
        """Process the request."""
        self.processed = True
        return await next_handler(request)


@pytest.mark.asyncio
async def test_middleware_chain():
    """Test middleware chain execution."""
    chain = MiddlewareChain()
    middleware = TestMiddleware()
    chain.add(middleware)
    
    async def handler(request: str) -> str:
        return request.upper()
    
    result = await chain.execute("test", handler)
    assert result == "TEST"
    assert middleware.processed


@pytest.mark.asyncio
async def test_middleware_chain_multiple():
    """Test multiple middleware in chain."""
    chain = MiddlewareChain()
    middleware1 = TestMiddleware()
    middleware2 = TestMiddleware()
    chain.add(middleware1)
    chain.add(middleware2)
    
    async def handler(request: str) -> str:
        return request.upper()
    
    result = await chain.execute("test", handler)
    assert result == "TEST"
    assert middleware1.processed
    assert middleware2.processed


@pytest.mark.asyncio
async def test_middleware_chain_remove():
    """Test removing middleware from chain."""
    chain = MiddlewareChain()
    middleware = TestMiddleware()
    chain.add(middleware)
    chain.remove(middleware)
    
    async def handler(request: str) -> str:
        return request.upper()
    
    result = await chain.execute("test", handler)
    assert result == "TEST"
    assert not middleware.processed


@pytest.mark.asyncio
async def test_logging_middleware(caplog):
    """Test logging middleware."""
    chain = MiddlewareChain()
    middleware = LoggingMiddleware()
    chain.add(middleware)
    
    async def handler(request: str) -> str:
        return request.upper()
    
    result = await chain.execute("test", handler)
    assert result == "TEST"
    
    # Check logs
    assert "Request: test" in caplog.text
    assert "Response: TEST" in caplog.text


@pytest.mark.asyncio
async def test_validation_middleware():
    """Test validation middleware."""
    chain = MiddlewareChain()
    middleware = ValidationMiddleware()
    chain.add(middleware)
    
    async def handler(request: str) -> str:
        return request.upper()
    
    # Test valid request/response
    result = await chain.execute("test", handler)
    assert result == "TEST"
    
    # Test invalid request (mock validation failure)
    middleware._validate_request = lambda x: False  # type: ignore
    with pytest.raises(ValidationError):
        await chain.execute("test", handler)
    
    # Test invalid response (mock validation failure)
    middleware._validate_request = lambda x: True  # type: ignore
    middleware._validate_response = lambda x: False  # type: ignore
    with pytest.raises(ValidationError):
        await chain.execute("test", handler) 