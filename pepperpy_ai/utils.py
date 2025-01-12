"""Utility functions module."""

import importlib
import logging
from typing import TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")


def load_class(
    module_path: str,
    class_name: str,
    base_class: type[T] | None = None,
) -> type[T] | None:
    """Load class from module path.

    Args:
        module_path: Module path.
        class_name: Class name.
        base_class: Base class to check inheritance.

    Returns:
        type[T] | None: Loaded class or None if not found.
    """
    try:
        module = importlib.import_module(module_path)
        cls = getattr(module, class_name)
        if base_class and not issubclass(cls, base_class):
            logger.warning(
                "Class %s from %s does not inherit from %s",
                class_name,
                module_path,
                base_class.__name__,
            )
            return None
        return cls
    except (ImportError, AttributeError) as e:
        logger.warning(
            "Failed to load class %s from %s: %s",
            class_name,
            module_path,
            str(e),
        )
        return None
