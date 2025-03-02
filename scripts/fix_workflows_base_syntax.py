#!/usr/bin/env python3
"""
Script to fix syntax errors in the workflows/base.py file.
"""

import re


def read_file(file_path: str) -> str:
    """Read file content."""
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()


def write_file(file_path: str, content: str) -> None:
    """Write content to file."""
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)


def fix_workflows_base_syntax() -> None:
    """Fix syntax errors in workflows/base.py."""
    file_path = "pepperpy/workflows/base.py"
    content = read_file(file_path)

    # Create a backup of the original file
    backup_path = f"{file_path}.syntax.bak"
    write_file(backup_path, content)
    print(f"Created backup at {backup_path}")

    # Fix import statement
    content = re.sub(
        r"from pepperpy\.core\.base import \(, ComponentBase, ComponentCallback, ComponentConfig, ComponentState\s+ComponentCallback,\s+ComponentConfig,\s+ComponentState,\s*\)",
        "from pepperpy.core.base import (ComponentBase, ComponentCallback, ComponentConfig, ComponentState)",
        content,
    )

    # Fix indentation in __init__ method
    content = re.sub(
        r"self\._callback = None\n\s+self\._metrics = \{\}\n\s+self\._metrics_manager = None  # Will be initialized later",
        "self._callback = None\n        self._metrics = {}\n        self._metrics_manager = None  # Will be initialized later",
        content,
    )

    # Fix docstring at the end of the file
    content = re.sub(
        r'# Merged from /home/pimentel/Workspace/pepperpy/pepperpy-ai/pepperpy/workflow/base\.py during consolidation  # noqa: E501\n"""Base classes and interfaces for the unified workflow system.',
        '# Merged from /home/pimentel/Workspace/pepperpy/pepperpy-ai/pepperpy/workflow/base.py during consolidation  # noqa: E501\n\n"""Base classes and interfaces for the unified workflow system.',
        content,
    )

    # Write the fixed content
    write_file(file_path, content)
    print(f"Fixed syntax errors in {file_path}")


def main() -> None:
    """Main function."""
    print("Fixing syntax errors in workflows/base.py...")
    fix_workflows_base_syntax()
    print("Done!")


if __name__ == "__main__":
    main()
