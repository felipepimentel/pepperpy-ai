"""Tests for the pepperpy.core.pipeline.base module."""

from typing import TypeVar

import pytest


# Importe diretamente os itens necessários, evitando importar o módulo inteiro
# que pode ter dependências complexas
class MockPepperpyError(Exception):
    """Mock para PepperpyError para evitar dependências complexas."""

    pass


# Importe apenas o que é necessário do módulo base
from pepperpy.core.pipeline.base import (
    Pipeline,
    PipelineConfig,
    PipelineContext,
    PipelineError,
    PipelineRegistry,
    PipelineStage,
    create_pipeline,
    execute_pipeline,
    get_pipeline,
    register_pipeline,
)

# Type variables for testing
T = TypeVar("T")
U = TypeVar("U")


class TestPipelineContext:
    """Tests for the PipelineContext class."""

    def test_create_context(self):
        """Test creating a pipeline context."""
        context = PipelineContext()
        assert context is not None
        assert context.data == {}
        assert context.metadata == {}

    def test_context_with_initial_data(self):
        """Test creating a context with initial data."""
        initial_data = {"key": "value"}
        context = PipelineContext(data=initial_data)
        assert context.data == initial_data
        assert context.get("key") == "value"

    def test_context_set_get(self):
        """Test setting and getting values from context."""
        context = PipelineContext()
        context.set("test_key", "test_value")
        assert context.get("test_key") == "test_value"
        assert context.get("non_existent") is None
        assert context.get("non_existent", "default") == "default"

    def test_context_set_metadata(self):
        """Test setting and getting metadata."""
        context = PipelineContext()
        context.set_metadata("execution_id", "123")
        assert context.get_metadata("execution_id") == "123"
        context.set_metadata("timestamp", "2023-01-01")
        assert context.get_metadata("timestamp") == "2023-01-01"


class TestPipelineConfig:
    """Tests for the PipelineConfig class."""

    def test_create_config(self):
        """Test creating a pipeline configuration."""
        config = PipelineConfig(name="test_config")
        assert config is not None
        assert config.name == "test_config"
        assert config.options == {}

    def test_config_with_options(self):
        """Test creating a config with initial options."""
        options = {"max_retries": 3, "timeout": 30}
        config = PipelineConfig(name="test_config", options=options)
        assert config.options == options

    def test_config_with_metadata(self):
        """Test config with metadata."""
        metadata = {"version": "1.0", "author": "Test"}
        config = PipelineConfig(name="test_config", metadata=metadata)
        assert config.metadata == metadata


class MockStage(PipelineStage[str, str]):
    """A mock pipeline stage for testing."""

    def __init__(self, transform_func=None, name="mock_stage"):
        """Initialize with an optional transform function."""
        super().__init__(name=name)
        self.transform_func = transform_func or (lambda x, _: x.upper())
        self.process_called = False

    def process(self, input_data: str, context: PipelineContext) -> str:
        """Process the input data by applying the transform function."""
        self.process_called = True
        return self.transform_func(input_data, context)


class FailingStage(PipelineStage[str, str]):
    """A pipeline stage that always raises an exception."""

    def __init__(self, name="failing_stage"):
        """Initialize the failing stage."""
        super().__init__(name=name)

    def process(self, input_data: str, context: PipelineContext) -> str:
        """Raise a PipelineError."""
        raise PipelineError("Intentional failure for testing")


class TestPipelineStage:
    """Tests for the PipelineStage class."""

    def test_stage_process(self):
        """Test the basic stage processing."""
        stage = MockStage(name="test_stage")
        context = PipelineContext()
        result = stage.process("test", context)
        assert result == "TEST"
        assert stage.process_called is True
        assert stage.name == "test_stage"


class TestPipeline:
    """Tests for the Pipeline class."""

    def test_empty_pipeline(self):
        """Test creating an empty pipeline."""
        pipeline = Pipeline[str, str](name="empty")
        assert pipeline.name == "empty"
        assert pipeline.stages == []

    def test_pipeline_with_stages(self):
        """Test creating a pipeline with stages."""
        stage1 = MockStage(lambda x, _: x.upper(), name="upper")
        stage2 = MockStage(lambda x, _: x + "!", name="append")
        pipeline = Pipeline[str, str](name="test", stages=[stage1, stage2])

        assert pipeline.name == "test"
        assert len(pipeline.stages) == 2
        assert pipeline.stages[0] == stage1
        assert pipeline.stages[1] == stage2

    def test_pipeline_execute(self):
        """Test executing a pipeline."""
        stage1 = MockStage(lambda x, _: x.upper(), name="upper")
        stage2 = MockStage(lambda x, _: x + "!", name="append")
        pipeline = Pipeline[str, str](name="test", stages=[stage1, stage2])

        context = PipelineContext()
        result = pipeline.execute("hello", context)

        assert result == "HELLO!"

    def test_pipeline_execute_with_error(self):
        """Test pipeline execution with an error."""
        stage1 = MockStage(name="upper")
        stage2 = FailingStage(name="fail")
        pipeline = Pipeline[str, str](name="failing", stages=[stage1, stage2])

        context = PipelineContext()
        with pytest.raises(PipelineError) as excinfo:
            pipeline.execute("test", context)

        assert "Intentional failure" in str(excinfo.value)

    def test_pipeline_add_stage(self):
        """Test adding stages to a pipeline."""
        pipeline = Pipeline[str, str](name="dynamic")
        assert len(pipeline.stages) == 0

        stage = MockStage(name="new_stage")
        pipeline.add_stage(stage)
        assert len(pipeline.stages) == 1
        assert pipeline.stages[0] == stage


class TestPipelineRegistry:
    """Tests for the pipeline registry functions."""

    def setup_method(self):
        """Set up the test environment."""
        # Reset the registry before each test
        PipelineRegistry._instance = None

    def test_register_and_get_pipeline(self):
        """Test registering and retrieving a pipeline."""
        pipeline = Pipeline[str, str](name="test_registry")

        register_pipeline(pipeline)
        retrieved = get_pipeline("test_registry")

        assert retrieved is not None
        assert retrieved.name == "test_registry"

    def test_get_nonexistent_pipeline(self):
        """Test retrieving a non-existent pipeline."""
        with pytest.raises(PipelineError) as excinfo:
            get_pipeline("non_existent")

        assert "Pipeline not found" in str(excinfo.value)

    def test_create_pipeline(self):
        """Test creating a pipeline with the factory function."""
        stage = MockStage(name="mock")
        pipeline = create_pipeline("factory_test", stages=[stage])

        assert pipeline.name == "factory_test"
        assert len(pipeline.stages) == 1

    def test_execute_pipeline(self):
        """Test executing a pipeline by name."""
        stage = MockStage(lambda x, _: x.upper(), name="upper")
        pipeline = Pipeline[str, str](name="exec_test", stages=[stage])
        register_pipeline(pipeline)

        result = execute_pipeline("exec_test", "hello")
        assert result == "HELLO"

    def test_execute_nonexistent_pipeline(self):
        """Test executing a non-existent pipeline."""
        with pytest.raises(PipelineError) as excinfo:
            execute_pipeline("non_existent", "data")

        assert "Pipeline not found" in str(excinfo.value)


if __name__ == "__main__":
    pytest.main(["-xvs", __file__])
