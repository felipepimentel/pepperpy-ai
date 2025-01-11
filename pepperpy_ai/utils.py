"""Utility functions for PepperPy AI."""

import importlib.util
import logging
from typing import Any, Dict, List, Optional, Type, TypeVar

from pepperpy_ai.exceptions import DependencyError

logger = logging.getLogger(__name__)

T = TypeVar("T")


def check_dependency(package: str) -> bool:
    """Check if a package is installed.

    Args:
        package: The name of the package to check.

    Returns:
        True if the package is installed, False otherwise.
    """
    return importlib.util.find_spec(package) is not None


def get_missing_dependencies(required_packages: List[str]) -> List[str]:
    """Get a list of missing dependencies.

    Args:
        required_packages: List of required package names.

    Returns:
        List of missing package names.
    """
    return [pkg for pkg in required_packages if not check_dependency(pkg)]


def verify_dependencies(
    feature_name: str, required_packages: List[str]
) -> None:
    """Verify that all required dependencies are installed.

    Args:
        feature_name: The name of the feature requiring the dependencies.
        required_packages: List of required package names.

    Raises:
        DependencyError: If any required dependencies are missing.
    """
    missing = get_missing_dependencies(required_packages)
    if missing:
        packages_str = ", ".join(missing)
        raise DependencyError(
            f"Missing required dependencies for {feature_name}: {packages_str}",
            package=packages_str,
        )


def safe_import(
    module_path: str,
    class_name: str,
    base_class: Optional[Type[T]] = None,
) -> Optional[Type[T]]:
    """Safely import a class from a module.

    Args:
        module_path: The path to the module.
        class_name: The name of the class to import.
        base_class: Optional base class to verify inheritance.

    Returns:
        The imported class or None if import fails.
    """
    try:
        module = importlib.import_module(module_path)
        cls = getattr(module, class_name)
        if base_class and not issubclass(cls, base_class):
            logger.warning(
                f"Class {class_name} from {module_path} does not inherit from {base_class.__name__}"
            )
            return None
        return cls
    except (ImportError, AttributeError) as e:
        logger.debug(f"Failed to import {class_name} from {module_path}: {e}")
        return None


def merge_configs(
    base: Dict[str, Any], override: Dict[str, Any]
) -> Dict[str, Any]:
    """Merge two configuration dictionaries.

    Args:
        base: The base configuration.
        override: The configuration to override with.

    Returns:
        The merged configuration.
    """
    result = base.copy()
    for key, value in override.items():
        if (
            key in result
            and isinstance(result[key], dict)
            and isinstance(value, dict)
        ):
            result[key] = merge_configs(result[key], value)
        else:
            result[key] = value
    return result


def format_exception(exc: Exception) -> str:
    """Format an exception for display.

    Args:
        exc: The exception to format.

    Returns:
        A formatted string representation of the exception.
    """
    return f"{exc.__class__.__name__}: {str(exc)}" 