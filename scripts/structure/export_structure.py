#!/usr/bin/env python3
"""Export project structure in a simplified format for LLM context.

This script exports the project structure in a simplified format that can be used
as context for language models. The output is designed to be easily parsed and
understood by AI models.

Component: Development Tools
Created: 2024-03-20
Task: TASK-000
Status: active
"""

import re
from pathlib import Path


def extract_file_purpose(file_path: Path) -> str | None:
    """Extract purpose from file header."""
    if not file_path.is_file():
        return None

    try:
        with open(file_path) as f:
            content = f.read(500)  # Read first 500 chars
            purpose_match = re.search(r"@purpose:\s*(.+)", content)
            return purpose_match.group(1).strip() if purpose_match else None
    except Exception:
        return None


def should_ignore(path: str) -> bool:
    """Check if path should be ignored."""
    ignore_patterns = [
        r"\.git",
        r"\.pytest_cache",
        r"__pycache__",
        r"\.mypy_cache",
        r"\.coverage",
        r"\.env",
        r"\.venv",
        r"\.idea",
        r"\.vscode",
    ]
    return any(re.search(pattern, path) for pattern in ignore_patterns)


def export_structure(
    root_dir: Path, current_depth: int = 0, max_depth: int = 5
) -> list[str]:
    """Export directory structure with purposes."""
    if current_depth > max_depth:
        return ["    " * current_depth + "..."]

    if should_ignore(str(root_dir)):
        return []

    lines = []
    indent = "    " * current_depth

    # Process directories first
    for path in sorted(root_dir.iterdir()):
        if path.is_dir():
            purpose = extract_file_purpose(path / "__init__.py")
            purpose_str = f" # {purpose}" if purpose else ""
            lines.append(f"{indent}{path.name}/{purpose_str}")
            lines.extend(export_structure(path, current_depth + 1, max_depth))

    # Then process files
    for path in sorted(root_dir.iterdir()):
        if path.is_file() and path.name != "__init__.py":
            purpose = extract_file_purpose(path)
            purpose_str = f" # {purpose}" if purpose else ""
            lines.append(f"{indent}{path.name}{purpose_str}")

    return lines


def main() -> None:
    """Main entry point."""
    project_root = Path(__file__).parent.parent.parent
    lines = export_structure(project_root)

    print("\nProject Structure:")
    print("=================")
    for line in lines:
        print(line)
    print("\nNote: Only showing files with @purpose headers")


if __name__ == "__main__":
    main()
