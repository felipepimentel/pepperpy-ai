"""Test fixtures for capabilities testing."""

from typing import Any, Dict

import pytest
from pydantic import BaseModel

from pepperpy.core.capabilities import (
    Capability,
    CapabilityError,
    CapabilityResult,
    CapabilityType,
)


class TestCapabilityConfig(BaseModel):
    """Test configuration model."""

    name: str = "test"
    value: int = 42
    metadata: Dict[str, Any] = {}


class MockCapability(Capability[TestCapabilityConfig]):
    """Mock capability for testing."""

    def __init__(self, type: CapabilityType, config: TestCapabilityConfig) -> None:
        super().__init__(type, config)
        self.initialize_called = False
        self.cleanup_called = False
        self.validate_called = False
        self.execute_called = False
        self.execute_result = CapabilityResult(success=True)

    async def initialize(self) -> None:
        """Initialize the mock capability."""
        self.initialize_called = True
        await super().initialize()

    async def cleanup(self) -> None:
        """Clean up the mock capability."""
        self.cleanup_called = True
        await super().cleanup()

    async def validate(self) -> None:
        """Validate the mock capability."""
        self.validate_called = True
        await super().validate()

    async def execute(self, **kwargs: Any) -> CapabilityResult:
        """Execute the mock capability."""
        self.execute_called = True
        self.execute_kwargs = kwargs
        return self.execute_result


class ErrorCapability(MockCapability):
    """Mock capability that raises errors."""

    def __init__(
        self,
        type: CapabilityType,
        config: TestCapabilityConfig,
        *,
        error_type: str = "initialize",
    ) -> None:
        super().__init__(type, config)
        self.error_type = error_type

    async def initialize(self) -> None:
        """Initialize with error."""
        if self.error_type == "initialize":
            raise CapabilityError(
                "Initialization failed",
                self.type,
                details={"error": "test error"},
            )
        await super().initialize()

    async def validate(self) -> None:
        """Validate with error."""
        if self.error_type == "validate":
            raise CapabilityError(
                "Validation failed",
                self.type,
                details={"error": "test error"},
            )
        await super().validate()

    async def execute(self, **kwargs: Any) -> CapabilityResult:
        """Execute with error."""
        if self.error_type == "execute":
            raise CapabilityError(
                "Execution failed",
                self.type,
                details={"error": "test error"},
            )
        return await super().execute(**kwargs)


@pytest.fixture
def test_config() -> TestCapabilityConfig:
    """Provide test configuration."""
    return TestCapabilityConfig()


@pytest.fixture
def mock_capability(test_config: TestCapabilityConfig) -> MockCapability:
    """Provide mock capability instance."""
    return MockCapability(CapabilityType.TOOLS, test_config)


@pytest.fixture
def error_capability(test_config: TestCapabilityConfig) -> ErrorCapability:
    """Provide error-raising capability instance."""
    return ErrorCapability(CapabilityType.TOOLS, test_config)
