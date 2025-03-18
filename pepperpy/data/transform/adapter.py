"""Adapter for migrating transform pipeline to the unified pipeline framework.

This module provides adapter classes that bridge between the existing transform
pipeline implementation and the new unified pipeline framework.
"""

from typing import Any, List, Optional, TypeVar, Union

from pepperpy.core.pipeline.base import (
    Pipeline,
    PipelineConfig,
    PipelineContext,
    PipelineStage,
)
from pepperpy.data.errors import TransformError, ValidationError
from pepperpy.data.transform import Transform, get_transform
from pepperpy.data.validation import (
    ValidationHook,
    ValidationLevel,
    ValidationStage,
)

# Type variables for data types
T = TypeVar("T")
U = TypeVar("U")


class ValidationStageAdapter(PipelineStage[Any, Any]):
    """Adapter for validation stages to use the new pipeline framework."""

    def __init__(
        self,
        name: str,
        hooks: List[ValidationHook],
        stage: ValidationStage,
        fail_fast: bool = True,
    ):
        """Initialize the adapter.

        Args:
            name: The name of the stage
            hooks: The validation hooks to apply
            stage: The validation stage (pre_transform, post_transform, intermediate)
            fail_fast: Whether to stop validation after the first failure
        """
        super().__init__(name=name)
        self._hooks = hooks
        self._stage = stage
        self._fail_fast = fail_fast

    async def process(self, data: Any, context: PipelineContext) -> Any:
        """Process data.

        Args:
            data: The data to process
            context: The pipeline context

        Returns:
            The processed data

        Raises:
            ValidationError: If validation fails and fail_fast is True
        """
        # Create a dict for the old implementation
        context_dict = {}
        for key in context.data.keys():
            context_dict[key] = context.get(key)
        for key in context.metadata.keys():
            context_dict[key] = context.get_metadata(key)
        context_dict["validation_stage"] = self._stage

        # Apply each validation hook
        all_errors = {}
        for hook in self._hooks:
            result = hook.validate(data, context_dict)
            if not result.is_valid:
                # Add errors from this hook
                for key, value in result.errors.items():
                    all_errors[f"{hook.validator.name}.{key}"] = value

                # Stop validation if fail_fast is True
                if self._fail_fast:
                    break

        # Raise an error if validation failed and fail_fast is True
        if all_errors and self._fail_fast:
            error_message = f"Validation failed at stage '{self.name}': {', '.join(f'{k}: {v}' for k, v in all_errors.items())}"
            raise ValidationError(
                message=error_message,
                details={"errors": all_errors, "stage": self.name},
            )

        # Add validation errors to the context
        if not context.get("validation_errors"):
            context.set("validation_errors", {})
        validation_errors = context.get("validation_errors")
        validation_errors[self.name] = all_errors
        context.set("validation_errors", validation_errors)

        # Return the data
        return data


class TransformStageAdapter(PipelineStage[Any, Any]):
    """Adapter for transform stages to use the new pipeline framework."""

    def __init__(
        self,
        name: str,
        transform: Union[Transform, str],
        pre_hooks: Optional[List[ValidationHook]] = None,
        post_hooks: Optional[List[ValidationHook]] = None,
        fail_fast: bool = True,
    ):
        """Initialize the adapter.

        Args:
            name: The name of the stage
            transform: The transform to apply, either as a Transform object or the name of a registered transform
            pre_hooks: The validation hooks to apply before transformation
            post_hooks: The validation hooks to apply after transformation
            fail_fast: Whether to stop validation after the first failure
        """
        super().__init__(name=name)
        self._transform = transform
        self._pre_hooks = pre_hooks or []
        self._post_hooks = post_hooks or []
        self._fail_fast = fail_fast

    async def process(self, data: Any, context: PipelineContext) -> Any:
        """Process data.

        Args:
            data: The data to process
            context: The pipeline context

        Returns:
            The processed data

        Raises:
            TransformError: If there is an error processing the data
            ValidationError: If validation fails and fail_fast is True
        """
        try:
            # Create a dict for the old implementation
            context_dict = {}
            for key in context.data.keys():
                context_dict[key] = context.get(key)
            for key in context.metadata.keys():
                context_dict[key] = context.get_metadata(key)

            # Apply pre-validation
            if self._pre_hooks:
                pre_validation = ValidationStageAdapter(
                    f"{self.name}_pre_validation",
                    self._pre_hooks,
                    ValidationStage.PRE_TRANSFORM,
                    self._fail_fast,
                )
                data = await pre_validation.process(data, context)

            # Get the transform
            transform_obj = self._transform
            if isinstance(transform_obj, str):
                transform_obj = get_transform(transform_obj)

            # Apply the transform
            result = transform_obj.transform(data)

            # Apply post-validation
            if self._post_hooks:
                post_validation = ValidationStageAdapter(
                    f"{self.name}_post_validation",
                    self._post_hooks,
                    ValidationStage.POST_TRANSFORM,
                    self._fail_fast,
                )
                result = await post_validation.process(result, context)

            # Update the context
            context.set("last_stage", self.name)
            context.set("last_result", result)

            return result
        except ValidationError as e:
            # Re-raise validation errors
            raise e
        except TransformError as e:
            # Add context to transform errors
            raise TransformError(
                f"Error in stage '{self.name}': {e}",
                transform_name=self.name,
            )
        except Exception as e:
            # Convert other exceptions to TransformError
            raise TransformError(
                f"Error in stage '{self.name}': {e}",
                transform_name=self.name,
            )


class TransformPipelineAdapter(Pipeline[Any, Any]):
    """Adapter for transform pipelines to use the new pipeline framework."""

    def __init__(
        self,
        name: str,
        stages: List[PipelineStage[Any, Any]],
        intermediate_hooks: Optional[List[ValidationHook]] = None,
        validation_levels: Optional[List[ValidationLevel]] = None,
    ):
        """Initialize the adapter.

        Args:
            name: The name of the pipeline
            stages: The stages to apply
            intermediate_hooks: The validation hooks to apply between stages
            validation_levels: The validation levels to enable
        """
        # Create intermediate validation stages if needed
        all_stages = []
        for i, stage in enumerate(stages):
            all_stages.append(stage)
            if intermediate_hooks and i < len(stages) - 1:
                intermediate_stage = ValidationStageAdapter(
                    f"{name}_intermediate_{i}",
                    intermediate_hooks,
                    ValidationStage.INTERMEDIATE,
                    True,
                )
                all_stages.append(intermediate_stage)

        # Create the pipeline config
        config = PipelineConfig(
            name=name,
            description="Transform Pipeline",
            metadata={
                "type": "transform",
                "validation_levels": [
                    level.value
                    for level in (validation_levels or [ValidationLevel.STANDARD])
                ],
            },
        )

        # Initialize the pipeline
        super().__init__(
            name=name,
            stages=all_stages,
            config=config,
        )


class TransformPipelineBuilderAdapter:
    """Builder for creating transform pipeline adapters."""

    def __init__(self):
        """Initialize the builder."""
        self._name = None
        self._stages = []
        self._intermediate_hooks = []
        self._validation_levels = [ValidationLevel.STANDARD]

    def with_name(self, name: str) -> "TransformPipelineBuilderAdapter":
        """Set the pipeline name.

        Args:
            name: The name of the pipeline

        Returns:
            The builder instance
        """
        self._name = name
        return self

    def with_transform(
        self,
        name: str,
        transform: Union[Transform, str],
        pre_hooks: Optional[List[ValidationHook]] = None,
        post_hooks: Optional[List[ValidationHook]] = None,
        fail_fast: bool = True,
    ) -> "TransformPipelineBuilderAdapter":
        """Add a transform stage.

        Args:
            name: The name of the stage
            transform: The transform to apply
            pre_hooks: The validation hooks to apply before transformation
            post_hooks: The validation hooks to apply after transformation
            fail_fast: Whether to stop validation after the first failure

        Returns:
            The builder instance
        """
        stage = TransformStageAdapter(
            name=name,
            transform=transform,
            pre_hooks=pre_hooks,
            post_hooks=post_hooks,
            fail_fast=fail_fast,
        )
        self._stages.append(stage)
        return self

    def with_intermediate_validation(
        self, hooks: List[ValidationHook]
    ) -> "TransformPipelineBuilderAdapter":
        """Add intermediate validation hooks.

        Args:
            hooks: The validation hooks to apply between stages

        Returns:
            The builder instance
        """
        self._intermediate_hooks.extend(hooks)
        return self

    def with_validation_levels(
        self, levels: List[ValidationLevel]
    ) -> "TransformPipelineBuilderAdapter":
        """Set the validation levels.

        Args:
            levels: The validation levels to enable

        Returns:
            The builder instance
        """
        self._validation_levels = levels
        return self

    def build(self) -> TransformPipelineAdapter:
        """Build the pipeline.

        Returns:
            The constructed pipeline

        Raises:
            ValueError: If the pipeline name is not set or no stages are added
        """
        if not self._name:
            raise ValueError("Pipeline name must be set")
        if not self._stages:
            raise ValueError("At least one stage must be added")

        return TransformPipelineAdapter(
            name=self._name,
            stages=self._stages,
            intermediate_hooks=self._intermediate_hooks,
            validation_levels=self._validation_levels,
        )
