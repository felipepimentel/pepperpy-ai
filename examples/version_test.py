#!/usr/bin/env python
"""
Version Test Example for PepperPy.

This simple example demonstrates accessing the version information
from both the main package and core module after the migration.
"""

# Import version from the main package (new preferred way)
from pepperpy import __version__

# Import version from the core module directly
from pepperpy.core.version import __version__ as core_version


def main():
    """Run a simple demonstration of version access."""
    print("=== PepperPy Version Example ===")

    # 1. Show version from main package
    print(f"\n1. Version from pepperpy package: {__version__}")

    # 2. Show version from core module
    print(f"\n2. Version from pepperpy.core.version: {core_version}")

    # 3. Compare versions
    print(f"\n3. Both versions are identical: {__version__ == core_version}")

    print("\n=== Example Complete ===")


if __name__ == "__main__":
    main()
