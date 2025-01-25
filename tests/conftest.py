"""
Pytest configuration and shared fixtures.
"""

import os
from typing import Any, AsyncGenerator, Dict, Generator, List

import pytest

from pepperpy.core.utils.constants import TEMP_DIR
from pepperpy.providers.base.provider import BaseProvider
from pepperpy.capabilities.base.capability import BaseCapability
from pepperpy.middleware.base import MiddlewareChain


@pytest.fixture(scope="session")
def temp_dir() -> Generator[str, None, None]:
    """Create and clean up a temporary directory."""
    os.makedirs(TEMP_DIR, exist_ok=True)
    yield TEMP_DIR
    # Clean up temp files after tests
    for root, dirs, files in os.walk(TEMP_DIR, topdown=False):
        for name in files:
            os.remove(os.path.join(root, name))
        for name in dirs:
            os.rmdir(os.path.join(root, name))


@pytest.fixture
def test_config() -> Dict[str, Any]:
    """Provide test configuration."""
    return {
        "test_mode": True,
        "log_level": "DEBUG",
        "cache_enabled": False,
    }


class TestProvider(BaseProvider):
    """Test provider implementation."""
    
    async def initialize(self) -> None:
        """Initialize the provider."""
        await super().initialize()
    
    async def shutdown(self) -> None:
        """Shutdown the provider."""
        await super().shutdown()


class TestCapability(BaseCapability[str, str]):
    """Test capability implementation."""
    
    async def initialize(self) -> None:
        """Initialize the capability."""
        await super().initialize()
    
    async def _initialize_impl(self) -> None:
        """Initialize implementation."""
        pass
    
    async def _cleanup_impl(self) -> None:
        """Clean up implementation."""
        pass
    
    async def _execute(self, input_data: str) -> str:
        """Execute the capability."""
        return input_data.upper()
    
    async def validate_input(self, input_data: str) -> None:
        """Validate input data."""
        if not isinstance(input_data, str):
            raise ValueError("Input must be a string")
    
    async def validate_output(self, output_data: str) -> None:
        """Validate output data."""
        if not isinstance(output_data, str):
            raise ValueError("Output must be a string")
            
    async def get_metadata(self) -> Dict[str, Any]:
        """Get capability metadata."""
        return {
            "name": self.name,
            "version": "1.0.0",
            "description": "Test capability for unit tests"
        }
        
    async def get_dependencies(self) -> List[str]:
        """Get capability dependencies."""
        return []
        
    async def get_required_providers(self) -> List[str]:
        """Get required providers."""
        return []
        
    async def get_supported_inputs(self) -> Dict[str, Any]:
        """Get supported input parameters."""
        return {"input": "string"}
        
    async def get_supported_outputs(self) -> Dict[str, Any]:
        """Get supported output parameters."""
        return {"output": "string"}


@pytest.fixture
async def initialized_provider(test_config: Dict[str, Any]) -> AsyncGenerator[TestProvider, None]:
    """Provide an initialized test provider."""
    provider = TestProvider(config=test_config)
    await provider.initialize()
    yield provider
    await provider.shutdown()


@pytest.fixture
async def initialized_capability(test_config: Dict[str, Any]) -> AsyncGenerator[TestCapability, None]:
    """Provide an initialized test capability."""
    capability = TestCapability(config=test_config)
    await capability.initialize()
    yield capability


@pytest.fixture
def middleware_chain() -> Generator[MiddlewareChain, None, None]:
    """Provide a middleware chain."""
    chain = MiddlewareChain()
    yield chain 