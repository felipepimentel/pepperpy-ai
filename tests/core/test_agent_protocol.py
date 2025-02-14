"""Tests for AgentProtocol implementation."""

from typing import Any, Dict, Optional
from uuid import UUID, uuid4

import pytest

from pepperpy.core.base import AgentCallback, AgentContext, AgentState


class MockAgent:
    """Mock implementation of AgentProtocol."""

    def __init__(self):
        """Initialize mock agent."""
        self._id = uuid4()
        self._name = "mock_agent"
        self._description = "A mock agent for testing"
        self._version = "1.0.0"
        self._capabilities = ["test", "mock"]
        self._state = AgentState.CREATED
        self._context = AgentContext()
        self._lifecycle_hooks: Dict[AgentState, list[AgentCallback]] = {}

    @property
    def id(self) -> UUID:
        """Get agent ID."""
        return self._id

    @property
    def name(self) -> str:
        """Get agent name."""
        return self._name

    @property
    def description(self) -> str:
        """Get agent description."""
        return self._description

    @property
    def version(self) -> str:
        """Get agent version."""
        return self._version

    @property
    def capabilities(self) -> list[str]:
        """Get agent capabilities."""
        return self._capabilities

    @property
    def state(self) -> AgentState:
        """Get agent state."""
        return self._state

    @property
    def context(self) -> AgentContext:
        """Get agent context."""
        return self._context

    async def initialize(self, config: Dict[str, Any]) -> None:
        """Initialize the agent."""
        self._state = AgentState.INITIALIZING
        # Simulate initialization
        self._state = AgentState.READY

    async def process(
        self,
        input_data: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Process input data."""
        self._state = AgentState.PROCESSING
        # Simulate processing
        result = f"Processed: {input_data}"
        self._state = AgentState.READY
        return result

    async def cleanup(self) -> None:
        """Clean up agent resources."""
        self._state = AgentState.CLEANING
        # Simulate cleanup
        self._state = AgentState.TERMINATED

    def add_lifecycle_hook(
        self,
        state: AgentState,
        callback: AgentCallback,
    ) -> None:
        """Add a lifecycle hook."""
        if state not in self._lifecycle_hooks:
            self._lifecycle_hooks[state] = []
        self._lifecycle_hooks[state].append(callback)

    def remove_lifecycle_hook(
        self,
        state: AgentState,
        callback: AgentCallback,
    ) -> None:
        """Remove a lifecycle hook."""
        if state in self._lifecycle_hooks:
            try:
                self._lifecycle_hooks[state].remove(callback)
            except ValueError:
                pass

    async def validate_state_transition(self, target_state: AgentState) -> None:
        """Validate a state transition."""
        valid_transitions = {
            AgentState.CREATED: [AgentState.INITIALIZING],
            AgentState.INITIALIZING: [AgentState.READY, AgentState.ERROR],
            AgentState.READY: [AgentState.PROCESSING, AgentState.CLEANING],
            AgentState.PROCESSING: [AgentState.READY, AgentState.ERROR],
            AgentState.ERROR: [AgentState.READY, AgentState.CLEANING],
            AgentState.CLEANING: [AgentState.TERMINATED],
        }

        if target_state not in valid_transitions.get(self._state, []):
            raise ValueError(
                f"Invalid state transition: {self._state} -> {target_state}"
            )


@pytest.mark.asyncio
async def test_agent_protocol():
    """Test AgentProtocol implementation."""
    agent = MockAgent()

    # Test properties
    assert isinstance(agent.id, UUID)
    assert agent.name == "mock_agent"
    assert agent.description == "A mock agent for testing"
    assert agent.version == "1.0.0"
    assert agent.capabilities == ["test", "mock"]
    assert agent.state == AgentState.CREATED
    assert isinstance(agent.context, AgentContext)

    # Test initialization
    await agent.initialize({"test": "config"})
    assert agent.state == AgentState.READY

    # Test processing
    result = await agent.process("test_input")
    assert result == "Processed: test_input"
    assert agent.state == AgentState.READY

    # Test lifecycle hooks
    state_changes = []

    async def state_change_hook(agent_id: UUID, new_state: AgentState) -> None:
        state_changes.append((agent_id, new_state))

    agent.add_lifecycle_hook(AgentState.PROCESSING, state_change_hook)
    await agent.process("another_input")
    assert len(state_changes) > 0

    # Test hook removal
    agent.remove_lifecycle_hook(AgentState.PROCESSING, state_change_hook)
    state_changes.clear()
    await agent.process("yet_another_input")
    assert len(state_changes) == 0

    # Test state transitions
    await agent.validate_state_transition(AgentState.PROCESSING)
    with pytest.raises(ValueError):
        await agent.validate_state_transition(AgentState.CREATED)

    # Test cleanup
    await agent.cleanup()
    assert agent.state == AgentState.TERMINATED
