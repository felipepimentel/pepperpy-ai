#!/usr/bin/env python3
"""Script to update imports for moved data files."""

import os
from pathlib import Path
import re


def update_imports(file_path: Path) -> None:
    """Update imports in a file."""
    with open(file_path, "r") as f:
        content = f.read()

    # Update imports
    replacements = {
        "from pepperpy.providers.vector_store.base": "from pepperpy.providers.vector_store",
        "from pepperpy.data.processing": "from pepperpy.core.data.processing",
        "from pepperpy.data.dynamic_sources": "from pepperpy.core.data.sources",
        "import pepperpy.data.vector": "import pepperpy.providers.vector_store",
        "import pepperpy.data.processing": "import pepperpy.core.data.processing",
        "import pepperpy.data.dynamic_sources": "import pepperpy.core.data.sources",
    }

    new_content = content
    for old, new in replacements.items():
        new_content = new_content.replace(old, new)

    if new_content != content:
        print(f"Updating imports in {file_path}")
        with open(file_path, "w") as f:
            f.write(new_content)


def main():
    """Main function to update imports in all Python files."""
    root = Path("pepperpy")
    for file_path in root.rglob("*.py"):
        update_imports(file_path)


if __name__ == "__main__":
    main()
