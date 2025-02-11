#!/usr/bin/env python3
"""Validate project structure against specification."""

import sys
from pathlib import Path
from typing import Any

import yaml


def load_structure(path: Path) -> dict[str, Any]:
    """Load project structure from YAML file.

    Args:
    ----
        path: Path to structure YAML file

    Returns:
    -------
        Dictionary containing structure specification

    """
    with open(path) as f:
        data = yaml.safe_load(f)
        if not isinstance(data, dict):
            raise ValueError("Structure file must contain a dictionary")
        return data


def validate_directory(
    path: Path,
    spec: dict[str, Any],
    errors: list[str],
    parent: str | None = None,
) -> None:
    """Validate a directory against specification.

    Args:
    ----
        path: Directory path to validate
        spec: Directory specification
        errors: List to collect validation errors
        parent: Parent directory name

    """
    if not path.exists():
        errors.append(f"Missing directory: {path}")
        return

    # Check required files
    required_files = spec.get("files", [])
    for file_name in required_files:
        file_path = path / file_name
        if not file_path.exists():
            errors.append(f"Missing required file: {file_path}")

    # Check required subdirectories
    required_dirs = spec.get("directories", {})
    for dir_name, dir_spec in required_dirs.items():
        dir_path = path / dir_name
        validate_directory(dir_path, dir_spec, errors, str(path))

    # Check for unexpected items
    allowed_items = set(required_files)
    allowed_items.update(required_dirs.keys())
    allowed_items.update(spec.get("optional_files", []))
    allowed_items.update(spec.get("optional_directories", []))

    for item in path.iterdir():
        if item.name.startswith("."):
            continue
        if item.name.startswith("__"):
            continue
        if item.name not in allowed_items:
            errors.append(f"Unexpected item in {parent or path}: {item.name}")


def main() -> int:
    """Validate project structure.

    Returns
    -------
        Exit code (0 for success, 1 for failure)

    """
    # Find project root (contains .product directory)
    root = Path.cwd()
    while not (root / ".product").exists():
        root = root.parent
        if root == root.parent:
            print("Error: Could not find project root")
            return 1

    # Load structure specification
    try:
        spec = load_structure(root / ".product/project_structure.yml")
    except Exception as e:
        print(f"Error loading structure specification: {e}")
        return 1

    # Validate structure
    errors: list[str] = []
    validate_directory(root, spec, errors)

    # Report results
    if errors:
        print("\nValidation Errors:")
        for error in errors:
            print(f"  ❌ {error}")
        print("\n❌ Project structure validation failed!")
        print("Please fix the errors and try again.")
        return 1

    print("\n✓ Project structure validation passed!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
