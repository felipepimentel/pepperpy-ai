"""Legacy pipeline adapter for the transform module.

This module provides adapters to help migrate from the legacy pipeline implementation
in pepperpy.data.transform to the new unified pipeline framework.
"""

from typing import Any, Dict

from pepperpy.core.pipeline.base import Pipeline as NewPipeline
from pepperpy.core.pipeline.base import PipelineContext, PipelineStage
from pepperpy.data.transform import Pipeline as LegacyPipeline
from pepperpy.data.transform import Transform, TransformError


class LegacyPipelineAdapter(NewPipeline[Any, Any]):
    """Adapter to wrap a legacy pipeline in the new pipeline interface.

    This adapter allows existing code using the legacy Pipeline class to
    gradually migrate to the new unified pipeline framework by providing
    a compatibility layer.

    Example:
        >>> from pepperpy.data.transform import Pipeline as LegacyPipeline
        >>> from pepperpy.data.transform import FunctionTransform
        >>>
        >>> # Create a legacy pipeline
        >>> legacy = LegacyPipeline()
        >>> legacy.add_stage(FunctionTransform("double", lambda x: x * 2))
        >>>
        >>> # Wrap it in the adapter
        >>> pipeline = LegacyPipelineAdapter(legacy, "legacy_pipeline")
        >>>
        >>> # Use it with the new interface
        >>> context = PipelineContext()
        >>> result = await pipeline.execute(2, context)
        >>> assert result == 4
    """

    def __init__(self, legacy_pipeline: LegacyPipeline, name: str):
        """Initialize the adapter.

        Args:
            legacy_pipeline: The legacy pipeline to wrap
            name: Name for the new pipeline
        """
        super().__init__(name)
        self._legacy_pipeline = legacy_pipeline

    async def _execute_impl(self, data: Any, context: PipelineContext) -> Any:
        """Execute the legacy pipeline with the new interface.

        Args:
            data: Input data to process
            context: Pipeline execution context

        Returns:
            The transformed data

        Raises:
            TransformError: If any stage fails
        """
        try:
            return self._legacy_pipeline.execute(data)
        except Exception as e:
            raise TransformError(f"Error in legacy pipeline: {e}")

    def to_dict(self) -> Dict[str, Any]:
        """Convert the pipeline to a dictionary representation.

        Returns:
            Dict containing the pipeline configuration
        """
        legacy_dict = self._legacy_pipeline.to_dict()
        return {
            "name": self.name,
            "type": "legacy_adapter",
            "legacy_pipeline": legacy_dict,
        }


class LegacyTransformStage(PipelineStage[Any, Any]):
    """Adapter to wrap a legacy transform in the new pipeline stage interface.

    This adapter allows existing transforms to be used in the new pipeline
    framework by wrapping them in a compatible stage interface.

    Example:
        >>> from pepperpy.data.transform import FunctionTransform
        >>> from pepperpy.core.pipeline.base import Pipeline
        >>>
        >>> # Create a legacy transform
        >>> transform = FunctionTransform("double", lambda x: x * 2)
        >>>
        >>> # Wrap it in the adapter
        >>> stage = LegacyTransformStage("double_stage", transform)
        >>>
        >>> # Use it in a new pipeline
        >>> pipeline = Pipeline("new_pipeline")
        >>> pipeline.add_stage(stage)
        >>>
        >>> context = PipelineContext()
        >>> result = await pipeline.execute(2, context)
        >>> assert result == 4
    """

    def __init__(self, name: str, transform: Transform):
        """Initialize the adapter.

        Args:
            name: Name for the stage
            transform: The legacy transform to wrap
        """
        super().__init__(name)
        self._transform = transform

    async def _execute_impl(self, data: Any, context: PipelineContext) -> Any:
        """Execute the legacy transform with the new interface.

        Args:
            data: Input data to process
            context: Pipeline execution context

        Returns:
            The transformed data

        Raises:
            TransformError: If the transform fails
        """
        try:
            return self._transform.transform(data)
        except Exception as e:
            raise TransformError(
                f"Error in legacy transform {self._transform.name}: {e}"
            )

    def to_dict(self) -> Dict[str, Any]:
        """Convert the stage to a dictionary representation.

        Returns:
            Dict containing the stage configuration
        """
        transform_dict = self._transform.to_dict()
        return {
            "name": self.name,
            "type": "legacy_transform",
            "transform": transform_dict,
        }
