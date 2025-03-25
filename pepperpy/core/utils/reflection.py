"""Utility functions for reflection and introspection."""

import inspect
from typing import Any, Dict, List, Optional, Set, Type


def get_class_attributes(
    cls: Type[Any],
    include_private: bool = False,
    include_methods: bool = False,
    include_inherited: bool = True,
) -> Dict[str, Any]:
    """Get all attributes of a class.

    Args:
        cls: The class to inspect.
        include_private: Whether to include private attributes (starting with _).
        include_methods: Whether to include methods.
        include_inherited: Whether to include inherited attributes.

    Returns:
        A dictionary mapping attribute names to their values.
    """
    result: Dict[str, Any] = {}
    seen: Set[str] = set()

    def should_include(name: str, value: Any) -> bool:
        if name in seen:
            return False
        if not include_private and name.startswith("_"):
            return False
        if not include_methods and inspect.isfunction(value):
            return False
        return True

    classes: List[Type[Any]] = [cls]
    if include_inherited:
        classes.extend(cls.__bases__)

    for c in classes:
        for name, value in inspect.getmembers(c):
            if should_include(name, value):
                result[name] = value
                seen.add(name)

    return result 