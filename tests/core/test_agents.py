"""Tests for the BaseAgent class.

This module contains tests for the BaseAgent class, including:
- Agent initialization and configuration
- Lifecycle management (initialize, cleanup)
- State transitions and validation
- Event handling and notifications
- Error handling and recovery
- Concurrent operations
"""

import asyncio
from typing import Any, Dict, List, Optional
from unittest.mock import AsyncMock, Mock

import pytest

from pepperpy.core.agents import BaseAgent
from pepperpy.core.errors import ValidationError
from pepperpy.core.events import Event, EventBus, EventType
from pepperpy.core.types import (
    AgentState,
    Message,
    MessageContent,
    MessageType,
    Response,
    ResponseStatus,
)


class TestAgent(BaseAgent):
    """Test implementation of BaseAgent."""

    def __init__(
        self,
        name: str,
        capabilities: Optional[List[str]] = None,
        config: Optional[Dict[str, Any]] = None,
        event_bus: Optional[EventBus] = None,
    ) -> None:
        """Initialize test agent."""
        super().__init__(name=name, capabilities=capabilities or [], config=config)
        self.event_bus = event_bus or Mock(spec=EventBus)
        self.initialized = False
        self.cleaned_up = False
        self._state = AgentState.CREATED

    @property
    def state(self) -> AgentState:
        """Get the current agent state."""
        return self._state

    async def initialize(self) -> None:
        """Initialize the agent."""
        self._state = AgentState.INITIALIZING
        self.initialized = True
        self._state = AgentState.READY
        if self.event_bus:
            await self.event_bus.publish(
                Event(
                    type=EventType.AGENT_CREATED,
                    source_id=self.name,
                    data={"agent": self.name},
                )
            )

    async def cleanup(self) -> None:
        """Clean up agent resources."""
        self._state = AgentState.CLEANING
        self.cleaned_up = True
        self._state = AgentState.TERMINATED
        if self.event_bus:
            await self.event_bus.publish(
                Event(
                    type=EventType.AGENT_REMOVED,
                    source_id=self.name,
                    data={"agent": self.name},
                )
            )

    async def analyze(
        self,
        query: str,
        depth: str = "comprehensive",
        style: str = "technical",
        **kwargs: Any,
    ) -> str:
        """Test implementation of analyze."""
        if self._state != AgentState.READY:
            raise ValidationError("Agent not ready")
        self._state = AgentState.PROCESSING
        try:
            result = f"Analyzed {query} with depth={depth} and style={style}"
            self._state = AgentState.READY
            return result
        except Exception:
            self._state = AgentState.ERROR
            raise

    async def process_message(self, message: Message) -> Response:
        """Process a message and return a response."""
        try:
            if message.metadata and message.metadata.get("type") == "analyze":
                result = await self.analyze(str(message.content))
                return Response(
                    message_id=str(message.id),
                    content=MessageContent(
                        type=MessageType.RESPONSE,
                        content={"result": result},
                    ),
                    status=ResponseStatus.SUCCESS,
                )
            else:
                return Response(
                    message_id=str(message.id),
                    content=MessageContent(
                        type=MessageType.ERROR,
                        content={"error": "Unknown message type"},
                    ),
                    status=ResponseStatus.ERROR,
                )
        except Exception as e:
            return Response(
                message_id=str(message.id),
                content=MessageContent(
                    type=MessageType.ERROR,
                    content={"error": str(e)},
                ),
                status=ResponseStatus.ERROR,
            )


@pytest.fixture
def event_bus():
    """Create a mock event bus."""
    return AsyncMock(spec=EventBus)


@pytest.fixture
def test_agent(event_bus) -> BaseAgent:
    """Create a test agent."""
    return TestAgent(
        name="test_agent",
        capabilities=["analyze", "research"],
        config={"style": "technical", "depth": "comprehensive"},
        event_bus=event_bus,
    )


def test_agent_initialization():
    """Test agent initialization."""
    name = "test_agent"
    capabilities = ["analyze", "research"]
    config = {"style": "technical"}

    agent = TestAgent(name=name, capabilities=capabilities, config=config)

    assert agent.name == name
    assert agent.capabilities == capabilities
    assert agent.config == config
    assert agent.state == AgentState.CREATED


def test_agent_initialization_default_config():
    """Test agent initialization with default config."""
    agent = TestAgent(name="test", capabilities=["analyze"])
    assert agent.config == {}


@pytest.mark.asyncio
async def test_agent_lifecycle(test_agent: TestAgent, event_bus: AsyncMock):
    """Test agent lifecycle management."""
    # Test initialization
    assert test_agent.state == AgentState.CREATED
    await test_agent.initialize()
    assert test_agent.initialized
    assert test_agent.state == AgentState.READY
    event_bus.publish.assert_called_once()
    assert event_bus.publish.call_args[0][0].type == EventType.AGENT_CREATED

    # Test cleanup
    event_bus.publish.reset_mock()
    await test_agent.cleanup()
    assert test_agent.cleaned_up
    assert test_agent.state == AgentState.TERMINATED
    event_bus.publish.assert_called_once()
    assert event_bus.publish.call_args[0][0].type == EventType.AGENT_REMOVED


@pytest.mark.asyncio
async def test_agent_state_transitions(test_agent: TestAgent):
    """Test agent state transitions."""
    # Test valid transitions
    assert test_agent.state == AgentState.CREATED
    await test_agent.initialize()
    assert test_agent.state == AgentState.READY

    result = await test_agent.analyze("test")
    assert "Analyzed test" in result
    assert test_agent.state == AgentState.READY

    await test_agent.cleanup()
    assert test_agent.state == AgentState.TERMINATED

    # Test invalid operations
    with pytest.raises(ValidationError):
        await test_agent.analyze("test")  # Can't analyze after termination


@pytest.mark.asyncio
async def test_agent_error_handling(test_agent: TestAgent):
    """Test agent error handling."""
    await test_agent.initialize()

    # Test validation error
    with pytest.raises(ValidationError):
        test_agent._state = AgentState.ERROR
        await test_agent.analyze("test")

    # Test recovery from error
    test_agent._state = AgentState.READY
    result = await test_agent.analyze("test")
    assert "Analyzed test" in result
    assert test_agent.state == AgentState.READY


@pytest.mark.asyncio
async def test_agent_concurrent_operations(test_agent: TestAgent):
    """Test concurrent agent operations."""
    await test_agent.initialize()

    # Test concurrent analysis
    async def analyze(query: str) -> str:
        return await test_agent.analyze(query)

    results = await asyncio.gather(*[analyze(f"query_{i}") for i in range(5)])

    assert len(results) == 5
    assert all("Analyzed query_" in result for result in results)
    assert test_agent.state == AgentState.READY


@pytest.mark.asyncio
async def test_agent_analyze():
    """Test agent analyze method."""
    agent = TestAgent(name="test", capabilities=["analyze"])
    await agent.initialize()
    result = await agent.analyze("test query", depth="brief", style="casual")
    assert result == "Analyzed test query with depth=brief and style=casual"
    assert agent.state == AgentState.READY


def test_agent_has_capability(test_agent: BaseAgent):
    """Test has_capability method."""
    assert test_agent.has_capability("analyze")
    assert test_agent.has_capability("research")
    assert not test_agent.has_capability("unknown")


def test_agent_validate_capabilities(test_agent: BaseAgent):
    """Test validate_capabilities method."""
    assert test_agent.validate_capabilities(["analyze"])
    assert test_agent.validate_capabilities(["analyze", "research"])
    assert not test_agent.validate_capabilities(["unknown"])
    assert not test_agent.validate_capabilities(["analyze", "unknown"])


def test_agent_get_config(test_agent: BaseAgent):
    """Test get_config method."""
    assert test_agent.get_config("style") == "technical"
    assert test_agent.get_config("depth") == "comprehensive"
    assert test_agent.get_config("unknown") is None
    assert test_agent.get_config("unknown", "default") == "default"


@pytest.mark.asyncio
async def test_agent_message_handling(test_agent: TestAgent):
    """Test agent message handling."""
    await test_agent.initialize()

    # Test valid message
    message = Message(
        content="Test message",
        type=MessageType.QUERY,
        metadata={"type": "analyze"},
    )
    response = await test_agent.process_message(message)
    assert isinstance(response, Response)
    assert response.status == ResponseStatus.SUCCESS
    assert test_agent.state == AgentState.READY

    # Test invalid message
    message = Message(
        content="Test message",
        type=MessageType.QUERY,
        metadata={"type": "unknown"},
    )
    response = await test_agent.process_message(message)
    assert isinstance(response, Response)
    assert response.status == ResponseStatus.ERROR
    assert test_agent.state == AgentState.READY
