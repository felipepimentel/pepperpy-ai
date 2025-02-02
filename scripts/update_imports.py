#!/usr/bin/env python3
"""Import statement updater.

Updates import statements in Python files to match new module structure.
"""

import os
from pathlib import Path

# Map of old imports to new imports
IMPORT_MAP = {
    "from pepperpy.providers.vector_store.base": (
        "from pepperpy.providers.vector_store.base"
    ),
    "from pepperpy.persistence.storage.document": (
        "from pepperpy.persistence.storage.document"
    ),
    "from pepperpy.persistence.storage.chunking": (
        "from pepperpy.persistence.storage.chunking"
    ),
    "from pepperpy.persistence.storage.conversation": (
        "from pepperpy.persistence.storage.conversation"
    ),
    "from pepperpy.providers.memory": "from pepperpy.providers.memory",
    "from pepperpy.persistence.storage.rag": ("from pepperpy.persistence.storage.rag"),
    "from pepperpy.providers.embedding": "from pepperpy.providers.embedding",
    "from pepperpy.providers.vector_store": ("from pepperpy.providers.vector_store"),
}


def update_imports(file_path: str) -> None:
    """Update imports in a file.

    Args:
        file_path: Path to file to update
    """
    with open(file_path) as f:
        content = f.read()

    updated = False
    for old, new in IMPORT_MAP.items():
        if old in content:
            content = content.replace(old, new)
            updated = True
            print(f"Updated {old} -> {new} in {file_path}")

    if updated:
        with open(file_path, "w") as f:
            f.write(content)


def main() -> None:
    """Main entry point."""
    workspace = Path(__file__).parent.parent

    # Files to exclude
    exclude = {".git", "__pycache__", "venv", "env", ".venv"}

    # Find all Python files
    for root, dirs, files in os.walk(workspace):
        # Skip excluded directories
        dirs[:] = [d for d in dirs if d not in exclude]

        for file in files:
            if file.endswith(".py"):
                file_path = os.path.join(root, file)
                update_imports(file_path)


if __name__ == "__main__":
    main()
