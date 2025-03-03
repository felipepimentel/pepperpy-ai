#!/usr/bin/env python3
"""
Script to fix unused imports and redefined imports in the project.
"""

import json
import os
import subprocess
from typing import Any, Dict, List, Set


def run_ruff_check() -> List[Dict[str, Any]]:
    """Run ruff check and return the errors as a list of dictionaries."""
    try:
        result = subprocess.run(
            ["ruff", "check", "pepperpy/", "--format=json", "--select=F401,F811"],
            capture_output=True,
            text=True,
        )
        if result.stdout:
            return json.loads(result.stdout)
        return []
    except Exception as e:
        print(f"Error running ruff check: {e}")
        return []


def group_errors_by_file(
    errors: List[Dict[str, Any]],
) -> Dict[str, List[Dict[str, Any]]]:
    """Group errors by file."""
    grouped: Dict[str, List[Dict[str, Any]]] = {}
    for error in errors:
        file_path = error.get("filename", "")
        if file_path not in grouped:
            grouped[file_path] = []
        grouped[file_path].append(error)
    return grouped


def fix_unused_imports(file_path: str, errors: List[Dict[str, Any]]) -> int:
    """Fix unused imports (F401) and redefined imports (F811)."""
    if not os.path.exists(file_path):
        return 0

    try:
        with open(file_path, "r") as f:
            content = f.read()

        lines = content.split("\n")
        lines_to_remove: Set[int] = set()

        for error in errors:
            code = error.get("code", "")
            if code in ["F401", "F811"]:
                line = error.get("location", {}).get("row", 0) - 1
                if 0 <= line < len(lines):
                    lines_to_remove.add(line)

        # Remove the lines with unused imports
        new_lines = [line for i, line in enumerate(lines) if i not in lines_to_remove]
        new_content = "\n".join(new_lines)

        with open(file_path, "w") as f:
            f.write(new_content)

        return len(lines_to_remove)
    except Exception as e:
        print(f"Error fixing unused imports in {file_path}: {e}")
        return 0


def fix_all_unused_imports() -> int:
    """Fix all unused imports in the project."""
    errors = run_ruff_check()
    if not errors:
        print("No unused import errors found.")
        return 0

    grouped_errors = group_errors_by_file(errors)
    total_fixed = 0

    for file_path, file_errors in grouped_errors.items():
        fixed = fix_unused_imports(file_path, file_errors)
        if fixed > 0:
            print(f"Fixed {fixed} unused imports in {file_path}")
            total_fixed += fixed

    return total_fixed


def main():
    """Main function."""
    print("Starting to fix unused imports...")

    total_fixed = fix_all_unused_imports()

    print(f"\nTotal unused imports fixed: {total_fixed}")

    # Run final check
    errors = run_ruff_check()
    print(f"Remaining unused import errors: {len(errors)}")


if __name__ == "__main__":
    main()
