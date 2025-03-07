"""Factory functions for creating developer assistants."""

from typing import Any, Dict, Optional, Union

from pepperpy.core.assistant.base import BaseAssistant
from pepperpy.core.assistant.types import AssistantType
from pepperpy.core.registry.registry import get_class


def create_assistant(
    assistant_type: Union[str, AssistantType],
    name: Optional[str] = None,
    config: Optional[Dict[str, Any]] = None,
    **kwargs: Any,
) -> BaseAssistant:
    """Create a developer assistant.

    Args:
        assistant_type: Type of assistant to create
        name: Optional name for the assistant
        config: Optional configuration for the assistant
        **kwargs: Additional keyword arguments for the assistant

    Returns:
        An instance of the requested assistant

    Examples:
        >>> import pepperpy as pp
        >>> # Create a pipeline builder assistant
        >>> assistant = pp.create_assistant("pipeline_builder")
        >>> # Use the assistant to create a pipeline
        >>> pipeline = assistant.create("question-answering")
    """
    # Normalize assistant type
    if isinstance(assistant_type, str):
        try:
            assistant_type = AssistantType(assistant_type)
        except ValueError:
            valid_types = ", ".join([t.value for t in AssistantType])
            raise ValueError(
                f"Invalid assistant type: {assistant_type}. "
                f"Valid types are: {valid_types}"
            )

    # Get the assistant class from the registry
    assistant_class = get_class(
        f"pepperpy.core.assistant.implementations.{assistant_type.value}"
    )

    # Create and return the assistant
    return assistant_class(
        name=name or f"{assistant_type.value}_assistant",
        config=config or {},
        **kwargs,
    )
