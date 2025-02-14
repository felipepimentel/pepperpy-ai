"""Tests for agent state management."""

from datetime import datetime, timedelta
from typing import Any, AsyncIterator, Dict, Optional, cast
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from pepperpy.core.agents import BaseAgent
from pepperpy.core.protocols import Memory, MemoryScope
from pepperpy.core.types import (
    Message,
    MessageType,
    Response,
    ResponseStatus,
)
from pepperpy.memory.types import (
    MemoryEntry,
)


class TestAgent(BaseAgent):
    """Test agent implementation."""

    def __init__(
        self, name: str, memory_manager: Optional[Memory[str, Dict[str, Any]]] = None
    ):
        super().__init__(name=name, capabilities=[])
        self._memory_manager = memory_manager
        self.state: Dict[str, Any] = {}

    async def process_message(self, message: Message) -> Response:
        """Process a message."""
        content = cast(Dict[str, Any], message.content)
        command = content.get("command")

        if command == "save_state":
            # Save state
            self.state = content.get("state", {})
            await self._save_state()
            return Response(
                content={"type": MessageType.RESULT, "content": {"saved": True}},
                message_id=str(message.id),
                status=ResponseStatus.SUCCESS,
            )
        elif command == "load_state":
            # Load state
            await self._load_state()
            return Response(
                content={"type": MessageType.RESULT, "content": {"state": self.state}},
                message_id=str(message.id),
                status=ResponseStatus.SUCCESS,
            )
        elif command == "clear_state":
            # Clear state
            await self._clear_state()
            return Response(
                content={"type": MessageType.RESULT, "content": {"cleared": True}},
                message_id=str(message.id),
                status=ResponseStatus.SUCCESS,
            )

        return Response(
            content={
                "type": MessageType.ERROR,
                "content": {"error": "Unknown command"},
            },
            message_id=str(message.id),
            status=ResponseStatus.ERROR,
        )

    async def _save_state(self) -> None:
        """Save agent state to memory."""
        if self._memory_manager:
            await self._memory_manager.store(
                f"{self.name}_state",
                self.state,
                scope=MemoryScope.CONVERSATION,
                expires_at=datetime.utcnow() + timedelta(hours=1),
            )

    async def _load_state(self) -> None:
        """Load agent state from memory."""
        if self._memory_manager:
            try:
                entry = await self._memory_manager.retrieve(f"{self.name}_state")
                self.state = entry.value
            except KeyError:
                self.state = {}

    async def _clear_state(self) -> None:
        """Clear agent state."""
        if self._memory_manager:
            try:
                await self._memory_manager.delete(f"{self.name}_state")
            except KeyError:
                pass
        self.state = {}


class MockMemory(Memory[str, Dict[str, Any]]):
    """Mock memory implementation for testing."""

    def __init__(self) -> None:
        """Initialize mock memory."""
        self.store_mock = AsyncMock()
        self.retrieve_mock = AsyncMock()
        self.delete_mock = AsyncMock()
        self.exists_mock = AsyncMock()
        self.list_mock = AsyncMock()
        self.clear_mock = AsyncMock()

    async def store(
        self,
        key: str,
        value: Dict[str, Any],
        scope: MemoryScope = MemoryScope.SESSION,
        metadata: Optional[Dict[str, Any]] = None,
        expires_at: Optional[datetime] = None,
    ) -> MemoryEntry[Dict[str, Any]]:
        """Store data in memory."""
        return await self.store_mock(key, value, scope, metadata, expires_at)

    async def retrieve(self, key: str) -> MemoryEntry[Dict[str, Any]]:
        """Retrieve data from memory."""
        return await self.retrieve_mock(key)

    async def delete(self, key: str) -> bool:
        """Delete data from memory."""
        return await self.delete_mock(key)

    async def exists(self, key: str) -> bool:
        """Check if key exists in memory."""
        return await self.exists_mock(key)

    async def list(
        self,
        scope: Optional[MemoryScope] = None,
        pattern: Optional[str] = None,
    ) -> AsyncIterator[MemoryEntry[Dict[str, Any]]]:
        """List memory entries."""
        async for entry in self.list_mock(scope, pattern):
            yield entry

    async def clear(self, scope: Optional[MemoryScope] = None) -> int:
        """Clear memory entries."""
        return await self.clear_mock(scope)


@pytest.fixture
def memory_manager():
    """Create a mock memory manager."""
    return MockMemory()


@pytest.fixture
def test_agent(memory_manager):
    """Create a test agent."""
    return TestAgent("test-agent", memory_manager=memory_manager)


@pytest.mark.asyncio
async def test_agent_state_persistence(
    test_agent: TestAgent, memory_manager: MockMemory
):
    """Test agent state persistence."""
    # Test saving state
    test_state = {"key": "value", "count": 42}
    save_message = Message(
        id=uuid4(),
        type=MessageType.COMMAND,
        content={"command": "save_state", "state": test_state},
    )

    # Mock store response
    memory_manager.store_mock.return_value = MemoryEntry(
        key="test-agent_state",
        value=test_state,
        scope=MemoryScope.CONVERSATION,
        created_at=datetime.utcnow(),
    )

    response = await test_agent.process_message(save_message)
    assert response.status == ResponseStatus.SUCCESS
    assert cast(Dict[str, Any], response.content)["content"]["saved"]

    memory_manager.store_mock.assert_called_once()
    store_args = memory_manager.store_mock.call_args
    assert store_args[0][0] == "test-agent_state"
    assert store_args[0][1] == test_state
    assert store_args[0][2] == MemoryScope.CONVERSATION

    # Test loading state
    memory_manager.retrieve_mock.return_value = MemoryEntry(
        key="test-agent_state",
        value=test_state,
        scope=MemoryScope.CONVERSATION,
        created_at=datetime.utcnow(),
    )
    load_message = Message(
        id=uuid4(),
        type=MessageType.COMMAND,
        content={"command": "load_state"},
    )

    response = await test_agent.process_message(load_message)
    assert response.status == ResponseStatus.SUCCESS
    assert cast(Dict[str, Any], response.content)["content"]["state"] == test_state

    memory_manager.retrieve_mock.assert_called_once_with("test-agent_state")


@pytest.mark.asyncio
async def test_agent_state_cleanup(test_agent: TestAgent, memory_manager: MockMemory):
    """Test agent state cleanup."""
    # Set initial state
    test_agent.state = {"key": "value"}

    # Test clearing state
    clear_message = Message(
        id=uuid4(),
        type=MessageType.COMMAND,
        content={"command": "clear_state"},
    )

    memory_manager.delete_mock.return_value = True

    response = await test_agent.process_message(clear_message)
    assert response.status == ResponseStatus.SUCCESS
    assert cast(Dict[str, Any], response.content)["content"]["cleared"]
    assert test_agent.state == {}

    memory_manager.delete_mock.assert_called_once_with("test-agent_state")


@pytest.mark.asyncio
async def test_agent_state_error_handling(
    test_agent: TestAgent, memory_manager: MockMemory
):
    """Test agent state error handling."""
    # Test loading non-existent state
    memory_manager.retrieve_mock.side_effect = KeyError("State not found")
    load_message = Message(
        id=uuid4(),
        type=MessageType.COMMAND,
        content={"command": "load_state"},
    )

    response = await test_agent.process_message(load_message)
    assert response.status == ResponseStatus.SUCCESS
    assert cast(Dict[str, Any], response.content)["content"]["state"] == {}

    # Test clearing non-existent state
    memory_manager.delete_mock.side_effect = KeyError("State not found")
    clear_message = Message(
        id=uuid4(),
        type=MessageType.COMMAND,
        content={"command": "clear_state"},
    )

    response = await test_agent.process_message(clear_message)
    assert response.status == ResponseStatus.SUCCESS
    assert cast(Dict[str, Any], response.content)["content"]["cleared"]


@pytest.mark.asyncio
async def test_agent_without_memory_manager():
    """Test agent behavior without memory manager."""
    agent = TestAgent("test-agent")  # No memory manager

    # Test saving state
    save_message = Message(
        id=uuid4(),
        type=MessageType.COMMAND,
        content={"command": "save_state", "state": {"key": "value"}},
    )

    response = await agent.process_message(save_message)
    assert response.status == ResponseStatus.SUCCESS

    # Test loading state
    load_message = Message(
        id=uuid4(),
        type=MessageType.COMMAND,
        content={"command": "load_state"},
    )

    response = await agent.process_message(load_message)
    assert response.status == ResponseStatus.SUCCESS
    assert cast(Dict[str, Any], response.content)["content"]["state"] == {}
