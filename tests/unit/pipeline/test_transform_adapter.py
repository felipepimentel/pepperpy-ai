"""Tests for the transform pipeline adapter."""

import asyncio
import unittest
from typing import Any, Dict, Optional

from pepperpy.core.pipeline.base import PipelineContext
from pepperpy.data.errors import TransformError, ValidationError
from pepperpy.data.transform import Transform, TransformType
from pepperpy.data.transform.adapter import (
    TransformPipelineAdapter,
    TransformPipelineBuilderAdapter,
    TransformStageAdapter,
    ValidationStageAdapter,
)
from pepperpy.data.validation import (
    ValidationHook,
    ValidationLevel,
    ValidationResult,
    ValidationStage,
    Validator,
)


class MockTransform(Transform):
    """Mock transform for testing."""

    def __init__(self, name: str = "mock_transform"):
        """Initialize the mock transform."""
        self._name = name

    @property
    def name(self) -> str:
        """Get the name of the transform."""
        return self._name

    @property
    def transform_type(self) -> TransformType:
        """Get the transform type."""
        return TransformType.CLASS

    def transform(self, data: Any) -> Any:
        """Transform the data."""
        if isinstance(data, str):
            return data.upper()
        if isinstance(data, int):
            return data * 2
        if isinstance(data, list):
            return [self.transform(item) for item in data]
        return data

    def to_dict(self) -> Dict[str, Any]:
        """Convert the transform to a dictionary."""
        return {
            "name": self.name,
            "type": self.transform_type.value,
        }


class MockValidator(Validator):
    """Mock validator for testing."""

    def __init__(self, name: str = "mock_validator", should_fail: bool = False):
        """Initialize the mock validator."""
        self._name = name
        self._should_fail = should_fail

    @property
    def name(self) -> str:
        """Get the name of the validator."""
        return self._name

    def validate(
        self, data: Any, context: Optional[Dict[str, Any]] = None
    ) -> ValidationResult:
        """Validate the data."""
        if self._should_fail:
            return ValidationResult(
                is_valid=False,
                errors={"mock_error": "Mock validation error"},
            )
        return ValidationResult(is_valid=True)


class TestValidationStageAdapter(unittest.TestCase):
    """Tests for the ValidationStageAdapter."""

    def setUp(self):
        """Set up test fixtures."""
        self.validator = MockValidator()
        self.hook = ValidationHook(self.validator, ValidationStage.PRE_TRANSFORM)
        self.stage = ValidationStageAdapter(
            name="test_validation",
            hooks=[self.hook],
            stage=ValidationStage.PRE_TRANSFORM,
            fail_fast=True,
        )

    def test_init(self):
        """Test initialization."""
        self.assertEqual(self.stage.name, "test_validation")
        self.assertEqual(len(self.stage._hooks), 1)
        self.assertEqual(self.stage._stage, ValidationStage.PRE_TRANSFORM)
        self.assertTrue(self.stage._fail_fast)

    def test_process_success(self):
        """Test successful validation."""
        context = PipelineContext()
        result = asyncio.run(self.stage.process("test data", context))
        self.assertEqual(result, "test data")
        self.assertEqual(context.get("validation_errors"), {"test_validation": {}})

    def test_process_failure(self):
        """Test validation failure."""
        failing_validator = MockValidator(should_fail=True)
        failing_hook = ValidationHook(failing_validator, ValidationStage.PRE_TRANSFORM)
        failing_stage = ValidationStageAdapter(
            name="test_validation",
            hooks=[failing_hook],
            stage=ValidationStage.PRE_TRANSFORM,
            fail_fast=True,
        )

        context = PipelineContext()
        with self.assertRaises(ValidationError):
            asyncio.run(failing_stage.process("test data", context))


class TestTransformStageAdapter(unittest.TestCase):
    """Tests for the TransformStageAdapter."""

    def setUp(self):
        """Set up test fixtures."""
        self.transform = MockTransform()
        self.validator = MockValidator()
        self.pre_hook = ValidationHook(self.validator, ValidationStage.PRE_TRANSFORM)
        self.post_hook = ValidationHook(self.validator, ValidationStage.POST_TRANSFORM)
        self.stage = TransformStageAdapter(
            name="test_transform",
            transform=self.transform,
            pre_hooks=[self.pre_hook],
            post_hooks=[self.post_hook],
            fail_fast=True,
        )

    def test_init(self):
        """Test initialization."""
        self.assertEqual(self.stage.name, "test_transform")
        self.assertEqual(self.stage._transform, self.transform)
        self.assertEqual(len(self.stage._pre_hooks), 1)
        self.assertEqual(len(self.stage._post_hooks), 1)
        self.assertTrue(self.stage._fail_fast)

    def test_process_success(self):
        """Test successful transformation."""
        context = PipelineContext()
        result = asyncio.run(self.stage.process("test data", context))
        self.assertEqual(result, "TEST DATA")
        self.assertEqual(context.get("last_stage"), "test_transform")
        self.assertEqual(context.get("last_result"), "TEST DATA")

    def test_process_validation_failure(self):
        """Test transformation with validation failure."""
        failing_validator = MockValidator(should_fail=True)
        failing_hook = ValidationHook(failing_validator, ValidationStage.PRE_TRANSFORM)
        failing_stage = TransformStageAdapter(
            name="test_transform",
            transform=self.transform,
            pre_hooks=[failing_hook],
            fail_fast=True,
        )

        context = PipelineContext()
        with self.assertRaises(ValidationError):
            asyncio.run(failing_stage.process("test data", context))

    def test_process_transform_error(self):
        """Test transformation error."""

        class FailingTransform(MockTransform):
            def transform(self, data: Any) -> Any:
                raise ValueError("Mock transform error")

        failing_stage = TransformStageAdapter(
            name="test_transform",
            transform=FailingTransform(),
        )

        context = PipelineContext()
        with self.assertRaises(TransformError):
            asyncio.run(failing_stage.process("test data", context))


class TestTransformPipelineAdapter(unittest.TestCase):
    """Tests for the TransformPipelineAdapter."""

    def setUp(self):
        """Set up test fixtures."""
        self.transform1 = MockTransform("transform1")
        self.transform2 = MockTransform("transform2")
        self.validator = MockValidator()
        self.hook = ValidationHook(self.validator, ValidationStage.INTERMEDIATE)

        # Create stages
        self.stage1 = TransformStageAdapter(
            name="stage1",
            transform=self.transform1,
        )
        self.stage2 = TransformStageAdapter(
            name="stage2",
            transform=self.transform2,
        )

        # Create pipeline
        self.pipeline = TransformPipelineAdapter(
            name="test_pipeline",
            stages=[self.stage1, self.stage2],
            intermediate_hooks=[self.hook],
            validation_levels=[ValidationLevel.STANDARD],
        )

    def test_init(self):
        """Test initialization."""
        self.assertEqual(self.pipeline.name, "test_pipeline")
        self.assertEqual(
            len(self.pipeline.stages), 3
        )  # 2 transform stages + 1 intermediate validation
        self.assertEqual(self.pipeline.config.name, "test_pipeline")
        self.assertEqual(self.pipeline.config.metadata["type"], "transform")
        self.assertEqual(
            self.pipeline.config.metadata["validation_levels"],
            [ValidationLevel.STANDARD.value],
        )

    def test_execute_success(self):
        """Test successful pipeline execution."""
        context = PipelineContext()
        result = asyncio.run(self.pipeline.execute_async("test data", context))
        self.assertEqual(result, "TEST DATA")
        self.assertEqual(context.get("last_stage"), "stage2")
        self.assertEqual(context.get("last_result"), "TEST DATA")


class TestTransformPipelineBuilderAdapter(unittest.TestCase):
    """Tests for the TransformPipelineBuilderAdapter."""

    def setUp(self):
        """Set up test fixtures."""
        self.builder = TransformPipelineBuilderAdapter()
        self.transform = MockTransform()
        self.validator = MockValidator()
        self.hook = ValidationHook(self.validator, ValidationStage.INTERMEDIATE)

    def test_with_name(self):
        """Test setting pipeline name."""
        builder = self.builder.with_name("test_pipeline")
        self.assertEqual(builder._name, "test_pipeline")

    def test_with_transform(self):
        """Test adding transform stage."""
        builder = self.builder.with_transform(
            name="test_transform",
            transform=self.transform,
            pre_hooks=[self.hook],
            post_hooks=[self.hook],
        )
        self.assertEqual(len(builder._stages), 1)
        self.assertEqual(builder._stages[0].name, "test_transform")

    def test_with_intermediate_validation(self):
        """Test adding intermediate validation."""
        builder = self.builder.with_intermediate_validation([self.hook])
        self.assertEqual(len(builder._intermediate_hooks), 1)

    def test_with_validation_levels(self):
        """Test setting validation levels."""
        builder = self.builder.with_validation_levels([ValidationLevel.STRICT])
        self.assertEqual(builder._validation_levels, [ValidationLevel.STRICT])

    def test_build_success(self):
        """Test successful pipeline build."""
        pipeline = (
            self.builder.with_name("test_pipeline")
            .with_transform("stage1", self.transform)
            .with_transform("stage2", self.transform)
            .with_intermediate_validation([self.hook])
            .with_validation_levels([ValidationLevel.STRICT])
            .build()
        )

        self.assertEqual(pipeline.name, "test_pipeline")
        self.assertEqual(
            len(pipeline.stages), 3
        )  # 2 transform stages + 1 intermediate validation
        self.assertEqual(pipeline.config.metadata["type"], "transform")
        self.assertEqual(
            pipeline.config.metadata["validation_levels"],
            [ValidationLevel.STRICT.value],
        )

    def test_build_error_no_name(self):
        """Test build error when name is not set."""
        with self.assertRaises(ValueError):
            self.builder.build()

    def test_build_error_no_stages(self):
        """Test build error when no stages are added."""
        with self.assertRaises(ValueError):
            self.builder.with_name("test_pipeline").build()
