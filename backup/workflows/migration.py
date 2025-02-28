"""Migration utilities for transitioning to the unified workflow system.

This module provides utilities to help migrate from the legacy workflow
implementations to the new unified workflow system.
"""

import ast
import re
from typing import Any, Dict, List, Tuple

from .base import WorkflowDefinition
from .builder import WorkflowBuilder


class MigrationHelper:
    """Helper for migrating from legacy workflow implementations."""

    # Mapping of old import paths to new ones
    IMPORT_MAPPING = {
        "workflows.definition.builder": "pepperpy.agents.workflows",
        "workflows.definition.factory": "pepperpy.agents.workflows",
        "workflows.definition.base": "pepperpy.agents.workflows",
    }

    # Mapping of old class names to new ones
    CLASS_MAPPING = {
        "WorkflowBuilder": "WorkflowBuilder",
        "WorkflowFactory": "WorkflowFactory",
        "WorkflowDefinition": "WorkflowDefinition",
        "WorkflowStep": "WorkflowStep",
        "BaseWorkflow": "BaseWorkflow",
    }

    # Mapping of old method names to new ones
    METHOD_MAPPING = {
        "add_step": "add_step",
        "depends_on": "depends_on",
        "with_metadata": "with_metadata",
        "build": "build",
        "create": "create",
        "create_from_dict": "create_from_dict",
        "load_from_module": "load_from_module",
        "execute": "execute",
    }

    @staticmethod
    def detect_legacy_imports(code: str) -> List[Tuple[str, str, str]]:
        """Detect legacy workflow imports in code.

        Args:
            code: Python code to analyze

        Returns:
            List of tuples (import_path, alias, line)
        """
        legacy_imports = []

        # Parse the code
        try:
            tree = ast.parse(code)
        except SyntaxError:
            return legacy_imports

        # Find import statements
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for name in node.names:
                    if name.name in MigrationHelper.IMPORT_MAPPING:
                        line = code.splitlines()[node.lineno - 1]
                        legacy_imports.append((
                            name.name,
                            name.asname or name.name,
                            line,
                        ))
            elif isinstance(node, ast.ImportFrom):
                if node.module in MigrationHelper.IMPORT_MAPPING:
                    line = code.splitlines()[node.lineno - 1]
                    for name in node.names:
                        legacy_imports.append((
                            f"{node.module}.{name.name}",
                            name.asname or name.name,
                            line,
                        ))

        return legacy_imports

    @staticmethod
    def generate_import_migration(
        legacy_imports: List[Tuple[str, str, str]],
    ) -> Dict[str, str]:
        """Generate migration code for imports.

        Args:
            legacy_imports: List of legacy imports (from detect_legacy_imports)

        Returns:
            Dictionary mapping old import lines to new ones
        """
        migration = {}

        for import_path, alias, line in legacy_imports:
            # Get the module part
            if "." in import_path:
                module, name = import_path.rsplit(".", 1)
            else:
                module, name = import_path, None

            # Generate new import
            if module in MigrationHelper.IMPORT_MAPPING:
                new_module = MigrationHelper.IMPORT_MAPPING[module]
                if name:
                    if alias == name:
                        new_line = f"from {new_module} import {name}"
                    else:
                        new_line = f"from {new_module} import {name} as {alias}"
                else:
                    if alias == module:
                        new_line = f"import {new_module}"
                    else:
                        new_line = f"import {new_module} as {alias}"

                migration[line] = new_line

        return migration

    @staticmethod
    def detect_legacy_usage(code: str) -> List[Tuple[str, int]]:
        """Detect legacy workflow usage in code.

        Args:
            code: Python code to analyze

        Returns:
            List of tuples (usage_type, line_number)
        """
        legacy_usage = []

        # Parse the code
        try:
            tree = ast.parse(code)
        except SyntaxError:
            return legacy_usage

        # Find class instantiations and method calls
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                if (
                    isinstance(node.func, ast.Name)
                    and node.func.id in MigrationHelper.CLASS_MAPPING
                ):
                    legacy_usage.append(("class", node.lineno))
                elif (
                    isinstance(node.func, ast.Attribute)
                    and node.func.attr in MigrationHelper.METHOD_MAPPING
                ):
                    legacy_usage.append(("method", node.lineno))

        return legacy_usage

    @staticmethod
    def convert_legacy_workflow(legacy_definition: Any) -> WorkflowDefinition:
        """Convert a legacy workflow definition to the new format.

        Args:
            legacy_definition: Legacy workflow definition

        Returns:
            New workflow definition

        Raises:
            ValueError: If conversion fails
        """
        # Check if it's already a new-style definition
        if isinstance(legacy_definition, WorkflowDefinition):
            return legacy_definition

        # Check if it has the expected attributes
        if not hasattr(legacy_definition, "name") or not hasattr(
            legacy_definition, "steps"
        ):
            raise ValueError("Legacy definition does not have required attributes")

        # Create a new definition
        builder = WorkflowBuilder(legacy_definition.name)

        # Add metadata if present
        if hasattr(legacy_definition, "metadata"):
            for key, value in legacy_definition.metadata.items():
                builder.with_metadata(key, value)

        # Add steps
        for step_id, legacy_step in legacy_definition.steps.items():
            # Extract step attributes
            name = getattr(legacy_step, "name", step_id)
            action = getattr(legacy_step, "action", "unknown")
            parameters = getattr(legacy_step, "parameters", {})

            # Add step
            builder.add_step(step_id, name, action, parameters)

            # Add dependencies if present
            dependencies = getattr(legacy_step, "dependencies", [])
            if dependencies:
                builder.depends_on(dependencies)

            # Add metadata if present
            if hasattr(legacy_step, "metadata"):
                for key, value in legacy_step.metadata.items():
                    builder.with_metadata(key, value)

        return builder.build()

    @staticmethod
    def generate_migration_guide(code: str) -> str:
        """Generate a migration guide for the given code.

        Args:
            code: Python code to analyze

        Returns:
            Migration guide as a string
        """
        legacy_imports = MigrationHelper.detect_legacy_imports(code)
        legacy_usage = MigrationHelper.detect_legacy_usage(code)
        import_migration = MigrationHelper.generate_import_migration(legacy_imports)

        guide = "# Migration Guide for Workflow System\n\n"

        if not legacy_imports and not legacy_usage:
            guide += "No legacy workflow code detected.\n"
            return guide

        guide += "## Import Changes\n\n"
        if legacy_imports:
            guide += "Replace the following imports:\n\n"
            for old_line, new_line in import_migration.items():
                guide += f"```python\n# Old\n{old_line}\n\n# New\n{new_line}\n```\n\n"
        else:
            guide += "No legacy imports detected.\n\n"

        guide += "## API Changes\n\n"
        if legacy_usage:
            guide += "The following lines may need updates:\n\n"
            for usage_type, line_number in legacy_usage:
                line = code.splitlines()[line_number - 1]
                guide += f"- Line {line_number}: `{line.strip()}`\n"

            guide += "\n### Key API Changes\n\n"
            guide += "- Workflow execution is now async\n"
            guide += "- Use the global `default_factory` for convenience\n"
            guide += "- The builder API has more fluent methods\n"
        else:
            guide += "No legacy API usage detected.\n\n"

        guide += "## Migration Steps\n\n"
        guide += "1. Update imports as shown above\n"
        guide += "2. Replace synchronous execution with async/await\n"
        guide += "3. Use the new builder API for workflow construction\n"
        guide += "4. Register custom workflow implementations with the factory\n"

        return guide

    @staticmethod
    def migrate_code(code: str) -> str:
        """Attempt to automatically migrate legacy workflow code.

        Args:
            code: Python code to migrate

        Returns:
            Migrated code
        """
        legacy_imports = MigrationHelper.detect_legacy_imports(code)
        import_migration = MigrationHelper.generate_import_migration(legacy_imports)

        # Replace imports
        migrated_code = code
        for old_line, new_line in import_migration.items():
            migrated_code = migrated_code.replace(old_line, new_line)

        # Add async/await where needed
        migrated_code = re.sub(
            r"def\s+execute\s*\(", "async def execute(", migrated_code
        )
        migrated_code = re.sub(
            r"(\w+)\.execute\s*\(", r"await \1.execute(", migrated_code
        )

        return migrated_code
