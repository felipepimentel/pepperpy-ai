#!/usr/bin/env python3
"""
Migrate base.py files to main module.

This script moves base.py files from subdirectories to the main module level
when they are the only file (besides __init__.py) in the directory.
"""

import os
import shutil
from pathlib import Path

# List of modules to migrate (directories that contain only base.py and __init__.py)
# Reminder: we're excluding 'tools' because it has subdirectories
MODULES_TO_MIGRATE = [
    "cache",
    "llm",
    "embeddings",
    "hub",
    "storage",
]


def migrate_base_file(module_name):
    """Migrate base.py file to main module level."""
    base_file = Path(f"pepperpy/{module_name}/base.py")
    init_file = Path(f"pepperpy/{module_name}/__init__.py")
    target_file = Path(f"pepperpy/{module_name}.py")

    # Check if files exist
    if not base_file.exists():
        print(f"Warning: {base_file} does not exist, skipping.")
        return

    if not init_file.exists():
        print(f"Warning: {init_file} does not exist, skipping.")
        return

    # Create backup directory
    backup_dir = Path("backup/base_migration")
    backup_dir.mkdir(exist_ok=True, parents=True)

    # Backup files
    shutil.copy2(base_file, backup_dir / f"{module_name}_base.py.bak")
    shutil.copy2(init_file, backup_dir / f"{module_name}_init.py.bak")
    print(f"Backed up {base_file} and {init_file}")

    # Read content of files
    with open(base_file) as f:
        base_content = f.read()

    with open(init_file) as f:
        init_content = f.read()

    # Extract imports from __init__.py
    import_lines = []
    export_lines = []

    for line in init_content.split("\n"):
        if line.startswith("from .base import"):
            # Convert "from .base import X" to imports in the new file
            # We'll add these later to the new file
            imports = line.replace("from .base import ", "").split(", ")
            export_lines.extend(imports)
        elif line.startswith("import") or line.startswith("from"):
            import_lines.append(line)

    # Create new file with combined content
    with open(target_file, "w") as f:
        # Add docstring
        f.write(f'"""{module_name.title()} module for PepperPy.\n\n')
        f.write("This module was migrated from a subdirectory structure.\n")
        f.write('"""\n\n')

        # Add imports from __init__.py
        if import_lines:
            for line in import_lines:
                if "from .base import" not in line:
                    f.write(line + "\n")
            f.write("\n")

        # Add base.py content
        f.write(base_content)

        # Ensure file ends with newline
        if not base_content.endswith("\n"):
            f.write("\n")

    print(f"Created {target_file}")

    # Update __init__.py to import from new file
    new_init_content = []

    # Copy the docstring if present
    in_docstring = False
    for line in init_content.split("\n"):
        if line.startswith('"""') or line.startswith("'''"):
            in_docstring = not in_docstring
            new_init_content.append(line)
        elif in_docstring:
            new_init_content.append(line)
        elif not (
            line.startswith("from .base import") or line.startswith("from . import")
        ):
            if line.strip() and not line.startswith("#"):
                # Skip non-docstring, non-import lines that aren't comments
                pass
            else:
                new_init_content.append(line)

    # Add imports from the new module file
    if export_lines:
        new_init_content.append(f"from .. import {module_name}")
        new_init_content.append("")

        # Add re-exports
        exports_str = ", ".join(export_lines)
        new_init_content.append(
            f"__all__ = [{', '.join([f'"{x.strip()}"' for x in export_lines])}]"
        )

    # Update the __init__.py in the module directory
    with open(init_file, "w") as f:
        f.write("\n".join(new_init_content))

    print(f"Updated {init_file}")

    # Remove base.py
    os.remove(base_file)
    print(f"Removed {base_file}")

    print(f"Migration of {module_name} completed.")


def migrate_all():
    """Migrate all base.py files."""
    for module in MODULES_TO_MIGRATE:
        print(f"\nMigrating {module}...")
        migrate_base_file(module)


if __name__ == "__main__":
    # Create backup directory
    Path("backup/base_migration").mkdir(exist_ok=True, parents=True)

    # Migrate all base.py files
    migrate_all()

    print("\nDone! All base.py files migrated to main module level.")
