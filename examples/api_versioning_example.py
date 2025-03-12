#!/usr/bin/env python
"""Example demonstrating API versioning and deprecation system.

This example shows how to use the API versioning and deprecation system provided by
the PepperPy framework. It demonstrates version comparison, deprecation decorators,
and version requirement decorators.
"""

import logging
import warnings

from pepperpy.core.versioning import (
    DeprecationError,
    DeprecationLevel,
    Version,
    VersionError,
    VersionFormat,
    api_version,
    check_version_compatibility,
    deprecated,
    deprecated_class,
    find_deprecated_usages,
    get_api_registry,
    get_api_version,
    register_api_version,
    version_required,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Show deprecation warnings
warnings.filterwarnings("always", category=DeprecationWarning)


def example_version_comparison():
    """Example of version comparison."""
    logger.info("=== Version Comparison Example ===")

    # Create versions
    v1 = Version("1.0.0")
    v2 = Version("1.1.0")
    v3 = Version("2.0.0")
    v4 = Version("1.0.0-alpha")
    v5 = Version("1.0.0-beta")

    # Compare versions
    logger.info(f"v1 = {v1.version}, v2 = {v2.version}, v3 = {v3.version}")
    logger.info(f"v1 < v2: {v1 < v2}")
    logger.info(f"v2 < v3: {v2 < v3}")
    logger.info(f"v1 == v1: {v1 == v1}")
    logger.info(f"v1 <= v2: {v1 <= v2}")
    logger.info(f"v3 >= v2: {v3 >= v2}")

    # Compare prerelease versions
    logger.info(f"v4 = {v4.version}, v5 = {v5.version}")
    logger.info(f"v4 < v5: {v4 < v5}")
    logger.info(f"v4 < v1: {v4 < v1}")

    # Date-based versions
    d1 = Version("2023.01.01", VersionFormat.DATE)
    d2 = Version("2023.01.15", VersionFormat.DATE)
    d3 = Version("2023.02.01", VersionFormat.DATE)

    logger.info(f"d1 = {d1.version}, d2 = {d2.version}, d3 = {d3.version}")
    logger.info(f"d1 < d2: {d1 < d2}")
    logger.info(f"d2 < d3: {d2 < d3}")

    # Custom versions
    c1 = Version("1.0.alpha", VersionFormat.CUSTOM)
    c2 = Version("1.0.beta", VersionFormat.CUSTOM)

    logger.info(f"c1 = {c1.version}, c2 = {c2.version}")
    logger.info(f"c1 < c2: {c1 < c2}")

    # Parse version strings
    v_parsed = Version.parse("1.2.3")
    logger.info(f"Parsed version: {v_parsed.version}, Format: {v_parsed.format.name}")

    d_parsed = Version.parse("2023.04.01")
    logger.info(f"Parsed version: {d_parsed.version}, Format: {d_parsed.format.name}")


def example_api_versioning():
    """Example of API versioning."""
    logger.info("=== API Versioning Example ===")

    # Register API versions
    register_api_version("example_api", "1.0.0")
    register_api_version("data_api", "2.1.0")
    register_api_version("auth_api", "0.9.0")

    # Get API versions
    example_version = get_api_version("example_api")
    data_version = get_api_version("data_api")
    auth_version = get_api_version("auth_api")

    logger.info(f"example_api version: {example_version}")
    logger.info(f"data_api version: {data_version}")
    logger.info(f"auth_api version: {auth_version}")

    # Check version compatibility
    logger.info(
        f"example_api compatible with 0.9.0: {check_version_compatibility('example_api', '0.9.0')}"
    )
    logger.info(
        f"example_api compatible with 1.1.0: {check_version_compatibility('example_api', '1.1.0')}"
    )
    logger.info(
        f"data_api compatible with 2.0.0: {check_version_compatibility('data_api', '2.0.0')}"
    )

    # Get API registry
    registry = get_api_registry()

    # Get version history
    example_history = registry.get_version_history("example_api")
    logger.info(
        f"example_api version history: {[v.version for v in example_history.values()]}"
    )


# Example of deprecated function
@deprecated(
    message="This function is no longer supported.",
    version="1.0.0",
    removal_version="2.0.0",
    alternative="new_function",
    level=DeprecationLevel.WARNING,
)
def old_function(value: str) -> str:
    """Example of a deprecated function.

    Args:
        value: Input value

    Returns:
        Processed value
    """
    return f"Processed: {value}"


def new_function(value: str) -> str:
    """Replacement for old_function.

    Args:
        value: Input value

    Returns:
        Processed value
    """
    return f"New processing: {value}"


# Example of deprecated class
@deprecated_class(
    message="This class is no longer supported.",
    version="1.0.0",
    removal_version="2.0.0",
    alternative="NewProcessor",
    level=DeprecationLevel.WARNING,
)
class OldProcessor:
    """Example of a deprecated class."""

    def __init__(self, name: str):
        """Initialize the processor.

        Args:
            name: Processor name
        """
        self.name = name

    def process(self, value: str) -> str:
        """Process a value.

        Args:
            value: Input value

        Returns:
            Processed value
        """
        return f"{self.name} processed: {value}"


class NewProcessor:
    """Replacement for OldProcessor."""

    def __init__(self, name: str, version: str = "1.0"):
        """Initialize the processor.

        Args:
            name: Processor name
            version: Processor version
        """
        self.name = name
        self.version = version

    def process(self, value: str) -> str:
        """Process a value.

        Args:
            value: Input value

        Returns:
            Processed value
        """
        return f"{self.name} (v{self.version}) processed: {value}"


# Example of function with version requirement
@version_required(
    api_name="example_api",
    min_version="1.0.0",
    max_version="1.5.0",
)
def feature_with_version_requirement(value: str) -> str:
    """Example of a function with version requirement.

    Args:
        value: Input value

    Returns:
        Processed value
    """
    return f"Feature processed: {value}"


# Example of function with API version
@api_version("1.1.0")
def versioned_function(value: str) -> str:
    """Example of a function with API version.

    Args:
        value: Input value

    Returns:
        Processed value
    """
    return f"Versioned function processed: {value}"


def example_deprecation():
    """Example of deprecation system."""
    logger.info("=== Deprecation Example ===")

    # Use deprecated function
    try:
        result = old_function("test")
        logger.info(f"Result from deprecated function: {result}")
    except DeprecationError as e:
        logger.error(f"Error using deprecated function: {e}")

    # Use deprecated class
    try:
        processor = OldProcessor("Old")
        result = processor.process("test")
        logger.info(f"Result from deprecated class: {result}")
    except DeprecationError as e:
        logger.error(f"Error using deprecated class: {e}")

    # Use new function and class
    result = new_function("test")
    logger.info(f"Result from new function: {result}")

    processor = NewProcessor("New", "2.0")
    result = processor.process("test")
    logger.info(f"Result from new class: {result}")

    # Find deprecated usages
    deprecated_usages = find_deprecated_usages(__import__(__name__))
    logger.info(f"Found {len(deprecated_usages)} deprecated usages:")
    for name, info in deprecated_usages:
        logger.info(
            f"  {name}: {info.message} (deprecated in {info.version}, removal in {info.removal_version})"
        )


def example_version_requirement():
    """Example of version requirement system."""
    logger.info("=== Version Requirement Example ===")

    # Use function with version requirement
    try:
        result = feature_with_version_requirement("test")
        logger.info(f"Result from function with version requirement: {result}")
    except VersionError as e:
        logger.error(f"Error using function with version requirement: {e}")

    # Change API version to incompatible version
    register_api_version("example_api", "1.6.0")

    # Use function with version requirement again
    try:
        result = feature_with_version_requirement("test")
        logger.info(f"Result from function with version requirement: {result}")
    except VersionError as e:
        logger.error(f"Error using function with version requirement: {e}")

    # Change API version back to compatible version
    register_api_version("example_api", "1.2.0")

    # Use function with version requirement again
    try:
        result = feature_with_version_requirement("test")
        logger.info(f"Result from function with version requirement: {result}")
    except VersionError as e:
        logger.error(f"Error using function with version requirement: {e}")


def main():
    """Run all examples."""
    example_version_comparison()
    example_api_versioning()
    example_deprecation()
    example_version_requirement()


if __name__ == "__main__":
    main()
