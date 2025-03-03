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

# Constants
REQUIRED_FIELDS = ["file", "purpose", "component", "created"]
OPTIONAL_FIELDS = ["task", "status"]
VALID_STATUSES = ["active", "deprecated", "experimental"]
DATE_PATTERN = r"^\d{4}-\d{2}-\d{2}$"
TASK_PATTERN = r"^TASK-\d{3}$"

# Type aliases
ErrorList = list[str]
ValidationResult = list[tuple[Path, ErrorList]]


def parse_header(content: str) -> dict[str, str]:
    """Parse file header into fields.

    Args:
        content: File content to parse

    Returns:
        Dictionary of field names to values

    """
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


def _check_required_fields(fields: dict[str, str]) -> ErrorList:
    """Check that all required fields are present and non-empty.

    Args:
        fields: Dictionary of field names to values

    Returns:
        List of error messages

    """
    errors: ErrorList = []
    for field in REQUIRED_FIELDS:
        if field not in fields:
            errors.append(f"Missing required field @{field}")
        elif not fields[field]:
            errors.append(f"Empty required field @{field}")
    return errors


def _validate_filename(file_path: Path, fields: dict[str, str]) -> ErrorList:
    """Validate that the file name matches the header.

    Args:
        file_path: Path to the file
        fields: Dictionary of field names to values

    Returns:
        List of error messages

    """
    errors: ErrorList = []
    if "file" in fields and fields["file"] != file_path.name:
        errors.append(f"File name mismatch: {fields['file']} != {file_path.name}")
    return errors


def _validate_date(fields: dict[str, str]) -> ErrorList:
    """Validate the created date field.

    Args:
        fields: Dictionary of field names to values

    Returns:
        List of error messages

    """
    errors: ErrorList = []
    if "created" in fields:
        if not re.match(DATE_PATTERN, fields["created"]):
            errors.append("Invalid date format in @created (use YYYY-MM-DD)")
    return errors


def _validate_status(fields: dict[str, str]) -> ErrorList:
    """Validate the status field.

    Args:
        fields: Dictionary of field names to values

    Returns:
        List of error messages

    """
    errors: ErrorList = []
    if "status" in fields:
        if fields["status"] not in VALID_STATUSES:
            errors.append(f"Invalid status: {fields['status']}")
    return errors


def _validate_task(fields: dict[str, str]) -> ErrorList:
    """Validate the task field.

    Args:
        fields: Dictionary of field names to values

    Returns:
        List of error messages

    """
    errors: ErrorList = []
    if "task" in fields:
        if not re.match(TASK_PATTERN, fields["task"]):
            errors.append("Invalid task format (use TASK-XXX)")
    return errors


def validate_header(file_path: Path, fields: dict[str, str]) -> ErrorList:
    """Validate header fields.

    Args:
        file_path: Path to the file
        fields: Dictionary of field names to values

    Returns:
        List of error messages

    """
    errors: ErrorList = []

    # Check each aspect of the header
    errors.extend(_check_required_fields(fields))
    errors.extend(_validate_filename(file_path, fields))
    errors.extend(_validate_date(fields))
    errors.extend(_validate_status(fields))
    errors.extend(_validate_task(fields))

    return errors


def should_check_file(path: Path) -> bool:
    """Determine if file should be checked.

    Args:
        path: Path to check

    Returns:
        True if file should be checked, False otherwise

    """
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


def check_files(root_dir: Path) -> ValidationResult:
    """Check all files in directory.

    Args:
        root_dir: Root directory to check

    Returns:
        List of (path, errors) tuples

    """
    issues: ValidationResult = []

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
            issues.append((path, [f"Failed to check file: {e}"]))

    return issues


def main() -> None:
    """Main entry point."""
    import argparse
    import sys

    parser = argparse.ArgumentParser(description="Validate file headers")
    parser.add_argument("path", help="File or directory to check")
    args = parser.parse_args()

    path = Path(args.path)
    if not path.exists():
        print(f"Path does not exist: {path}", file=sys.stderr)
        sys.exit(1)

    issues = check_files(path if path.is_dir() else path.parent)
    if issues:
        for path, errors in issues:
            print(f"\n{path}:")
            for error in errors:
                print(f"  - {error}")
        sys.exit(1)

    print("All headers valid")


if __name__ == "__main__":
    main()
