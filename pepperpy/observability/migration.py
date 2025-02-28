"""Migration utilities for transitioning to the unified observability system.

This module provides utilities to help migrate from the legacy monitoring
implementations to the new unified observability system.
"""

import ast
import re
from typing import Dict, List, Tuple


class MigrationHelper:
    """Helper for migrating from legacy monitoring implementations."""

    # Mapping of old import paths to new ones
    IMPORT_MAPPING = {
        "pepperpy.monitoring": "pepperpy.observability",
        "pepperpy.monitoring.metrics": "pepperpy.observability.metrics",
    }

    # Mapping of old class names to new ones
    CLASS_MAPPING = {
        "MetricsManager": "MetricsRegistry",
        "Counter": "Counter",
        "Histogram": "Histogram",
        "Gauge": "Gauge",
    }

    # Mapping of old method names to new ones
    METHOD_MAPPING = {
        "create_counter": "register_counter",
        "create_histogram": "register_histogram",
        "create_gauge": "register_gauge",
        "get_counter": "get_counter",
        "get_histogram": "get_histogram",
        "get_gauge": "get_gauge",
    }

    @staticmethod
    def detect_legacy_imports(code: str) -> List[Tuple[str, str, str]]:
        """Detect legacy monitoring imports in code.

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
                        if name.name.startswith("pepperpy.monitoring"):
                            legacy_imports.append((
                                name.name,
                                name.name,
                                name.asname or name.name,
                            ))
                elif isinstance(node, ast.ImportFrom):
                    if node.module and node.module.startswith("pepperpy.monitoring"):
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

        guide = "# Migration Guide for Monitoring to Observability\n\n"

        if import_migrations:
            guide += "## Import Changes\n\n"
            guide += "Replace the following imports:\n\n"
            for old_import, new_import in import_migrations.items():
                guide += (
                    f"```python\n# Old\n{old_import}\n\n# New\n{new_import}\n```\n\n"
                )

        guide += "## General Changes\n\n"
        guide += "1. The `monitoring` module has been deprecated in favor of the `observability` module.\n"
        guide += (
            "2. The `MetricsManager` class has been replaced with `MetricsRegistry`.\n"
        )
        guide += "3. Method names have changed (e.g., `create_counter` → `register_counter`).\n\n"

        guide += "## Example Migration\n\n"
        guide += "```python\n"
        guide += "# Old code\n"
        guide += "from pepperpy.monitoring.metrics import MetricsManager\n"
        guide += "metrics_manager = MetricsManager()\n"
        guide += (
            "counter = metrics_manager.create_counter('requests', 'Request counter')\n"
        )
        guide += "counter.increment()\n\n"
        guide += "# New code\n"
        guide += "from pepperpy.observability.metrics import MetricsRegistry\n"
        guide += "metrics_registry = MetricsRegistry()\n"
        guide += "counter = metrics_registry.register_counter('requests', 'Request counter')\n"
        guide += "counter.increment()\n"
        guide += "```\n"

        return guide

    @staticmethod
    def print_migration_guide() -> None:
        """Print a general migration guide."""
        guide = """
# Migration Guide: Monitoring Module to Observability Module

## Overview

The `pepperpy.monitoring` module has been deprecated and its functionality has been moved to the `pepperpy.observability` module. This guide will help you migrate your code to use the new module structure.

## Key Changes

1. Module Renaming:
   - `pepperpy.monitoring` → `pepperpy.observability`
   - `pepperpy.monitoring.metrics` → `pepperpy.observability.metrics`

2. Class Renaming:
   - `MetricsManager` → `MetricsRegistry`

3. Method Renaming:
   - `create_counter` → `register_counter`
   - `create_histogram` → `register_histogram`
   - `create_gauge` → `register_gauge`

## Step-by-Step Migration

### 1. Update Imports

Replace imports from the monitoring module with imports from the observability module:

```python
# Old
from pepperpy.monitoring.metrics import MetricsManager, Counter, Histogram

# New
from pepperpy.observability.metrics import MetricsRegistry, Counter, Histogram
```

### 2. Update Class Usage

Replace `MetricsManager` with `MetricsRegistry`:

```python
# Old
metrics_manager = MetricsManager()

# New
metrics_registry = MetricsRegistry()
```

### 3. Update Method Calls

Replace method calls with their new equivalents:

```python
# Old
counter = metrics_manager.create_counter('requests', 'Request counter')
histogram = metrics_manager.create_histogram('latency', [0.1, 0.5, 1.0], 'Latency histogram')

# New
counter = metrics_registry.register_counter('requests', 'Request counter')
histogram = metrics_registry.register_histogram('latency', [0.1, 0.5, 1.0], 'Latency histogram')
```

## Example Migration

### Before:

```python
from pepperpy.monitoring.metrics import MetricsManager

# Create metrics manager
metrics_manager = MetricsManager()

# Create metrics
request_counter = metrics_manager.create_counter('requests', 'Request counter')
error_counter = metrics_manager.create_counter('errors', 'Error counter')
latency_histogram = metrics_manager.create_histogram('latency', [0.1, 0.5, 1.0], 'Latency histogram')

# Use metrics
request_counter.increment()
error_counter.increment(5)
latency_histogram.observe(0.75)
```

### After:

```python
from pepperpy.observability.metrics import MetricsRegistry

# Create metrics registry
metrics_registry = MetricsRegistry()

# Create metrics
request_counter = metrics_registry.register_counter('requests', 'Request counter')
error_counter = metrics_registry.register_counter('errors', 'Error counter')
latency_histogram = metrics_registry.register_histogram('latency', [0.1, 0.5, 1.0], 'Latency histogram')

# Use metrics
request_counter.increment()
error_counter.increment(5)
latency_histogram.observe(0.75)
```

## Temporary Compatibility

For backward compatibility, the `pepperpy.monitoring` module currently redirects to the `pepperpy.observability` module, but this will be removed in a future version. It's recommended to update your code as soon as possible.
"""
        print(guide)


def migrate_code(file_path: str) -> str:
    """Migrate code in a file from monitoring to observability.

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

    # Replace class names
    for old_class, new_class in MigrationHelper.CLASS_MAPPING.items():
        if old_class != new_class:
            pattern = r"\b" + re.escape(old_class) + r"\b"
            code = re.sub(pattern, new_class, code)

    # Replace method names
    for old_method, new_method in MigrationHelper.METHOD_MAPPING.items():
        if old_method != new_method:
            pattern = r"\.(" + re.escape(old_method) + r")\("
            code = re.sub(pattern, "." + new_method + "(", code)

    return code
