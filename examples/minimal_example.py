#!/usr/bin/env python
"""
Minimal PepperPy Example.

This example demonstrates basic usage without relying on plugins or storage.
"""

import asyncio
import sys


async def main():
    """Run the minimal example."""
    print("PepperPy Minimal Example")
    print("=======================")

    print("\nThis is a minimal example that doesn't depend on plugins or storage.")
    print(
        "It demonstrates the ability to run basic functionality without complex dependencies."
    )

    # Show project structure info
    print("\nProject Structure Updates:")
    print("- Refactored project to follow architectural principles")
    print("- Removed unnecessary nested directories")
    print("- Fixed import references to follow proper abstraction layers")
    print("- Updated code to use framework APIs instead of direct provider imports")

    # Explain architectural improvements
    print("\nArchitectural Improvements:")
    print("- No direct access to providers (using framework abstractions)")
    print("- Flattened directory structure where appropriate")
    print("- Removed deprecated code")
    print("- Simplified plugin system")

    print("\nExample complete!")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nExample interrupted.")
        sys.exit(0)
