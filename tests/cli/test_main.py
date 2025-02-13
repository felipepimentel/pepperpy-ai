"""Tests for the main CLI module."""

import pytest
from click.testing import CliRunner

from pepperpy.cli.__main__ import cli


@pytest.fixture
def runner():
    """Create a CLI runner."""
    return CliRunner()


def test_version(runner):
    """Test version command."""
    result = runner.invoke(cli, ["--version"])
    assert result.exit_code == 0
    assert "Pepperpy version" in result.output


def test_init_command(runner, monkeypatch):
    """Test init command."""

    # Mock setup wizard
    def mock_setup(*args, **kwargs):
        return True

    monkeypatch.setattr("pepperpy.cli.setup.setup_wizard", mock_setup)

    # Test successful initialization
    result = runner.invoke(cli, ["init"])
    assert result.exit_code == 0

    # Test keyboard interrupt
    def mock_setup_interrupt(*args, **kwargs):
        raise KeyboardInterrupt()

    monkeypatch.setattr("pepperpy.cli.setup.setup_wizard", mock_setup_interrupt)
    result = runner.invoke(cli, ["init"])
    assert result.exit_code == 1
    assert "Setup cancelled" in result.output

    # Test general error
    def mock_setup_error(*args, **kwargs):
        raise Exception("Test error")

    monkeypatch.setattr("pepperpy.cli.setup.setup_wizard", mock_setup_error)
    result = runner.invoke(cli, ["init"])
    assert result.exit_code == 1
    assert "Setup failed: Test error" in result.output


@pytest.mark.asyncio
async def test_test_command(runner, monkeypatch):
    """Test test command with different options."""

    # Mock Pepperpy class
    class MockPepperpy:
        async def create():
            return MockPepperpy()

        async def ask(self, message, **kwargs):
            return "Test response"

    monkeypatch.setattr("pepperpy.cli.__main__.Pepperpy", MockPepperpy)

    # Test with default options
    result = runner.invoke(cli, ["test", "Hello"])
    assert result.exit_code == 0
    assert "Test response" in result.output

    # Test with custom style and format
    result = runner.invoke(
        cli, ["test", "Hello", "--style", "technical", "--format", "markdown"]
    )
    assert result.exit_code == 0
    assert "Test response" in result.output

    # Test with invalid style
    result = runner.invoke(cli, ["test", "Hello", "--style", "invalid"])
    assert result.exit_code == 2

    # Test with invalid format
    result = runner.invoke(cli, ["test", "Hello", "--format", "invalid"])
    assert result.exit_code == 2


@pytest.mark.asyncio
async def test_doctor_command(runner, monkeypatch):
    """Test doctor command."""

    # Mock diagnostics
    class MockPepperpy:
        async def create():
            return MockPepperpy()

        async def test_connection(self):
            return True

        async def get_models(self):
            return ["model1", "model2"]

    monkeypatch.setattr("pepperpy.cli.__main__.Pepperpy", MockPepperpy)

    # Test successful diagnostics
    result = runner.invoke(cli, ["doctor"])
    assert result.exit_code == 0

    # Test failed connection
    class MockPepperpyFailed:
        async def create():
            return MockPepperpyFailed()

        async def test_connection(self):
            raise Exception("Connection failed")

        async def get_models(self):
            return []

    monkeypatch.setattr("pepperpy.cli.__main__.Pepperpy", MockPepperpyFailed)
    result = runner.invoke(cli, ["doctor"])
    assert result.exit_code == 1
    assert "Connection failed" in result.output


@pytest.mark.asyncio
async def test_research_command(runner, monkeypatch):
    """Test research command with different options."""

    # Mock research functionality
    class MockPepperpy:
        async def create():
            return MockPepperpy()

        async def research(self, topic, **kwargs):
            return {
                "summary": "Test summary",
                "details": "Test details",
                "references": ["ref1", "ref2"],
            }

    monkeypatch.setattr("pepperpy.cli.__main__.Pepperpy", MockPepperpy)

    # Test with default options
    result = runner.invoke(cli, ["research", "AI"])
    assert result.exit_code == 0
    assert "Test summary" in result.output

    # Test with custom options
    result = runner.invoke(
        cli,
        [
            "research",
            "AI",
            "--depth",
            "comprehensive",
            "--style",
            "academic",
            "--format",
            "markdown",
        ],
    )
    assert result.exit_code == 0
    assert "Test summary" in result.output

    # Test with invalid depth
    result = runner.invoke(cli, ["research", "AI", "--depth", "invalid"])
    assert result.exit_code == 2

    # Test with invalid style
    result = runner.invoke(cli, ["research", "AI", "--style", "invalid"])
    assert result.exit_code == 2


@pytest.mark.asyncio
async def test_chat_command(runner, monkeypatch):
    """Test chat command."""

    # Mock chat functionality
    class MockPepperpy:
        async def create():
            return MockPepperpy()

        async def chat(self, message=None, **kwargs):
            return "Chat response"

    monkeypatch.setattr("pepperpy.cli.__main__.Pepperpy", MockPepperpy)

    # Test with message
    result = runner.invoke(cli, ["chat", "Hello"])
    assert result.exit_code == 0
    assert "Chat response" in result.output

    # Test interactive mode
    result = runner.invoke(cli, ["chat"], input="Hello\n")
    assert result.exit_code == 0
    assert "Chat response" in result.output

    # Test with custom style
    result = runner.invoke(cli, ["chat", "Hello", "--style", "technical"])
    assert result.exit_code == 0
    assert "Chat response" in result.output

    # Test with invalid style
    result = runner.invoke(cli, ["chat", "Hello", "--style", "invalid"])
    assert result.exit_code == 2

    # Test keyboard interrupt
    class MockPepperpyInterrupt:
        async def create():
            return MockPepperpyInterrupt()

        async def chat(self, message=None, **kwargs):
            raise KeyboardInterrupt()

    monkeypatch.setattr("pepperpy.cli.__main__.Pepperpy", MockPepperpyInterrupt)
    result = runner.invoke(cli, ["chat", "Hello"])
    assert result.exit_code == 1
    assert "Chat cancelled" in result.output
