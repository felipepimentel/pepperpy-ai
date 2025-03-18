"""Examples of using the PepperPy pipeline framework.

This module contains examples of how to use the pipeline framework for
various common tasks. These examples can be used as a reference for
implementing custom pipelines.
"""

import logging
from typing import Any, Dict, List, Optional

from pepperpy.core.pipeline.base import (
    Pipeline,
    PipelineConfig,
    PipelineContext,
    register_pipeline,
)
from pepperpy.core.pipeline.stages import (
    BranchingStage,
    ConditionalStage,
    FunctionStage,
)

logger = logging.getLogger(__name__)


# Example 1: Simple data transformation pipeline
def create_data_processing_pipeline() -> Pipeline:
    """Create a simple data processing pipeline.

    This pipeline performs basic data transformations on a dictionary of values.

    Returns:
        A pipeline for processing data
    """
    # Create the pipeline with stages
    pipeline = Pipeline(
        name="data_processing_pipeline",
        stages=[
            # Validate input data
            FunctionStage(
                name="validate_input",
                func=lambda data, context: (
                    data
                    if isinstance(data, dict)
                    else {"value": data}
                    if data is not None
                    else {"value": None}
                ),
                description="Ensure input is a dictionary",
            ),
            # Fill missing values
            FunctionStage(
                name="fill_missing_values",
                func=lambda data, context: {
                    **{k: None for k in context.get("required_fields", [])},
                    **data,
                },
                description="Fill missing values with None",
            ),
            # Transform values
            FunctionStage(
                name="transform_values",
                func=lambda data, context: {
                    k: _transform_value(v, context.get("transforms", {}).get(k))
                    for k, v in data.items()
                },
                description="Apply transformations to values",
            ),
            # Validate output
            FunctionStage(
                name="validate_output",
                func=_validate_output,
                description="Validate the output data",
            ),
        ],
        config=PipelineConfig(
            name="data_processing_pipeline",
            description="A pipeline for processing and transforming data",
            metadata={"version": "1.0.0"},
            options={"log_level": "debug"},
        ),
    )

    # Register the pipeline for later use
    register_pipeline(pipeline)

    return pipeline


def _transform_value(value: Any, transform: Optional[Any] = None) -> Any:
    """Transform a value using the specified transform.

    Args:
        value: The value to transform
        transform: The transform to apply (function or object with transform method)

    Returns:
        The transformed value
    """
    if value is None or transform is None:
        return value

    if callable(transform):
        return transform(value)
    elif hasattr(transform, "transform"):
        return transform.transform(value)
    else:
        return value


def _validate_output(data: Dict[str, Any], context: PipelineContext) -> Dict[str, Any]:
    """Validate the output data.

    Args:
        data: The data to validate
        context: The pipeline context

    Returns:
        The validated data
    """
    required_fields = context.get("required_fields", [])

    # Check required fields
    for field in required_fields:
        if field not in data or data[field] is None:
            logger.warning(f"Required field '{field}' is missing or None")

    # Add validation metadata
    context.set_metadata("validated", True)
    context.set_metadata(
        "missing_fields",
        [
            field
            for field in required_fields
            if field not in data or data[field] is None
        ],
    )

    return data


# Example 2: Conditional processing pipeline
def create_conditional_pipeline() -> Pipeline:
    """Create a pipeline with conditional processing.

    This pipeline demonstrates how to use conditional stages to handle
    different types of data.

    Returns:
        A pipeline for conditional processing
    """

    # Define helper functions for the stages
    def is_list(data: Any, context: PipelineContext) -> bool:
        """Check if data is a list."""
        is_list_data = isinstance(data, list)
        context.set_metadata("is_list", is_list_data)
        return is_list_data

    def process_list(data: List[Any], context: PipelineContext) -> Dict[str, Any]:
        """Process a list of items."""
        return {
            "count": len(data),
            "items": data,
            "type": "list",
        }

    def process_single(data: Any, context: PipelineContext) -> Dict[str, Any]:
        """Process a single item."""
        return {
            "value": data,
            "type": "single",
        }

    # Create stages
    check_stage = FunctionStage("check_type", is_list)
    list_stage = FunctionStage("process_list", process_list)
    single_stage = FunctionStage("process_single", process_single)

    # Create conditional stage
    conditional_stage = ConditionalStage(
        name="conditional_processing",
        condition=is_list,
        if_true=list_stage,
        if_false=single_stage,
        description="Process data differently based on type",
    )

    # Create the pipeline
    pipeline = Pipeline(
        name="conditional_pipeline",
        stages=[conditional_stage],
        config=PipelineConfig(
            name="conditional_pipeline",
            description="A pipeline for conditional processing based on data type",
        ),
    )

    # Register the pipeline
    register_pipeline(pipeline)

    return pipeline


# Example 3: Branching pipeline
def create_branching_pipeline() -> Pipeline:
    """Create a pipeline with parallel processing branches.

    This pipeline demonstrates how to process the same data in multiple ways
    and collect the results.

    Returns:
        A pipeline for parallel processing
    """

    # Define processing functions
    def count_items(data: Any, context: PipelineContext) -> int:
        """Count items in the data."""
        if isinstance(data, (list, tuple, dict, str)):
            return len(data)
        return 1

    def summarize(data: Any, context: PipelineContext) -> str:
        """Create a summary of the data."""
        if isinstance(data, list):
            return f"List with {len(data)} items"
        elif isinstance(data, dict):
            return f"Dictionary with {len(data)} keys: {', '.join(data.keys())}"
        elif isinstance(data, str):
            return f"String of length {len(data)}"
        else:
            return f"Value of type {type(data).__name__}"

    def process_stats(data: Any, context: PipelineContext) -> Dict[str, Any]:
        """Calculate statistics about the data."""
        result: Dict[str, Any] = {
            "type": type(data).__name__,
        }

        if isinstance(data, (list, tuple)) and data:
            if all(isinstance(x, (int, float)) for x in data):
                result["min"] = min(data)
                result["max"] = max(data)
                result["avg"] = sum(data) / len(data)

        return result

    # Create the branching stage
    branching_stage = BranchingStage(
        name="parallel_processing",
        branches={
            "count": FunctionStage("count_items", count_items),
            "summary": FunctionStage("summarize", summarize),
            "stats": FunctionStage("process_stats", process_stats),
        },
        description="Process the data in multiple ways",
    )

    # Create a stage to format the results
    format_results = FunctionStage(
        name="format_results",
        func=lambda data, context: {
            "results": data,
            "metadata": {
                key: value
                for key, value in context.metadata.items()
                if key not in ("current_stage", "stage_index", "pipeline_name")
            },
        },
        description="Format the final results",
    )

    # Create the pipeline
    pipeline = Pipeline(
        name="branching_pipeline",
        stages=[
            branching_stage,
            format_results,
        ],
        config=PipelineConfig(
            name="branching_pipeline",
            description="A pipeline for parallel processing",
        ),
    )

    # Register the pipeline
    register_pipeline(pipeline)

    return pipeline


# Example usage of the pipelines
def run_pipeline_examples() -> None:
    """Run examples of the pipeline framework.

    This function demonstrates how to create and use pipelines for
    different types of data processing tasks.
    """
    logger.info("Running pipeline examples")

    # Example 1: Data processing pipeline
    data_pipeline = create_data_processing_pipeline()
    context = PipelineContext()
    context.set("required_fields", ["name", "age", "email"])
    context.set(
        "transforms",
        {
            "name": str.strip,
            "age": lambda x: int(x) if x is not None else None,
        },
    )

    input_data = {
        "name": "  John Doe  ",
        "email": "john@example.com",
    }

    result1 = data_pipeline.execute(input_data, context)
    logger.info(f"Data processing result: {result1}")
    logger.info(f"Missing fields: {context.get_metadata('missing_fields')}")

    # Example 2: Conditional processing pipeline
    conditional_pipeline = create_conditional_pipeline()

    list_data = [1, 2, 3, 4, 5]
    single_data = "Hello, World!"

    list_context = PipelineContext()
    result2a = conditional_pipeline.execute(list_data, list_context)
    logger.info(f"Conditional pipeline (list) result: {result2a}")

    single_context = PipelineContext()
    result2b = conditional_pipeline.execute(single_data, single_context)
    logger.info(f"Conditional pipeline (single) result: {result2b}")

    # Example 3: Branching pipeline
    branching_pipeline = create_branching_pipeline()

    numeric_data = [10, 20, 30, 40, 50]
    string_data = "PepperPy Pipeline Framework"

    numeric_context = PipelineContext()
    numeric_context.set_metadata("data_type", "numeric")
    result3a = branching_pipeline.execute(numeric_data, numeric_context)
    logger.info(f"Branching pipeline (numeric) result: {result3a}")

    string_context = PipelineContext()
    string_context.set_metadata("data_type", "string")
    result3b = branching_pipeline.execute(string_data, string_context)
    logger.info(f"Branching pipeline (string) result: {result3b}")

    logger.info("Pipeline examples completed")


if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Run the examples
    run_pipeline_examples()
