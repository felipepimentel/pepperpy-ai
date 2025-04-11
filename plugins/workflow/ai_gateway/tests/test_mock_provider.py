"""Tests for the mock model provider."""

from typing import Any, cast

import pytest

from pepperpy.core.base import PepperpyError
from pepperpy.core.types import ComponentType
from plugins.workflow.ai_gateway.adapter import AIGatewayAdapter
from plugins.workflow.ai_gateway.gateway import GatewayRequest
from plugins.workflow.ai_gateway.run_mesh import MockModelProvider, create_mock_provider


@pytest.mark.asyncio
async def test_mock_provider_direct():
    """Test mock provider functionality directly."""
    # Given
    provider = await create_mock_provider()
    assert provider is not None
    provider = cast(MockModelProvider, provider)

    # When
    await provider.initialize()

    try:
        # Then
        assert provider.get_model_id() == "mock-model"
        assert provider.temperature == 0.7
        assert provider.max_tokens == 1000
    finally:
        await provider.cleanup()


@pytest.mark.asyncio
async def test_mock_provider_chat():
    """Test mock provider chat functionality."""
    # Given
    provider = await create_mock_provider()
    assert provider is not None
    provider = cast(MockModelProvider, provider)
    await provider.initialize()

    try:
        # When
        request = GatewayRequest(
            request_id="test-1",
            operation="chat",
            inputs={"messages": [{"role": "user", "content": "Test message"}]},
            target=ComponentType.MODEL,
        )
        response = await provider.execute(request)

        # Then
        assert response.success
        assert "message" in response.outputs
        assert "usage" in response.outputs
        assert response.outputs["model"] == "mock-model"
    finally:
        await provider.cleanup()


@pytest.mark.asyncio
async def test_adapter_workflow():
    """Test adapter workflow functionality."""
    # Given
    adapter = AIGatewayAdapter()

    # When
    await adapter.initialize()

    try:
        # Then
        result = await adapter.execute({
            "operation": "chat",
            "messages": [{"role": "user", "content": "Test message"}],
        })

        assert result["success"]
        assert "outputs" in result
        assert "message" in result["outputs"]
    finally:
        await adapter.cleanup()


@pytest.mark.asyncio
async def test_adapter_error_handling():
    """Test adapter error handling."""
    # Given
    adapter = AIGatewayAdapter()
    await adapter.initialize()

    try:
        # When/Then
        with pytest.raises(PepperpyError):
            await adapter.execute({
                "operation": "invalid",
                "messages": [{"role": "user", "content": "Test message"}],
            })
    finally:
        await adapter.cleanup()


@pytest.mark.asyncio
async def test_provider_configuration():
    """Test provider configuration."""
    # Given
    config: dict[str, Any] = {
        "model_id": "custom-model",
        "temperature": 0.5,
        "max_tokens": 2000,
    }

    # When
    provider = MockModelProvider(**config)
    await provider.initialize()

    try:
        # Then
        assert provider.model_id == "custom-model"
        assert provider.temperature == 0.5
        assert provider.max_tokens == 2000
    finally:
        await provider.cleanup()


@pytest.mark.asyncio
async def test_provider_cleanup():
    """Test provider cleanup behavior."""
    # Given
    provider = await create_mock_provider()
    assert provider is not None
    provider = cast(MockModelProvider, provider)

    # When
    await provider.initialize()
    assert provider.initialized
    await provider.cleanup()

    # Then
    assert not provider.initialized
