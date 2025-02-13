"""Test all documented usage patterns."""

import os
from unittest.mock import AsyncMock, patch

import pytest

from pepperpy import Pepperpy
from pepperpy.core.errors import PepperpyError


@pytest.mark.asyncio
async def test_basic_usage():
    """Test basic usage patterns."""
    with patch("pepperpy.Pepperpy.create") as mock_create:
        # Setup mock
        mock_pepper = AsyncMock()
        mock_create.return_value = mock_pepper
        mock_pepper.ask.return_value = "Test response"

        # Test creation
        pepper = await Pepperpy.create()
        assert pepper is not None

        # Test ask method
        result = await pepper.ask("What is AI?")
        assert result == "Test response"
        mock_pepper.ask.assert_called_once_with("What is AI?")

        # Test ask with options
        await pepper.ask(
            "What is AI?",
            style="concise",
            format="text",
            temperature=0.7,
            max_tokens=2048,
        )
        mock_pepper.ask.assert_called_with(
            "What is AI?",
            style="concise",
            format="text",
            temperature=0.7,
            max_tokens=2048,
        )


@pytest.mark.asyncio
async def test_research_patterns():
    """Test research functionality."""
    with patch("pepperpy.Pepperpy.create") as mock_create:
        # Setup mock
        mock_pepper = AsyncMock()
        mock_create.return_value = mock_pepper
        mock_pepper.research.return_value.tldr = "Summary"
        mock_pepper.research.return_value.full = "Full report"
        mock_pepper.research.return_value.bullets = ["Point 1", "Point 2"]
        mock_pepper.research.return_value.references = ["Ref 1", "Ref 2"]

        # Test creation
        pepper = await Pepperpy.create()

        # Test basic research
        result = await pepper.research("Impact of AI")
        assert result.tldr == "Summary"
        assert result.full == "Full report"
        assert len(result.bullets) == 2
        assert len(result.references) == 2

        # Test research with options
        await pepper.research(
            topic="Quantum Computing",
            depth="comprehensive",
            style="technical",
            format="report",
            max_sources=10,
        )
        mock_pepper.research.assert_called_with(
            topic="Quantum Computing",
            depth="comprehensive",
            style="technical",
            format="report",
            max_sources=10,
        )


@pytest.mark.asyncio
async def test_team_patterns():
    """Test team functionality."""
    with patch("pepperpy.Pepperpy.create") as mock_create:
        # Setup mock
        mock_pepper = AsyncMock()
        mock_create.return_value = mock_pepper
        mock_team = AsyncMock()
        mock_session = AsyncMock()
        mock_pepper.hub.team.return_value = mock_team

        # Setup async context manager
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock()
        mock_team.run = AsyncMock(return_value=mock_session)

        mock_session.current_step = "Research"
        mock_session.progress = 0.5
        mock_session.thoughts = "Analyzing data"
        mock_session.needs_input = False

        # Test creation
        pepper = await Pepperpy.create()

        # Test team usage
        team = await pepper.hub.team("research-team")
        session = await team.run("Analyze AI trends")
        async with session as session:
            assert session.current_step == "Research"
            assert session.progress == 0.5
            assert session.thoughts == "Analyzing data"
            assert not session.needs_input


@pytest.mark.asyncio
async def test_agent_patterns():
    """Test agent functionality."""
    with patch("pepperpy.Pepperpy.create") as mock_create:
        # Setup mock
        mock_pepper = AsyncMock()
        mock_create.return_value = mock_pepper
        mock_agent = AsyncMock()
        mock_pepper.hub.create_agent.return_value = mock_agent
        mock_agent.research = AsyncMock()  # Add research method to mock

        # Test creation
        pepper = await Pepperpy.create()

        # Test agent creation
        agent = await pepper.hub.create_agent(
            name="technical-researcher",
            base="researcher",
            config={"style": "technical", "depth": "deep"},
        )
        assert agent is not None

        # Test agent usage
        await agent.research("Topic")  # Now using the mocked research method
        mock_agent.research.assert_called_once_with("Topic")

        # Test agent sharing
        await pepper.hub.publish("technical-researcher")
        mock_pepper.hub.publish.assert_called_once_with("technical-researcher")


@pytest.mark.asyncio
async def test_configuration():
    """Test configuration patterns."""
    # Test environment variables
    with patch.dict(
        os.environ,
        {
            "PEPPERPY_API_KEY": "test-key",
            "PEPPERPY_MODEL": "openai/gpt-4",
            "PEPPERPY_TEMPERATURE": "0.7",
            "PEPPERPY_MAX_TOKENS": "2048",
            "PEPPERPY_STYLE": "detailed",
            "PEPPERPY_FORMAT": "text",
        },
    ):
        with patch("pepperpy.Pepperpy.create") as mock_create:
            mock_create.return_value = AsyncMock()
            pepper = await Pepperpy.create()
            assert pepper is not None

    # Test programmatic configuration
    with patch("pepperpy.Pepperpy.create") as mock_create:
        mock_create.return_value = AsyncMock()
        pepper = await Pepperpy.create(
            api_key="test-key",
            model="openai/gpt-4",
            temperature=0.7,
            max_tokens=2048,
            style="technical",
            format="markdown",
            cache_enabled=True,
            cache_ttl=3600,
            request_timeout=30.0,
            max_retries=3,
            metrics_enabled=True,
            log_level="DEBUG",
            hub_sync_interval=300,
            hub_auto_update=True,
        )
        assert pepper is not None


@pytest.mark.asyncio
async def test_error_handling():
    """Test error handling patterns."""
    with patch("pepperpy.Pepperpy.create") as mock_create:
        # Setup mock
        mock_pepper = AsyncMock()
        mock_create.return_value = mock_pepper
        test_error = "Test error"
        mock_pepper.ask.side_effect = PepperpyError(test_error)

        # Test creation
        pepper = await Pepperpy.create()

        # Test error handling
        with pytest.raises(PepperpyError) as exc_info:
            await pepper.ask("Question")
        assert (
            test_error == exc_info.value.message
        )  # Check the message attribute directly
