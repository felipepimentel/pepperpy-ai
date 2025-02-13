"""Tests for research workflow functionality."""

import asyncio
from pathlib import Path
from typing import Any, Dict, cast
from unittest.mock import AsyncMock, Mock, patch

import pytest
import yaml

from pepperpy.core.types import (
    Message,
    MessageContent,
    MessageType,
    Response,
    ResponseStatus,
)
from pepperpy.hub import PepperpyHub
from pepperpy.hub.teams import Team


@pytest.fixture
def mock_client():
    """Create a mock client."""
    return Mock()


@pytest.fixture
def mock_agent():
    """Create a mock agent."""
    agent = AsyncMock()
    agent.name = "test-agent"
    agent.process_message = AsyncMock()
    return agent


@pytest.fixture
def hub(mock_client, tmp_path):
    """Create a test hub instance."""
    hub = PepperpyHub(mock_client)
    hub._local_path = tmp_path
    return hub


@pytest.fixture
def research_team_config(tmp_path) -> Path:
    """Create a test research team configuration."""
    config = {
        "name": "research-team",
        "description": "Research team for testing",
        "members": [
            {
                "name": "researcher",
                "role": "researcher",
                "config": {"style": "academic"},
            },
            {"name": "writer", "role": "writer", "config": {"style": "technical"}},
            {"name": "reviewer", "role": "reviewer", "config": {"focus": "accuracy"}},
        ],
        "workflow": "research-flow",
    }

    # Save config file
    team_dir = tmp_path / "teams" / "research-team"
    team_dir.mkdir(parents=True)
    config_file = team_dir / "1.0.0.yaml"
    config_file.write_text(yaml.dump(config))

    return config_file


@pytest.mark.asyncio
async def test_research_workflow(hub, research_team_config, mock_agent):
    """Test the complete research workflow."""
    # Mock agent responses
    research_result: MessageContent = {
        "type": MessageType.RESULT,
        "content": {"findings": "Test findings", "sources": ["source1", "source2"]},
    }
    writing_result: MessageContent = {
        "type": MessageType.RESULT,
        "content": {
            "article": "Test article",
            "sections": ["intro", "body", "conclusion"],
        },
    }
    review_result: MessageContent = {
        "type": MessageType.RESULT,
        "content": {"approved": True, "comments": [], "suggestions": []},
    }

    async def mock_process_message(message: Message) -> Response:
        """Mock agent message processing."""
        content = cast(Dict[str, Any], message.content)
        role = content.get("role")
        if role == "researcher":
            return Response(
                content=research_result,
                message_id="test-1",
                status=ResponseStatus.SUCCESS,
            )
        elif role == "writer":
            return Response(
                content=writing_result,
                message_id="test-2",
                status=ResponseStatus.SUCCESS,
            )
        elif role == "reviewer":
            return Response(
                content=review_result,
                message_id="test-3",
                status=ResponseStatus.SUCCESS,
            )
        return Response(
            content={"type": MessageType.ERROR, "content": {"error": "Unknown role"}},
            message_id="test-error",
            status=ResponseStatus.ERROR,
        )

    # Set up mock agent behavior
    mock_agent.process_message.side_effect = mock_process_message

    # Mock agent loading
    async def mock_agent_loader(name: str, **kwargs):
        return mock_agent

    with patch.object(hub, "agent", side_effect=mock_agent_loader):
        # Load team
        team = await Team.from_config(hub, research_team_config)

        # Execute research workflow
        session = await team.run("Research AI impact")
        async with session:
            result = await session.wait()

            # Verify success
            assert result.success
            assert result.current_status == "Completed"
            assert not result.error

            # Verify results
            assert result.research == research_result["content"]
            assert result.article == writing_result["content"]
            assert result.review == review_result["content"]

            # Verify agent interactions
            assert mock_agent.process_message.call_count == 3

            # Verify message content for each role
            calls = mock_agent.process_message.call_args_list
            researcher_call = cast(Message, calls[0][0][0])
            writer_call = cast(Message, calls[1][0][0])
            reviewer_call = cast(Message, calls[2][0][0])

            researcher_content = cast(Dict[str, Any], researcher_call.content)
            writer_content = cast(Dict[str, Any], writer_call.content)
            reviewer_content = cast(Dict[str, Any], reviewer_call.content)

            assert researcher_content["role"] == "researcher"
            assert researcher_content["config"] == {"style": "academic"}

            assert writer_content["role"] == "writer"
            assert writer_content["config"] == {"style": "technical"}

            assert reviewer_content["role"] == "reviewer"
            assert reviewer_content["config"] == {"focus": "accuracy"}


@pytest.mark.asyncio
async def test_research_workflow_failure(hub, research_team_config, mock_agent):
    """Test research workflow with agent failure."""

    # Mock agent to fail during research
    async def mock_process_message(message: Message) -> Response:
        content = cast(Dict[str, Any], message.content)
        if content.get("role") == "researcher":
            raise Exception("Research failed")
        return Response(
            content={"type": MessageType.RESULT, "content": {"status": "ok"}},
            message_id="test",
            status=ResponseStatus.SUCCESS,
        )

    mock_agent.process_message.side_effect = mock_process_message

    # Mock agent loading
    async def mock_agent_loader(name: str, **kwargs):
        return mock_agent

    with patch.object(hub, "agent", side_effect=mock_agent_loader):
        # Load team
        team = await Team.from_config(hub, research_team_config)

        # Execute research workflow
        session = await team.run("Research AI impact")
        async with session:
            result = await session.wait()

            # Verify failure
            assert not result.success
            assert result.current_status == "Failed"
            assert result.error is not None
            assert str(result.error) == "Research failed"

            # Verify only researcher was called
            assert mock_agent.process_message.call_count == 1

            # Verify no results were stored
            assert result.research is None
            assert result.article is None
            assert result.review is None


@pytest.mark.asyncio
async def test_research_workflow_cancellation(hub, research_team_config, mock_agent):
    """Test cancelling research workflow."""

    # Mock slow agent execution
    async def mock_process_message(message: Message) -> Response:
        await asyncio.sleep(0.1)  # Simulate work
        return Response(
            content={"type": MessageType.RESULT, "content": {"status": "ok"}},
            message_id="test",
            status=ResponseStatus.SUCCESS,
        )

    mock_agent.process_message.side_effect = mock_process_message

    # Mock agent loading
    async def mock_agent_loader(name: str, **kwargs):
        return mock_agent

    with patch.object(hub, "agent", side_effect=mock_agent_loader):
        # Load team
        team = await Team.from_config(hub, research_team_config)

        # Start execution and cancel
        session = await team.run("Research AI impact")
        async with session:
            # Let first agent start
            await asyncio.sleep(0.05)

            # Cancel execution
            await session.cancel()
            result = await session.wait()

            # Verify cancellation
            assert not result.success
            assert result.current_status == "Cancelled"
            assert result.cancelled

            # Verify partial execution
            assert mock_agent.process_message.call_count == 1
