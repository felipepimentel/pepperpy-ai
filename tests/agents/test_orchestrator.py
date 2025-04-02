"""Tests for the orchestrator and the unified API interfaces."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from pepperpy.agents.orchestrator import (
    ExecutionContext,
    Orchestrator,
)


@pytest.fixture
def mock_plugin_registry():
    """Fixture to mock the plugin registry for testing."""
    with patch("pepperpy.agents.orchestrator.get_plugins_by_type") as mock_get_plugins:
        # Mock available plugins
        mock_get_plugins.return_value = {
            "general": MagicMock(),
            "question": MagicMock(),
            "default": MagicMock(),
        }
        yield mock_get_plugins


@pytest.fixture
def mock_create_provider():
    """Fixture to mock the provider creation."""
    with patch("pepperpy.agents.orchestrator.create_provider_instance") as mock_create:
        # Setup mock provider
        mock_provider = AsyncMock()
        mock_provider.initialized = False
        mock_provider.initialize = AsyncMock()
        mock_provider.execute = AsyncMock(return_value="Mocked result")
        mock_provider.process = AsyncMock(return_value="Processed content")
        mock_provider.create = AsyncMock(return_value="Created content")
        mock_provider.analyze = AsyncMock(return_value={"analysis": "Analyzed data"})

        mock_create.return_value = mock_provider
        yield mock_create, mock_provider


class TestExecutionContext:
    """Test the ExecutionContext class."""

    def test_init_empty(self):
        """Test initialization with empty data."""
        context = ExecutionContext()
        assert context.as_dict() == {}

    def test_init_with_data(self):
        """Test initialization with data."""
        data = {"key": "value"}
        context = ExecutionContext(data)
        assert context.get("key") == "value"

    def test_get_set(self):
        """Test getting and setting values."""
        context = ExecutionContext()
        context.set("test", "value")
        assert context.get("test") == "value"

    def test_get_default(self):
        """Test getting with default."""
        context = ExecutionContext()
        assert context.get("nonexistent", "default") == "default"

    def test_nested_get_set(self):
        """Test nested getting and setting."""
        context = ExecutionContext()
        context.set("level1.level2.level3", "value")
        assert context.get("level1.level2.level3") == "value"
        assert context.get("level1.level2", {}) == {"level3": "value"}

    def test_update(self):
        """Test update method."""
        context = ExecutionContext({"a": 1})
        context.update({"b": 2, "c": 3})
        assert context.get("a") == 1
        assert context.get("b") == 2
        assert context.get("c") == 3

    def test_cache(self):
        """Test caching."""
        context = ExecutionContext()
        context.cache("key", "value")
        assert context.get_cache("key") == "value"
        assert context.get_cache("nonexistent", "default") == "default"


class TestOrchestrator:
    """Test the Orchestrator class."""

    @pytest.mark.asyncio
    async def test_execute(self, mock_plugin_registry, mock_create_provider):
        """Test the execute method."""
        mock_create, mock_provider = mock_create_provider
        orchestrator = Orchestrator()

        # Test with question intent
        with patch(
            "pepperpy.agents.orchestrator.analyze_intent", return_value="question"
        ):
            result = await orchestrator.execute("What is the capital of France?", {})
            assert result == "Mocked result"
            mock_create.assert_called_with("agent", "question")
            mock_provider.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_process(self, mock_plugin_registry, mock_create_provider):
        """Test the process method."""
        mock_create, mock_provider = mock_create_provider
        orchestrator = Orchestrator()

        with patch(
            "pepperpy.agents.orchestrator.detect_content_type", return_value="text"
        ):
            result = await orchestrator.process(
                "Hello world", "Translate to Spanish", {}
            )
            assert result == "Processed content"
            mock_create.assert_called_with("processor", "text")
            mock_provider.process.assert_called_once()

    @pytest.mark.asyncio
    async def test_create(self, mock_plugin_registry, mock_create_provider):
        """Test the create method."""
        mock_create, mock_provider = mock_create_provider
        orchestrator = Orchestrator()

        result = await orchestrator.create("An image of a cat", "image", {})
        assert result == "Created content"
        mock_create.assert_called_with("creator", "image")
        mock_provider.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_analyze(self, mock_plugin_registry, mock_create_provider):
        """Test the analyze method."""
        mock_create, mock_provider = mock_create_provider
        orchestrator = Orchestrator()

        with patch(
            "pepperpy.agents.orchestrator._detect_data_type", return_value="json"
        ):
            result = await orchestrator.analyze(
                {"data": [1, 2, 3]}, "Find patterns", {}
            )
            assert result == {"analysis": "Analyzed data"}
            mock_create.assert_called_with("analyzer", "json")
            mock_provider.analyze.assert_called_once()

    def test_select_agent_for_intent(self, mock_plugin_registry):
        """Test selecting an agent for an intent."""
        orchestrator = Orchestrator()

        # Test exact match
        assert orchestrator._select_agent_for_intent("general") == "general"

        # Test with supported intents
        with patch("pepperpy.agents.orchestrator.get_plugin_metadata") as mock_metadata:
            mock_metadata.return_value = {"supported_intents": ["create", "process"]}
            assert orchestrator._select_agent_for_intent("create") == "general"

        # Test fallback
        assert orchestrator._select_agent_for_intent("unknown") == "default"


@pytest.mark.asyncio
async def test_pepperpy_integration():
    """Test integration with PepperPy class."""
    from pepperpy import PepperPy

    # Mock the orchestrator
    mock_orchestrator = AsyncMock()
    mock_orchestrator.execute = AsyncMock(return_value="Response from execute")
    mock_orchestrator.process = AsyncMock(return_value="Processed result")
    mock_orchestrator.create = AsyncMock(return_value="Created content")
    mock_orchestrator.analyze = AsyncMock(return_value={"result": "Analysis"})

    with patch("pepperpy.pepperpy.get_orchestrator", return_value=mock_orchestrator):
        # Initialize PepperPy
        pp = PepperPy()

        # Test the high-level API methods
        ask_result = await pp.ask_query("What is AI?")
        assert ask_result == "Response from execute"
        mock_orchestrator.execute.assert_called_once()

        process_result = await pp.process_content("text", "Summarize")
        assert process_result == "Processed result"
        mock_orchestrator.process.assert_called_once()

        create_result = await pp.create_content("A cat image", "image")
        assert create_result == "Created content"
        mock_orchestrator.create.assert_called_once()

        analyze_result = await pp.analyze_data([1, 2, 3], "Find patterns")
        assert analyze_result == {"result": "Analysis"}
        mock_orchestrator.analyze.assert_called_once()


@pytest.mark.asyncio
async def test_convenience_methods():
    """Test the convenience methods in the root module."""
    with patch("pepperpy._instance.ask_query", return_value="Ask response"), patch(
        "pepperpy._instance.process_content", return_value="Process response"
    ), patch(
        "pepperpy._instance.create_content", return_value="Create response"
    ), patch("pepperpy._instance.analyze_data", return_value="Analyze response"):
        # Import the convenience methods
        from pepperpy import analyze, ask, create, process

        # Test each method
        assert await ask("Question") == "Ask response"
        assert await process("Content") == "Process response"
        assert await create("Description") == "Create response"
        assert await analyze("Data", "Instruction") == "Analyze response"
