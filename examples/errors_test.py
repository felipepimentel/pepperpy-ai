#!/usr/bin/env python
"""
Errors Test Example for PepperPy.

This simple example demonstrates the usage of the PepperpyError class 
from both the main package and core module after the migration.
"""

# Import directly from pepperpy package (new preferred way)
from pepperpy import PepperpyError

# Import from the core module
from pepperpy.core.errors import PepperpyError as CorePepperpyError


def main():
    """Run a simple demonstration of the PepperpyError class."""
    print("=== PepperPy Errors Example ===")

    # 1. Create and use a PepperpyError from the main package
    print("\n1. Using PepperpyError from pepperpy:")
    try:
        raise PepperpyError("This is a test error from the main package")
    except PepperpyError as e:
        print(f"Caught error: {e}")
        print(f"Error message: {e.message}")
        print(f"Error type: {type(e).__name__}")

    # 2. Create and use a PepperpyError from core.errors
    print("\n2. Using PepperpyError from pepperpy.core.errors:")
    try:
        raise CorePepperpyError("This is a test error from the core module")
    except CorePepperpyError as e:
        print(f"Caught error: {e}")
        print(f"Error message: {e.message}")
        print(f"Error type: {type(e).__name__}")

    # 3. Compare identity of error classes
    print("\n3. Comparing identity of error classes:")
    print(
        f"pepperpy.PepperpyError is pepperpy.core.errors.PepperpyError: {PepperpyError is CorePepperpyError}"
    )

    # 4. Test custom attributes
    print("\n4. Testing custom attributes:")
    try:
        raise PepperpyError(
            "Error with custom attributes", code="E1001", severity="high"
        )
    except PepperpyError as e:
        print(f"Caught error: {e}")
        print(f"Error message: {e.message}")
        print(f"Error code: {e.code}")
        print(f"Error severity: {e.severity}")

    print("\n=== Example Complete ===")


if __name__ == "__main__":
    main()
