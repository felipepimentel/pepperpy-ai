"""Tests for event handlers.

This module contains tests for:
- Agent event handlers
- Workflow event handlers
- Memory event handlers
- Hub event handlers
"""

from uuid import uuid4

import pytest

from pepperpy.core.events import (
    AgentCreatedEvent,
    AgentEventHandler,
    AgentRemovedEvent,
    AgentStateChangedEvent,
    Event,
    EventPriority,
    EventType,
    HubAssetCreatedEvent,
    HubAssetDeletedEvent,
    HubAssetUpdatedEvent,
    HubEventHandler,
    MemoryEventHandler,
    MemoryRetrievedEvent,
    MemoryStoredEvent,
    MemoryUpdatedEvent,
    WorkflowCompletedEvent,
    WorkflowEventHandler,
    WorkflowFailedEvent,
    WorkflowStartedEvent,
)


@pytest.fixture
def agent_handler():
    """Create agent event handler fixture."""
    return AgentEventHandler()


@pytest.fixture
def workflow_handler():
    """Create workflow event handler fixture."""
    return WorkflowEventHandler()


@pytest.fixture
def memory_handler():
    """Create memory event handler fixture."""
    return MemoryEventHandler()


@pytest.fixture
def hub_handler():
    """Create hub event handler fixture."""
    return HubEventHandler()


async def test_agent_event_handler(agent_handler):
    """Test agent event handler."""
    # Test agent created event
    agent_id = uuid4()
    created_event = AgentCreatedEvent(
        agent_id=agent_id,
        agent_name="test_agent",
    )
    await agent_handler.handle_event(created_event)

    # Test agent removed event
    removed_event = AgentRemovedEvent(
        agent_id=agent_id,
        agent_name="test_agent",
    )
    await agent_handler.handle_event(removed_event)

    # Test agent state changed event
    state_event = AgentStateChangedEvent(
        agent_id=agent_id,
        agent_name="test_agent",
        previous_state="idle",
        new_state="running",
    )
    await agent_handler.handle_event(state_event)

    # Test invalid event type
    invalid_event = Event(
        event_type="invalid.event",
        priority=EventPriority.NORMAL,
    )
    await agent_handler.handle_event(invalid_event)


async def test_workflow_event_handler(workflow_handler):
    """Test workflow event handler."""
    # Test workflow started event
    workflow_id = uuid4()
    started_event = WorkflowStartedEvent(
        workflow_id=workflow_id,
        workflow_name="test_workflow",
    )
    await workflow_handler.handle_event(started_event)

    # Test workflow completed event
    completed_event = WorkflowCompletedEvent(
        workflow_id=workflow_id,
        workflow_name="test_workflow",
    )
    await workflow_handler.handle_event(completed_event)

    # Test workflow failed event
    failed_event = WorkflowFailedEvent(
        workflow_id=workflow_id,
        workflow_name="test_workflow",
        error="Test error",
        error_type="ValueError",
    )
    await workflow_handler.handle_event(failed_event)

    # Test invalid event type
    invalid_event = Event(
        event_type="invalid.event",
        priority=EventPriority.NORMAL,
    )
    await workflow_handler.handle_event(invalid_event)


async def test_memory_event_handler(memory_handler):
    """Test memory event handler."""
    # Test memory stored event
    memory_id = uuid4()
    stored_event = MemoryStoredEvent(
        memory_id=memory_id,
        memory_type="test_memory",
    )
    await memory_handler.handle_event(stored_event)

    # Test memory retrieved event
    retrieved_event = MemoryRetrievedEvent(
        memory_id=memory_id,
        memory_type="test_memory",
    )
    await memory_handler.handle_event(retrieved_event)

    # Test memory updated event
    updated_event = MemoryUpdatedEvent(
        memory_id=memory_id,
        memory_type="test_memory",
    )
    await memory_handler.handle_event(updated_event)

    # Test invalid event type
    invalid_event = Event(
        event_type="invalid.event",
        priority=EventPriority.NORMAL,
    )
    await memory_handler.handle_event(invalid_event)


async def test_hub_event_handler(hub_handler):
    """Test hub event handler."""
    # Test hub asset created event
    asset_id = uuid4()
    created_event = HubAssetCreatedEvent(
        hub_name="test_hub",
        asset_id=asset_id,
        asset_type="test_asset",
        asset_name="test_asset.txt",
    )
    await hub_handler.handle_event(created_event)

    # Test hub asset updated event
    updated_event = HubAssetUpdatedEvent(
        hub_name="test_hub",
        asset_id=asset_id,
        asset_type="test_asset",
        asset_name="test_asset.txt",
    )
    await hub_handler.handle_event(updated_event)

    # Test hub asset deleted event
    deleted_event = HubAssetDeletedEvent(
        hub_name="test_hub",
        asset_id=asset_id,
        asset_type="test_asset",
        asset_name="test_asset.txt",
    )
    await hub_handler.handle_event(deleted_event)

    # Test invalid event type
    invalid_event = Event(
        event_type="invalid.event",
        priority=EventPriority.NORMAL,
    )
    await hub_handler.handle_event(invalid_event)


def test_event_type_values():
    """Test event type values."""
    # Test agent event types
    assert EventType.AGENT_CREATED == "agent.created"
    assert EventType.AGENT_REMOVED == "agent.removed"
    assert EventType.AGENT_STATE_CHANGED == "agent.state.changed"

    # Test workflow event types
    assert EventType.WORKFLOW_STARTED == "workflow.started"
    assert EventType.WORKFLOW_COMPLETED == "workflow.completed"
    assert EventType.WORKFLOW_FAILED == "workflow.failed"

    # Test memory event types
    assert EventType.MEMORY_STORED == "memory.stored"
    assert EventType.MEMORY_RETRIEVED == "memory.retrieved"
    assert EventType.MEMORY_UPDATED == "memory.updated"

    # Test hub event types
    assert EventType.HUB_ASSET_CREATED == "hub.asset.created"
    assert EventType.HUB_ASSET_UPDATED == "hub.asset.updated"
    assert EventType.HUB_ASSET_DELETED == "hub.asset.deleted"
