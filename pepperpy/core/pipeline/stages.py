"""Common pipeline stages for the PepperPy framework.

This module provides implementations of common pipeline stages that can be
used across different types of pipelines in the framework.
"""

import logging
from typing import Any, Callable, Dict, Optional, TypeVar, cast

from pepperpy.core.pipeline.base import PipelineContext, PipelineError, PipelineStage

# Type variables for generic pipeline stages
Input = TypeVar("Input")
Output = TypeVar("Output")
T = TypeVar("T")
R = TypeVar("R")

logger = logging.getLogger(__name__)


class FunctionStage(PipelineStage[Input, Output]):
    """Function-based pipeline stage.

    This stage wraps a function that processes input data and
    produces output data. The function can be synchronous or
    asynchronous.

    Attributes:
        name: The name of the stage
        func: The function to execute
        description: Optional description of the stage

    Example:
        >>> stage = FunctionStage("stage1", lambda x: x.upper())
        >>> context = PipelineContext()
        >>> result = await stage.execute("hello", context)
        >>> assert result == "HELLO"
    """

    def __init__(
        self,
        name: str,
        func: Callable[[Input, PipelineContext], Output],
        description: Optional[str] = None,
    ):
        """Initialize a function stage.

        Args:
            name: The name of the stage
            func: The function to execute
            description: Optional description of the stage

        Example:
            >>> stage = FunctionStage("stage1", lambda x: x.upper())
            >>> assert stage.name == "stage1"
        """
        super().__init__(name, description or "")
        self.func = func

    def process(self, input_data: Input, context: PipelineContext) -> Output:
        """Process the input data using the wrapped function.

        Args:
            input_data: The input data to process
            context: The pipeline context

        Returns:
            The processed output data

        Example:
            >>> stage = FunctionStage("stage1", lambda x, ctx: x.upper())
            >>> context = PipelineContext()
            >>> result = stage.process("hello", context)
            >>> assert result == "HELLO"
        """
        return self.func(input_data, context)


class TransformStage(PipelineStage[Input, Output]):
    """A pipeline stage that transforms input data using a transform object.

    This stage uses a transform object that has a transform method.
    """

    def __init__(
        self,
        name: str,
        transform: Any,
        description: str = "",
    ):
        """Initialize a transform stage.

        Args:
            name: The name of the stage
            transform: The transform object to use
            description: A description of the stage
        """
        super().__init__(name, description)
        self._transform = transform

    def process(self, input_data: Input, context: PipelineContext) -> Output:
        """Process the input data using the transform.

        Args:
            input_data: The input data to process
            context: The pipeline context

        Returns:
            The transformed output data
        """
        try:
            logger.debug(f"Executing transform stage: {self.name}")

            # If the transform is a string, look it up in the context
            if isinstance(self._transform, str):
                transform_name = self._transform
                transforms = context.get("transforms", {})
                if transform_name not in transforms:
                    raise PipelineError(
                        f"Transform '{transform_name}' not found in context"
                    )
                transform = transforms[transform_name]
            else:
                transform = self._transform

            # Call the transform method
            if hasattr(transform, "transform"):
                return transform.transform(input_data)
            elif callable(transform):
                return transform(input_data)
            else:
                raise PipelineError(
                    f"Invalid transform in stage {self.name}: {transform}"
                )

        except Exception as e:
            logger.error(f"Error in transform stage {self.name}: {str(e)}")
            raise PipelineError(
                f"Error in transform stage {self.name}: {str(e)}"
            ) from e


class ConditionalStage(PipelineStage[Input, Output]):
    """A pipeline stage that conditionally applies another stage.

    This stage applies a condition to the input data and, if the condition is
    met, applies another stage.
    """

    def __init__(
        self,
        name: str,
        condition: Callable[[Input, PipelineContext], bool],
        if_true: PipelineStage[Input, Output],
        if_false: Optional[PipelineStage[Input, Output]] = None,
        description: str = "",
    ):
        """Initialize a conditional stage.

        Args:
            name: The name of the stage
            condition: The condition to check
            if_true: The stage to apply if the condition is true
            if_false: The stage to apply if the condition is false (optional)
            description: A description of the stage
        """
        super().__init__(name, description)
        self._condition = condition
        self._if_true = if_true
        self._if_false = if_false

    def process(self, input_data: Input, context: PipelineContext) -> Output:
        """Process the input data conditionally.

        Args:
            input_data: The input data to process
            context: The pipeline context

        Returns:
            The processed output data
        """
        try:
            logger.debug(f"Executing conditional stage: {self.name}")

            # Check the condition
            if self._condition(input_data, context):
                logger.debug(
                    f"Condition in stage {self.name} is true, using if_true stage"
                )
                return self._if_true(input_data, context)
            elif self._if_false is not None:
                logger.debug(
                    f"Condition in stage {self.name} is false, using if_false stage"
                )
                return self._if_false(input_data, context)
            else:
                logger.debug(
                    f"Condition in stage {self.name} is false, no if_false stage, returning input"
                )
                return cast(Output, input_data)

        except Exception as e:
            logger.error(f"Error in conditional stage {self.name}: {str(e)}")
            raise PipelineError(
                f"Error in conditional stage {self.name}: {str(e)}"
            ) from e


class BranchingStage(PipelineStage[Input, Dict[str, Any]]):
    """A pipeline stage that applies multiple stages to the same input data.

    This stage applies multiple sub-stages to the same input data and collects
    the results into a dictionary.
    """

    def __init__(
        self,
        name: str,
        branches: Dict[str, PipelineStage[Input, Any]],
        description: str = "",
    ):
        """Initialize a branching stage.

        Args:
            name: The name of the stage
            branches: Dictionary mapping branch names to stages
            description: A description of the stage
        """
        super().__init__(name, description)
        self._branches = branches

    def process(self, input_data: Input, context: PipelineContext) -> Dict[str, Any]:
        """Process the input data using multiple branches.

        Args:
            input_data: The input data to process
            context: The pipeline context

        Returns:
            Dictionary mapping branch names to their outputs
        """
        try:
            logger.debug(f"Executing branching stage: {self.name}")
            results = {}

            # Process each branch
            for branch_name, stage in self._branches.items():
                logger.debug(f"Processing branch '{branch_name}' in stage {self.name}")
                branch_context = PipelineContext(
                    data=context.data.copy(),
                    metadata=context.metadata.copy(),
                )
                branch_context.set_metadata("branch_name", branch_name)
                results[branch_name] = stage(input_data, branch_context)

            return results

        except Exception as e:
            logger.error(f"Error in branching stage {self.name}: {str(e)}")
            raise PipelineError(
                f"Error in branching stage {self.name}: {str(e)}"
            ) from e
