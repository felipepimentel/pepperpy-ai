"""Data transformation pipeline with validation hooks.

This module provides a data transformation pipeline that integrates with
validation hooks to validate data at various stages of transformation.
"""

from typing import Any, Dict, List, Optional, TypeVar, Union

from pepperpy.data.errors import TransformError, ValidationError
from pepperpy.data.transform import (
    Pipeline,
    PipelineStage,
    Transform,
    get_transform,
)
from pepperpy.data.validation import (
    ValidationHook,
    ValidationLevel,
    ValidationStage,
    Validator,
    get_validator,
)
from pepperpy.utils.logging import get_logger

# Logger for this module
logger = get_logger(__name__)

# Type variables for data types
T = TypeVar("T")
U = TypeVar("U")


class ValidationStageAdapter(PipelineStage):
    """Pipeline stage that applies validation hooks.

    This stage applies validation hooks to data.
    """

    def __init__(
        self,
        name: str,
        hooks: List[ValidationHook],
        stage: ValidationStage,
        fail_fast: bool = True,
    ):
        """Initialize a validation stage.

        Args:
            name: The name of the stage
            hooks: The validation hooks to apply
            stage: The validation stage (pre_transform, post_transform, intermediate)
            fail_fast: Whether to stop validation after the first failure
        """
        self._name = name
        self._hooks = hooks
        self._stage = stage
        self._fail_fast = fail_fast

    @property
    def name(self) -> str:
        """Get the name of the stage.

        Returns:
            The name of the stage
        """
        return self._name

    def process(self, data: Any, context: Dict[str, Any]) -> Any:
        """Process data.

        Args:
            data: The data to process
            context: The pipeline context

        Returns:
            The processed data

        Raises:
            ValidationError: If validation fails and fail_fast is True
        """
        # Add the validation stage to the context
        context["validation_stage"] = self._stage

        # Apply each validation hook
        all_errors = {}
        for hook in self._hooks:
            result = hook.validate(data, context)
            if not result.is_valid:
                # Add errors from this hook
                for key, value in result.errors.items():
                    all_errors[f"{hook.validator.name}.{key}"] = value

                # Stop validation if fail_fast is True
                if self._fail_fast:
                    break

        # Raise an error if validation failed and fail_fast is True
        if all_errors and self._fail_fast:
            error_message = f"Validation failed at stage '{self._name}': {', '.join(f'{k}: {v}' for k, v in all_errors.items())}"
            raise ValidationError(
                message=error_message,
                details={"errors": all_errors, "stage": self._name},
            )

        # Add validation errors to the context
        if "validation_errors" not in context:
            context["validation_errors"] = {}
        context["validation_errors"][self._name] = all_errors

        # Return the data
        return data


class ValidatedTransformStage(PipelineStage):
    """Pipeline stage that applies a transform with validation.

    This stage applies a transform to data, with validation before and after
    transformation.
    """

    def __init__(
        self,
        name: str,
        transform: Union[Transform, str],
        pre_hooks: Optional[List[ValidationHook]] = None,
        post_hooks: Optional[List[ValidationHook]] = None,
        fail_fast: bool = True,
    ):
        """Initialize a validated transform stage.

        Args:
            name: The name of the stage
            transform: The transform to apply, either as a Transform object or the name of a registered transform
            pre_hooks: The validation hooks to apply before transformation, or None for no pre-validation
            post_hooks: The validation hooks to apply after transformation, or None for no post-validation
            fail_fast: Whether to stop validation after the first failure
        """
        self._name = name
        self._transform = transform
        self._pre_hooks = pre_hooks or []
        self._post_hooks = post_hooks or []
        self._fail_fast = fail_fast

    @property
    def name(self) -> str:
        """Get the name of the stage.

        Returns:
            The name of the stage
        """
        return self._name

    def process(self, data: Any, context: Dict[str, Any]) -> Any:
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
            # Apply pre-validation
            if self._pre_hooks:
                pre_validation = ValidationStageAdapter(
                    f"{self._name}_pre_validation",
                    self._pre_hooks,
                    ValidationStage.PRE_TRANSFORM,
                    self._fail_fast,
                )
                data = pre_validation.process(data, context)

            # Get the transform
            transform_obj = self._transform
            if isinstance(transform_obj, str):
                transform_obj = get_transform(transform_obj)

            # Apply the transform
            result = transform_obj.transform(data)

            # Apply post-validation
            if self._post_hooks:
                post_validation = ValidationStageAdapter(
                    f"{self._name}_post_validation",
                    self._post_hooks,
                    ValidationStage.POST_TRANSFORM,
                    self._fail_fast,
                )
                result = post_validation.process(result, context)

            # Update the context
            context["last_stage"] = self.name
            context["last_result"] = result

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


class ValidatedPipeline(Pipeline):
    """Pipeline for data transformation with validation.

    This pipeline applies a sequence of stages to data, with validation hooks
    at various stages of transformation.
    """

    def __init__(
        self,
        name: str,
        stages: List[PipelineStage],
        intermediate_hooks: Optional[List[ValidationHook]] = None,
        validation_levels: Optional[List[ValidationLevel]] = None,
    ):
        """Initialize a validated pipeline.

        Args:
            name: The name of the pipeline
            stages: The stages to apply
            intermediate_hooks: The validation hooks to apply between stages, or None for no intermediate validation
            validation_levels: The validation levels to enable, or None to enable only STANDARD validation
        """
        super().__init__(name, stages)
        self._intermediate_hooks = intermediate_hooks or []
        self._validation_levels = validation_levels or [ValidationLevel.STANDARD]

    @property
    def intermediate_hooks(self) -> List[ValidationHook]:
        """Get the intermediate validation hooks.

        Returns:
            The intermediate validation hooks
        """
        return self._intermediate_hooks

    @property
    def validation_levels(self) -> List[ValidationLevel]:
        """Get the validation levels.

        Returns:
            The validation levels
        """
        return self._validation_levels

    def execute(self, data: Any, context: Optional[Dict[str, Any]] = None) -> Any:
        """Execute the pipeline.

        Args:
            data: The data to process
            context: The pipeline context, or None to create a new context

        Returns:
            The processed data

        Raises:
            TransformError: If there is an error executing the pipeline
            ValidationError: If validation fails
        """
        try:
            # Create a new context if none is provided
            if context is None:
                context = {}

            # Add the pipeline to the context
            context["pipeline"] = self.name

            # Add validation levels to the context
            context["validation_levels"] = self._validation_levels

            # Apply each stage in sequence
            result = data
            for i, stage in enumerate(self._stages):
                # Apply the stage
                result = stage.process(result, context)

                # Apply intermediate validation after each stage except the last
                if i < len(self._stages) - 1 and self._intermediate_hooks:
                    intermediate_validation = ValidationStageAdapter(
                        f"{self.name}_intermediate_validation_{i}",
                        self._intermediate_hooks,
                        ValidationStage.INTERMEDIATE,
                        True,
                    )
                    result = intermediate_validation.process(result, context)

            return result
        except ValidationError as e:
            # Re-raise validation errors
            raise e
        except TransformError as e:
            # Add context to transform errors
            raise TransformError(
                f"Error in pipeline '{self.name}': {e}",
                transform_name=self.name,
            )
        except Exception as e:
            # Convert other exceptions to TransformError
            raise TransformError(
                f"Error in pipeline '{self.name}': {e}",
                transform_name=self.name,
            )


# Registry for validated pipelines
_validated_pipelines: Dict[str, ValidatedPipeline] = {}


def register_validated_pipeline(pipeline: ValidatedPipeline) -> None:
    """Register a validated pipeline.

    Args:
        pipeline: The pipeline to register

    Raises:
        TransformError: If the pipeline is already registered
    """
    if pipeline.name in _validated_pipelines:
        raise TransformError(
            f"Pipeline '{pipeline.name}' is already registered",
            transform_name=pipeline.name,
        )
    _validated_pipelines[pipeline.name] = pipeline


def get_validated_pipeline(name: str) -> ValidatedPipeline:
    """Get a registered validated pipeline.

    Args:
        name: The name of the pipeline to get

    Returns:
        The pipeline

    Raises:
        TransformError: If the pipeline is not registered
    """
    if name not in _validated_pipelines:
        raise TransformError(
            f"Pipeline '{name}' is not registered",
            transform_name=name,
        )
    return _validated_pipelines[name]


def create_validated_pipeline(
    name: str,
    transforms: List[Union[Transform, str]],
    validators: Optional[List[Union[Validator, str]]] = None,
    pre_validation: bool = True,
    post_validation: bool = True,
    intermediate_validation: bool = True,
    validation_levels: Optional[List[ValidationLevel]] = None,
    fail_fast: bool = True,
) -> ValidatedPipeline:
    """Create a validated pipeline.

    This function creates a pipeline that applies a sequence of transforms to data,
    with validation hooks at various stages of transformation.

    Args:
        name: The name of the pipeline
        transforms: The transforms to apply, either as Transform objects or the names of registered transforms
        validators: The validators to use, either as Validator objects or the names of registered validators,
            or None to use no validators
        pre_validation: Whether to apply validation before each transform
        post_validation: Whether to apply validation after each transform
        intermediate_validation: Whether to apply validation between stages
        validation_levels: The validation levels to enable, or None to enable only STANDARD validation
        fail_fast: Whether to stop validation after the first failure

    Returns:
        The validated pipeline
    """
    # Resolve validators
    resolved_validators = []
    if validators:
        for v in validators:
            if isinstance(v, str):
                resolved_validators.append(get_validator(v))
            else:
                resolved_validators.append(v)

    # Create validation hooks
    pre_hooks = []
    post_hooks = []
    intermediate_hooks = []

    for validator in resolved_validators:
        if pre_validation:
            pre_hooks.append(
                ValidationHook(
                    validator=validator,
                    stage=ValidationStage.PRE_TRANSFORM,
                )
            )
        if post_validation:
            post_hooks.append(
                ValidationHook(
                    validator=validator,
                    stage=ValidationStage.POST_TRANSFORM,
                )
            )
        if intermediate_validation:
            intermediate_hooks.append(
                ValidationHook(
                    validator=validator,
                    stage=ValidationStage.INTERMEDIATE,
                )
            )

    # Create validated transform stages
    stages = []
    for i, transform in enumerate(transforms):
        stage_name = f"{name}_stage_{i}"
        if isinstance(transform, str):
            stage_name = transform

        stage = ValidatedTransformStage(
            name=stage_name,
            transform=transform,
            pre_hooks=pre_hooks,
            post_hooks=post_hooks,
            fail_fast=fail_fast,
        )
        stages.append(stage)

    # Create and register the pipeline
    pipeline = ValidatedPipeline(
        name=name,
        stages=stages,
        intermediate_hooks=intermediate_hooks,
        validation_levels=validation_levels,
    )
    register_validated_pipeline(pipeline)

    return pipeline


def execute_validated_pipeline(
    name: str, data: Any, context: Optional[Dict[str, Any]] = None
) -> Any:
    """Execute a registered validated pipeline.

    Args:
        name: The name of the pipeline to execute
        data: The data to process
        context: The pipeline context, or None to create a new context

    Returns:
        The processed data

    Raises:
        TransformError: If the pipeline is not registered or there is an error executing the pipeline
        ValidationError: If validation fails
    """
    pipeline = get_validated_pipeline(name)
    return pipeline.execute(data, context)
