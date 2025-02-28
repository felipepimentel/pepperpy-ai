#!/usr/bin/env python3
"""Import Management Script.

This script provides a unified interface for managing imports across the project.
It handles:
- Updating import paths after module migrations
- Validating import patterns
- Fixing common import issues
"""

import argparse
import ast
import os
from collections.abc import Sequence
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import TypeVar

from loguru import Logger

from pepperpy.monitoring.logger import get_logger

# Type aliases
T = TypeVar("T")
ImportPair = tuple[str, str]
ImportList = list[ImportPair]

logger: Logger = get_logger(__name__)


class ImportType(Enum):
    """Types of import updates."""

    PROVIDERS = "providers"
    DATA = "data"
    RUNTIME = "runtime"
    PROFILE = "profile"
    CUSTOM = "custom"


@dataclass
class ImportMapping:
    """Mapping for import updates."""

    old_pattern: str
    new_pattern: str
    description: str


# Standard import mappings
IMPORT_MAPPINGS: dict[ImportType, list[ImportMapping]] = {
    ImportType.PROVIDERS: [
        ImportMapping(
            "from pepperpy.providers.vector_store.base",
            "from pepperpy.providers.vector_store.base",
            "Vector store base imports",
        ),
        ImportMapping(
            "from pepperpy.providers.memory",
            "from pepperpy.providers.memory",
            "Memory provider imports",
        ),
        ImportMapping(
            "from pepperpy.providers.llm",
            "from pepperpy.providers.llm",
            "LLM provider imports",
        ),
        ImportMapping(
            "from pepperpy.memory.providers",
            "from pepperpy.memory.providers",
            "Memory provider imports",
        ),
    ],
    ImportType.DATA: [
        ImportMapping(
            "from pepperpy.persistence.storage.document",
            "from pepperpy.persistence.storage.document",
            "Document storage imports",
        ),
        ImportMapping(
            "from pepperpy.persistence.storage.chunking",
            "from pepperpy.persistence.storage.chunking",
            "Chunking imports",
        ),
    ],
}


class ImportUpdater:
    """Handles import updates across the project."""

    def __init__(self, workspace: Path) -> None:
        """Initialize the updater.

        Args:
            workspace: Root workspace directory
        """
        self.workspace = workspace
        self.exclude_dirs = {".git", "__pycache__", "venv", "env", ".venv"}
        self.updated_files: set[Path] = set()

    def update_file(self, file_path: Path, mappings: list[ImportMapping]) -> None:
        """Update imports in a single file.

        Args:
            file_path: Path to file to update
            mappings: List of import mappings to apply
        """
        try:
            with open(file_path) as f:
                content = f.read()

            updated = False
            for mapping in mappings:
                if mapping.old_pattern in content:
                    content = content.replace(mapping.old_pattern, mapping.new_pattern)
                    updated = True
                    logger.info(
                        "Updated import",
                        extra={
                            "file": str(file_path),
                            "old": mapping.old_pattern,
                            "new": mapping.new_pattern,
                        },
                    )

            if updated:
                with open(file_path, "w") as f:
                    f.write(content)
                self.updated_files.add(file_path)

        except Exception as e:
            logger.error(
                "Failed to update file",
                extra={
                    "file": str(file_path),
                    "error": str(e),
                },
            )

    def update_imports(
        self,
        import_type: ImportType,
        custom_mappings: list[ImportMapping] | None = None,
    ) -> None:
        """Update imports of a specific type across the project.

        Args:
            import_type: Type of imports to update
            custom_mappings: Optional custom mappings to use instead of standard ones
        """
        mappings = custom_mappings or IMPORT_MAPPINGS.get(import_type, [])
        if not mappings:
            logger.warning(f"No mappings found for import type: {import_type}")
            return

        for root, dirs, files in os.walk(self.workspace):
            # Skip excluded directories
            dirs[:] = [d for d in dirs if d not in self.exclude_dirs]

            for file in files:
                if file.endswith(".py"):
                    file_path = Path(root) / file
                    self.update_file(file_path, mappings)

    def report(self) -> None:
        """Report results of the update operation."""
        if self.updated_files:
            logger.info(
                "Import update complete",
                extra={
                    "updated_files": len(self.updated_files),
                    "files": [str(f) for f in self.updated_files],
                },
            )
        else:
            logger.info("No files needed updating")


def extract_imports(tree: ast.AST) -> ImportList:
    """Extract imports from an AST.

    Args:
        tree: The AST to extract imports from

    Returns:
        List of (module, name) tuples
    """
    imports: ImportList = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for name in node.names:
                imports.append(("", name.name))
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            for name in node.names:
                imports.append((module, name.name))
    return imports


def _group_imports(
    imports: Sequence[ImportPair],
) -> tuple[set[str], set[str], set[str]]:
    """Group imports by type (stdlib, third-party, local).

    Args:
        imports: List of (module, name) tuples

    Returns:
        Tuple of (stdlib_imports, third_party_imports, local_imports) sets
    """
    stdlib_imports: set[str] = set()
    third_party_imports: set[str] = set()
    local_imports: set[str] = set()

    for module, name in imports:
        import_str = f"from {module} import {name}" if module else f"import {name}"
        if module.startswith("pepperpy"):
            local_imports.add(import_str)
        elif "." in module:
            third_party_imports.add(import_str)
        else:
            stdlib_imports.add(import_str)

    return stdlib_imports, third_party_imports, local_imports


def _build_import_section(
    stdlib_imports: set[str],
    third_party_imports: set[str],
    local_imports: set[str],
) -> list[str]:
    """Build the new imports section.

    Args:
        stdlib_imports: Set of standard library imports
        third_party_imports: Set of third-party imports
        local_imports: Set of local imports

    Returns:
        List of import lines
    """
    new_imports: list[str] = []
    if stdlib_imports:
        new_imports.extend(sorted(stdlib_imports))
        new_imports.append("")
    if third_party_imports:
        new_imports.extend(sorted(third_party_imports))
        new_imports.append("")
    if local_imports:
        new_imports.extend(sorted(local_imports))
        new_imports.append("")
    return new_imports


def _find_import_bounds(lines: Sequence[str]) -> tuple[int, int]:
    """Find the start and end lines of the imports section.

    Args:
        lines: The file lines

    Returns:
        Tuple of (start_line, end_line) indices
    """
    start_line = 0
    end_line = 0

    for i, line in enumerate(lines):
        if line.startswith(("import ", "from ")):
            if start_line == 0:
                start_line = i
            end_line = i + 1

    return start_line, end_line


def organize_imports(content: str, imports: ImportList) -> str:
    """Organize imports in a file.

    Args:
        content: The file content
        imports: List of imports to organize

    Returns:
        The organized file content
    """
    # Group imports by type
    stdlib_imports, third_party_imports, local_imports = _group_imports(imports)

    # Build new imports section
    new_imports = _build_import_section(
        stdlib_imports,
        third_party_imports,
        local_imports,
    )

    # Replace old imports with new ones
    lines = content.splitlines()
    start_line, end_line = _find_import_bounds(lines)

    if start_line == end_line:
        return content

    return "\n".join(lines[:start_line] + new_imports + lines[end_line:])


def update_imports(file_path: str) -> None:
    """Update imports in a Python file."""
    try:
        with open(file_path, encoding="utf-8") as f:
            content = f.read()

        tree = ast.parse(content)
        imports = extract_imports(tree)
        if not imports:
            return

        new_content = organize_imports(content, imports)
        if new_content != content:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(new_content)
            logger.info(
                "Updated imports",
                extra={"file": file_path},
            )

    except Exception as e:
        logger.error(
            "Failed to update imports",
            extra={"file": file_path, "error": str(e)},
        )


def update_all_imports(directory: str) -> None:
    """Update imports in all Python files in a directory.

    Args:
        directory: Directory to update
    """
    try:
        for path in Path(directory).rglob("*.py"):
            if path.is_file():
                update_imports(str(path))
    except Exception as e:
        logger.error(
            "Failed to update directory",
            extra={"directory": directory, "error": str(e)},
        )


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Update imports in Python files")
    parser.add_argument("path", help="File or directory to update")
    args = parser.parse_args()

    path = Path(args.path)
    if path.is_file():
        update_imports(str(path))
    elif path.is_dir():
        update_all_imports(str(path))
    else:
        logger.error("Invalid path", extra={"path": str(path)})


if __name__ == "__main__":
    main()
