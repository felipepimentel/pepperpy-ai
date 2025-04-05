#!/usr/bin/env python
"""
Check for singular/plural naming inconsistencies in the PepperPy codebase.

This script scans the codebase for directories that violate the singular naming convention.
"""

import sys
from pathlib import Path

# Known domain names (always singular)
DOMAIN_NAMES = {
    "agent",
    "cache",
    "content",
    "discovery",
    "embedding",
    "llm",
    "rag",
    "tool",
    "tts",
    "workflow",
}


def is_plural(name: str) -> bool:
    """Simple check if a name appears to be plural.

    Args:
        name: Directory name to check

    Returns:
        True if the name appears to be plural
    """
    return name.endswith("s") and name[:-1] in DOMAIN_NAMES


def check_directory(base_path: Path, *, verbose: bool = False) -> list[str]:
    """Check a directory for plural naming violations.

    Args:
        base_path: Base directory to check
        verbose: Whether to print verbose output

    Returns:
        List of violation paths
    """
    violations = []

    for path in base_path.iterdir():
        if not path.is_dir() or path.name.startswith("."):
            continue

        # Check if the directory name is plural
        if is_plural(path.name):
            violations.append(str(path))
            if verbose:
                singular = path.name[:-1]
                print(f"❌ Found plural directory: {path}")
                print(f"   Should be: {path.parent / singular}")

        # Recursively check subdirectories
        violations.extend(check_directory(path, verbose=verbose))

    return violations


def main() -> int:
    """Main entry point.

    Returns:
        Exit code (0 for success, 1 for violations found)
    """
    verbose = "--verbose" in sys.argv
    strict = "--strict" in sys.argv

    base_dir = Path(__file__).parent.parent

    print(f"Checking {base_dir} for naming violations...")

    # Directories to check
    dirs_to_check = [
        base_dir / "pepperpy",
        base_dir / "plugins",
    ]

    all_violations = []
    for directory in dirs_to_check:
        violations = check_directory(directory, verbose=verbose)
        all_violations.extend(violations)

    if all_violations:
        print(f"\nFound {len(all_violations)} naming violations:")
        for violation in all_violations:
            print(f"  - {violation}")

        print("\nTo fix, REMOVE plural directories and use singular form:")
        print("  1. Ensure a singular directory exists with required functionality")
        print("  2. Remove the plural directory entirely")
        print("  3. Update imports in all code to use singular form")
        print("  4. Run tests to ensure nothing breaks")

        if strict:
            return 1
    else:
        print("\n✅ No naming violations found!")

    return 0


if __name__ == "__main__":
    sys.exit(main())
