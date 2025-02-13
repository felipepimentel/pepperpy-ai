"""Tests for Hub team functionality."""

import asyncio
from pathlib import Path
from typing import Generator
from unittest.mock import patch

import pytest
import yaml

from pepperpy.hub import Hub
from pepperpy.hub.types import Team, TeamConfig, TeamMember, TeamRole


@pytest.fixture
def temp_hub_dir(tmp_path) -> Generator[Path, None, None]:
    """Create a temporary hub directory."""
    yield tmp_path


@pytest.fixture
def hub(temp_hub_dir):
    """Create a test hub instance."""
    return Hub(storage_dir=temp_hub_dir)


@pytest.fixture
def test_team_config() -> TeamConfig:
    """Create a test team configuration."""
    return TeamConfig(
        name="research-team",
        description="Research team for testing",
        members=[
            TeamMember(
                name="researcher",
                role=TeamRole.RESEARCHER,
                config={"style": "academic"},
            ),
            TeamMember(
                name="writer", role=TeamRole.WRITER, config={"style": "technical"}
            ),
            TeamMember(
                name="reviewer", role=TeamRole.REVIEWER, config={"focus": "accuracy"}
            ),
        ],
        workflow="research-flow",
    )


@pytest.mark.asyncio
async def test_team_creation(hub, test_team_config, temp_hub_dir):
    """Test creating a new team."""
    # Save team configuration
    team_dir = temp_hub_dir / "teams" / "research-team"
    team_dir.mkdir(parents=True)
    team_file = team_dir / "1.0.0.yaml"
    team_file.write_text(yaml.dump(test_team_config.model_dump()))

    # Load team
    team = await hub.load_team("research-team")
    assert isinstance(team, Team)
    assert team.name == "research-team"
    assert len(team.members) == 3
    assert any(m.role == TeamRole.RESEARCHER for m in team.members)
    assert any(m.role == TeamRole.WRITER for m in team.members)
    assert any(m.role == TeamRole.REVIEWER for m in team.members)


@pytest.mark.asyncio
async def test_team_execution(hub, test_team_config, temp_hub_dir):
    """Test team execution workflow."""
    # Mock agent responses
    research_result = {"findings": "Test findings"}
    writing_result = {"article": "Test article"}
    review_result = {"approved": True, "comments": []}

    class MockAgent:
        def __init__(self, role):
            self.role = role
            self.config = {}

        async def execute(self, task):
            if self.role == TeamRole.RESEARCHER:
                return research_result
            elif self.role == TeamRole.WRITER:
                return writing_result
            elif self.role == TeamRole.REVIEWER:
                return review_result

    # Mock agent loading
    async def mock_load_agent(name, version=None):
        for member in test_team_config.members:
            if member.name == name:
                return MockAgent(member.role)
        raise ValueError(f"Agent {name} not found")

    with patch.object(hub, "load_agent", side_effect=mock_load_agent):
        # Save and load team
        team_dir = temp_hub_dir / "teams" / "research-team"
        team_dir.mkdir(parents=True)
        team_file = team_dir / "1.0.0.yaml"
        team_file.write_text(yaml.dump(test_team_config.model_dump()))

        team = await hub.load_team("research-team")

        # Execute team workflow
        async with team.run("Research AI impact") as session:
            result = await session.wait()

            assert result.success
            assert result.research == research_result
            assert result.article == writing_result
            assert result.review == review_result


@pytest.mark.asyncio
async def test_team_monitoring(hub, test_team_config, temp_hub_dir):
    """Test team execution monitoring."""

    # Mock long-running agent execution
    class MockAgent:
        def __init__(self, role):
            self.role = role
            self.config = {}

        async def execute(self, task):
            # Simulate work with progress updates
            for i in range(5):
                self.last_status = f"Step {i + 1}/5"
                await asyncio.sleep(0.1)
            return {"status": "completed"}

        def get_status(self):
            return getattr(self, "last_status", "Not started")

    # Mock agent loading
    async def mock_load_agent(name, version=None):
        for member in test_team_config.members:
            if member.name == name:
                return MockAgent(member.role)
        raise ValueError(f"Agent {name} not found")

    with patch.object(hub, "load_agent", side_effect=mock_load_agent):
        # Save and load team
        team_dir = temp_hub_dir / "teams" / "research-team"
        team_dir.mkdir(parents=True)
        team_file = team_dir / "1.0.0.yaml"
        team_file.write_text(yaml.dump(test_team_config.model_dump()))

        team = await hub.load_team("research-team")

        # Execute and monitor
        status_updates = []
        async with team.run("Research AI impact") as session:
            while not session.done:
                status = session.current_status
                status_updates.append(status)
                await asyncio.sleep(0.1)

            result = await session.wait()
            assert result.success

            # Verify we got status updates
            assert len(status_updates) > 0
            assert any("Step" in status for status in status_updates)


@pytest.mark.asyncio
async def test_team_error_handling(hub, test_team_config, temp_hub_dir):
    """Test team error handling."""

    # Mock failing agent
    class MockAgent:
        def __init__(self, role):
            self.role = role
            self.config = {}

        async def execute(self, task):
            if self.role == TeamRole.RESEARCHER:
                raise Exception("Research failed")
            return {"status": "completed"}

    # Mock agent loading
    async def mock_load_agent(name, version=None):
        for member in test_team_config.members:
            if member.name == name:
                return MockAgent(member.role)
        raise ValueError(f"Agent {name} not found")

    with patch.object(hub, "load_agent", side_effect=mock_load_agent):
        # Save and load team
        team_dir = temp_hub_dir / "teams" / "research-team"
        team_dir.mkdir(parents=True)
        team_file = team_dir / "1.0.0.yaml"
        team_file.write_text(yaml.dump(test_team_config.model_dump()))

        team = await hub.load_team("research-team")

        # Execute and verify error handling
        async with team.run("Research AI impact") as session:
            result = await session.wait()

            assert not result.success
            assert "Research failed" in str(result.error)
            assert session.current_status == "Failed"


@pytest.mark.asyncio
async def test_team_cancellation(hub, test_team_config, temp_hub_dir):
    """Test team execution cancellation."""

    # Mock long-running agent
    class MockAgent:
        def __init__(self, role):
            self.role = role
            self.config = {}

        async def execute(self, task):
            try:
                await asyncio.sleep(10)  # Long operation
                return {"status": "completed"}
            except asyncio.CancelledError:
                return {"status": "cancelled"}

    # Mock agent loading
    async def mock_load_agent(name, version=None):
        for member in test_team_config.members:
            if member.name == name:
                return MockAgent(member.role)
        raise ValueError(f"Agent {name} not found")

    with patch.object(hub, "load_agent", side_effect=mock_load_agent):
        # Save and load team
        team_dir = temp_hub_dir / "teams" / "research-team"
        team_dir.mkdir(parents=True)
        team_file = team_dir / "1.0.0.yaml"
        team_file.write_text(yaml.dump(test_team_config.model_dump()))

        team = await hub.load_team("research-team")

        # Start execution and cancel
        async with team.run("Research AI impact") as session:
            await asyncio.sleep(0.1)  # Let it start
            await session.cancel()

            result = await session.wait()
            assert not result.success
            assert result.cancelled
            assert session.current_status == "Cancelled"
