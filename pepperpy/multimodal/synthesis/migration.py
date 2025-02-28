"""Migration utilities for transitioning to the unified synthesis system.

This module provides utilities to help migrate from the legacy content
implementations to the new unified synthesis system.
"""

import ast
from typing import Dict, List, Tuple


class MigrationHelper:
    """Helper for migrating from legacy content implementations."""

    # Mapping of old import paths to new ones
    IMPORT_MAPPING = {
        "pepperpy.content.synthesis.processors": "pepperpy.synthesis.processors",
        "pepperpy.content.synthesis": "pepperpy.synthesis",
        "pepperpy.content": "pepperpy.synthesis",
    }

    # Mapping of old class names to new ones
    CLASS_MAPPING = {
        "AudioProcessor": "AudioProcessor",
        "ImageProcessor": "ImageProcessor",
        "TextProcessor": "TextProcessor",
        "ContentGenerator": "SynthesisGenerator",
    }

    # Mapping of old method names to new ones
    METHOD_MAPPING = {
        "process_audio": "process_audio",
        "process_image": "process_image",
        "process_text": "process_text",
        "generate": "generate",
    }

    @staticmethod
    def detect_legacy_imports(code: str) -> List[Tuple[str, str, str]]:
        """Detect legacy content imports in code.

        Args:
            code: Source code to analyze

        Returns:
            List of tuples (import_path, imported_name, alias)
        """
        legacy_imports = []
        try:
            tree = ast.parse(code)
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for name in node.names:
                        if name.name.startswith("pepperpy.content"):
                            legacy_imports.append((
                                name.name,
                                name.name,
                                name.asname or name.name,
                            ))
                elif isinstance(node, ast.ImportFrom):
                    if node.module and node.module.startswith("pepperpy.content"):
                        for name in node.names:
                            legacy_imports.append((
                                node.module,
                                name.name,
                                name.asname or name.name,
                            ))
        except SyntaxError:
            # If code can't be parsed, return empty list
            pass
        return legacy_imports

    @staticmethod
    def generate_import_migration(
        legacy_imports: List[Tuple[str, str, str]],
    ) -> Dict[str, str]:
        """Generate migration code for imports.

        Args:
            legacy_imports: List of legacy imports (import_path, imported_name, alias)

        Returns:
            Dictionary mapping old import statements to new ones
        """
        migration_map = {}
        for import_path, imported_name, alias in legacy_imports:
            new_import_path = MigrationHelper.IMPORT_MAPPING.get(import_path)
            if not new_import_path:
                continue

            new_imported_name = MigrationHelper.CLASS_MAPPING.get(
                imported_name, imported_name
            )

            if import_path == imported_name:  # Direct import
                old_import = f"import {import_path}"
                new_import = f"import {new_import_path}"
                if alias != import_path:
                    old_import += f" as {alias}"
                    new_import += f" as {alias}"
            else:  # From import
                old_import = f"from {import_path} import {imported_name}"
                new_import = f"from {new_import_path} import {new_imported_name}"
                if alias != imported_name:
                    old_import += f" as {alias}"
                    new_import += f" as {alias}"

            migration_map[old_import] = new_import

        return migration_map

    @staticmethod
    def generate_migration_guide(code: str) -> str:
        """Generate a migration guide for the given code.

        Args:
            code: Source code to analyze

        Returns:
            Migration guide as a string
        """
        legacy_imports = MigrationHelper.detect_legacy_imports(code)
        import_migrations = MigrationHelper.generate_import_migration(legacy_imports)

        guide = "# Migration Guide for Content to Synthesis\n\n"

        if import_migrations:
            guide += "## Import Changes\n\n"
            guide += "Replace the following imports:\n\n"
            for old_import, new_import in import_migrations.items():
                guide += (
                    f"```python\n# Old\n{old_import}\n\n# New\n{new_import}\n```\n\n"
                )

        guide += "## General Changes\n\n"
        guide += "1. The `content` module has been deprecated in favor of the `synthesis` module.\n"
        guide += "2. All processors have been moved from `content.synthesis.processors` to `synthesis.processors`.\n"
        guide += "3. The API remains largely the same, but some method names may have changed.\n\n"

        guide += "## Example Migration\n\n"
        guide += "```python\n"
        guide += "# Old code\n"
        guide += "from pepperpy.content.synthesis.processors import AudioProcessor\n"
        guide += "processor = AudioProcessor('audio_processor')\n"
        guide += "result = processor.process(audio_data)\n\n"
        guide += "# New code\n"
        guide += "from pepperpy.synthesis.processors import AudioProcessor\n"
        guide += "processor = AudioProcessor('audio_processor')\n"
        guide += "result = processor.process(audio_data)\n"
        guide += "```\n"

        return guide

    @staticmethod
    def print_migration_guide() -> None:
        """Print a general migration guide."""
        guide = """
# Migration Guide: Content Module to Synthesis Module

## Overview

The `pepperpy.content` module has been deprecated and its functionality has been moved to the `pepperpy.synthesis` module. This guide will help you migrate your code to use the new module structure.

## Key Changes

1. Module Renaming:
   - `pepperpy.content.synthesis` → `pepperpy.synthesis`
   - `pepperpy.content.synthesis.processors` → `pepperpy.synthesis.processors`

2. Class Relocations:
   - All processor classes have been moved to the `pepperpy.synthesis.processors` module
   - The API of these classes remains largely the same

## Step-by-Step Migration

### 1. Update Imports

Replace imports from the content module with imports from the synthesis module:

```python
# Old
from pepperpy.content.synthesis.processors import AudioProcessor, ImageProcessor, TextProcessor

# New
from pepperpy.synthesis.processors import AudioProcessor, ImageProcessor, TextProcessor
```

### 2. Update Module References

If you have references to the content module in your code, update them:

```python
# Old
import pepperpy.content.synthesis as content_synthesis

# New
import pepperpy.multimodal.synthesis as synthesis
```

### 3. Check for Method Changes

While most method signatures remain the same, check the documentation for any specific changes.

## Example Migration

### Before:

```python
from pepperpy.content.synthesis.processors import AudioProcessor
from pepperpy.content.synthesis.processors import effects

processor = AudioProcessor("audio_gen", config={"sample_rate": 44100})
audio_data = processor.process(input_data)
audio_data = effects.apply_reverb(audio_data, room_size=0.8)
```

### After:

```python
from pepperpy.synthesis.processors import AudioProcessor
from pepperpy.synthesis.processors import effects

processor = AudioProcessor("audio_gen", config={"sample_rate": 44100})
audio_data = processor.process(input_data)
audio_data = effects.apply_reverb(audio_data, room_size=0.8)
```

## Temporary Compatibility

For backward compatibility, the `pepperpy.content` module currently redirects to the `pepperpy.synthesis` module, but this will be removed in a future version. It's recommended to update your code as soon as possible.
"""
        print(guide)


def migrate_code(file_path: str) -> str:
    """Migrate code in a file from content to synthesis.

    Args:
        file_path: Path to the file to migrate

    Returns:
        Migrated code
    """
    with open(file_path, "r") as f:
        code = f.read()

    legacy_imports = MigrationHelper.detect_legacy_imports(code)
    import_migrations = MigrationHelper.generate_import_migration(legacy_imports)

    for old_import, new_import in import_migrations.items():
        code = code.replace(old_import, new_import)

    return code
