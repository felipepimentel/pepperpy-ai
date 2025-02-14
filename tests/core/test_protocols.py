"""Tests for the Protocol System.

This module contains tests for the Protocol System, including:
- Protocol validation and registration
- Protocol implementation verification
- Protocol error handling
- Protocol lifecycle management
"""

from typing import Any, Dict, List, Optional, Protocol, runtime_checkable
from uuid import uuid4

import pytest

from pepperpy.core.types import (
    AgentCapability,
    AgentConfig,
    AgentContext,
    AgentState,
)


@runtime_checkable
class TestProtocol(Protocol):
    """Test protocol for capability verification."""

    name: str
    version: str
    description: str

    def validate(self) -> bool:
        """Validate protocol implementation."""
        ...

    async def initialize(self, config: Dict[str, Any]) -> None:
        """Initialize protocol with configuration."""
        ...

    async def cleanup(self) -> None:
        """Clean up protocol resources."""
        ...


class TestCapability(AgentCapability):
    """Test implementation of AgentCapability."""

    def __init__(
        self,
        name: str = "test_capability",
        version: str = "1.0.0",
        description: str = "Test capability",
        requirements: Optional[List[str]] = None,
    ) -> None:
        """Initialize test capability."""
        self._name = name
        self._version = version
        self._description = description
        self._requirements = requirements or []
        self._initialized = False

    @property
    def name(self) -> str:
        """Get capability name."""
        return self._name

    @property
    def version(self) -> str:
        """Get capability version."""
        return self._version

    @property
    def description(self) -> str:
        """Get capability description."""
        return self._description

    @property
    def requirements(self) -> List[str]:
        """Get capability requirements."""
        return self._requirements

    def is_available(self) -> bool:
        """Check if capability is available."""
        return True

    async def initialize(self, config: Dict[str, Any]) -> None:
        """Initialize capability."""
        self._initialized = True

    async def cleanup(self) -> None:
        """Clean up capability."""
        self._initialized = False

    @property
    def is_initialized(self) -> bool:
        """Check if capability is initialized."""
        return self._initialized


class InvalidCapability:
    """Invalid capability that doesn't implement the protocol."""

    def __init__(self) -> None:
        """Initialize invalid capability."""
        self.name = "invalid"


def test_protocol_validation():
    """Test protocol validation."""
    # Test valid capability
    capability = TestCapability()
    assert isinstance(capability, AgentCapability)

    # Test invalid capability
    invalid = InvalidCapability()
    assert not isinstance(invalid, AgentCapability)


def test_capability_properties():
    """Test capability properties."""
    name = "test_capability"
    version = "1.0.0"
    description = "Test capability"
    requirements = ["req1", "req2"]

    capability = TestCapability(
        name=name,
        version=version,
        description=description,
        requirements=requirements,
    )

    assert capability.name == name
    assert capability.version == version
    assert capability.description == description
    assert capability.requirements == requirements
    assert capability.is_available()
    assert not capability.is_initialized


@pytest.mark.asyncio
async def test_capability_lifecycle():
    """Test capability lifecycle."""
    capability = TestCapability()
    config = {"key": "value"}

    # Test initialization
    assert not capability.is_initialized
    await capability.initialize(config)
    assert capability.is_initialized

    # Test cleanup
    await capability.cleanup()
    assert not capability.is_initialized


@pytest.mark.asyncio
async def test_capability_error_handling():
    """Test capability error handling."""

    class ErrorCapability(TestCapability):
        """Capability that raises errors."""

        async def initialize(self, config: Dict[str, Any]) -> None:
            """Raise error during initialization."""
            raise ValueError("Initialization error")

        async def cleanup(self) -> None:
            """Raise error during cleanup."""
            raise ValueError("Cleanup error")

    capability = ErrorCapability()

    # Test initialization error
    with pytest.raises(ValueError, match="Initialization error"):
        await capability.initialize({})

    # Test cleanup error
    with pytest.raises(ValueError, match="Cleanup error"):
        await capability.cleanup()


def test_capability_requirements():
    """Test capability requirements validation."""
    # Test with no requirements
    capability = TestCapability()
    assert capability.requirements == []

    # Test with requirements
    requirements = ["req1", "req2"]
    capability = TestCapability(requirements=requirements)
    assert capability.requirements == requirements

    # Test requirement validation
    assert all(req in capability.requirements for req in requirements)


@pytest.mark.asyncio
async def test_capability_configuration():
    """Test capability configuration."""

    class ConfigCapability(TestCapability):
        """Capability that stores configuration."""

        async def initialize(self, config: Dict[str, Any]) -> None:
            """Store configuration."""
            await super().initialize(config)
            self.config = config

    config = {"key1": "value1", "key2": {"nested": "value2"}}

    capability = ConfigCapability()
    await capability.initialize(config)

    assert capability.is_initialized
    assert capability.config == config


@pytest.mark.asyncio
async def test_capability_in_agent_context():
    """Test capability usage in agent context."""

    class TestAgent:
        """Test agent implementation."""

        def __init__(self, capability: AgentCapability) -> None:
            """Initialize test agent."""
            self.capability = capability
            self.config = AgentConfig(
                type="test",
                name="test_agent",
                description="Test agent",
                version="1.0.0",
                capabilities=[capability.name],
            )
            self.context = AgentContext(
                agent_id=uuid4(),
                session_id=uuid4(),
                parent_id=None,
                state=AgentState.CREATED,
                settings={},
                metadata={},
            )

        async def initialize(self) -> None:
            """Initialize agent and capability."""
            await self.capability.initialize(self.config.settings)

        async def cleanup(self) -> None:
            """Clean up agent and capability."""
            await self.capability.cleanup()

    capability = TestCapability()
    agent = TestAgent(capability)

    # Test initialization
    await agent.initialize()
    assert capability.is_initialized

    # Test cleanup
    await agent.cleanup()
    assert not capability.is_initialized
