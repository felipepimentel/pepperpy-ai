#!/usr/bin/env python3
"""Import Management Script.

This script provides a unified interface for managing imports across the project.
It handles:
- Updating import paths after module migrations
- Validating import patterns
- Fixing common import issues
"""

import argparse
import os
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from pepperpy.monitoring import logger


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

    def __init__(self, workspace: Path):
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
                        file=str(file_path),
                        old=mapping.old_pattern,
                        new=mapping.new_pattern,
                    )

            if updated:
                with open(file_path, "w") as f:
                    f.write(content)
                self.updated_files.add(file_path)

        except Exception as e:
            logger.error("Failed to update file", file=str(file_path), error=str(e))

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
                updated_files=len(self.updated_files),
                files=[str(f) for f in self.updated_files],
            )
        else:
            logger.info("No files needed updating")


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Update imports across the project")
    parser.add_argument(
        "--type",
        type=str,
        choices=[t.value for t in ImportType],
        help="Type of imports to update",
    )
    parser.add_argument(
        "--workspace",
        type=Path,
        default=Path(__file__).parent.parent.parent,
        help="Workspace root directory",
    )
    args = parser.parse_args()

    updater = ImportUpdater(args.workspace)
    updater.update_imports(ImportType(args.type))
    updater.report()


if __name__ == "__main__":
    main()
