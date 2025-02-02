#!/usr/bin/env python3
"""Validate file headers according to project rules.

This script validates that all file headers in the project follow the defined
format and contain the required information.

Component: Development Tools
Created: 2024-03-20
Task: TASK-000
Status: active
"""

import re
from pathlib import Path

REQUIRED_FIELDS = ["file", "purpose", "component", "created"]
OPTIONAL_FIELDS = ["task", "status"]


def parse_header(content: str) -> dict[str, str]:
    """Parse file header into fields."""
    fields: dict[str, str] = {}
    header_match = re.search(r'"""(.*?)"""', content, re.DOTALL)

    if not header_match:
        return fields

    header = header_match.group(1)
    for line in header.split("\n"):
        field_match = re.match(r"@(\w+):\s*(.+)", line.strip())
        if field_match:
            fields[field_match.group(1)] = field_match.group(2).strip()

    return fields


def validate_header(file_path: Path, fields: dict[str, str]) -> list[str]:
    """Validate header fields."""
    errors = []

    # Check required fields
    for field in REQUIRED_FIELDS:
        if field not in fields:
            errors.append(f"Missing required field @{field}")
        elif not fields[field]:
            errors.append(f"Empty required field @{field}")

    # Validate specific fields
    if "file" in fields and fields["file"] != file_path.name:
        errors.append(f"File name mismatch: {fields['file']} != {file_path.name}")

    if "created" in fields:
        date_pattern = r"^\d{4}-\d{2}-\d{2}$"
        if not re.match(date_pattern, fields["created"]):
            errors.append("Invalid date format in @created (use YYYY-MM-DD)")

    if "status" in fields:
        valid_statuses = ["active", "deprecated", "experimental"]
        if fields["status"] not in valid_statuses:
            errors.append(f"Invalid status: {fields['status']}")

    if "task" in fields:
        task_pattern = r"^TASK-\d{3}$"
        if not re.match(task_pattern, fields["task"]):
            errors.append("Invalid task format (use TASK-XXX)")

    return errors


def should_check_file(path: Path) -> bool:
    """Determine if file should be checked."""
    if not path.is_file():
        return False

    # Only check Python files
    if path.suffix != ".py":
        return False

    # Skip test files
    if path.name.startswith("test_"):
        return False

    # Skip ignored directories
    ignore_dirs = {".git", ".venv", "__pycache__", ".mypy_cache"}
    if any(p.name in ignore_dirs for p in path.parents):
        return False

    return True


def check_files(root_dir: Path) -> list[tuple[Path, list[str]]]:
    """Check all files in directory."""
    issues = []

    for path in root_dir.rglob("*"):
        if not should_check_file(path):
            continue

        try:
            with open(path) as f:
                content = f.read()

            fields = parse_header(content)
            errors = validate_header(path, fields)

            if errors:
                issues.append((path, errors))

        except Exception as e:
            issues.append((path, [f"Error reading file: {e!s}"]))

    return issues


def main() -> None:
    """Main entry point."""
    project_root = Path(__file__).parent.parent.parent
    issues = check_files(project_root)

    if not issues:
        print("\n✅ All files have valid headers")
        return

    print("\n❌ Found header issues:")
    print("=====================")

    for path, errors in issues:
        print(f"\n{path}:")
        for error in errors:
            print(f"  - {error}")


if __name__ == "__main__":
    main()
