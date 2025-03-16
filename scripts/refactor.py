#!/usr/bin/env python
"""
PepperPy Refactor Script

A comprehensive tool for automating the PepperPy library refactoring process.
This script combines functionality from various existing scripts and implements
new refactoring features to assist with the vertical restructuring task.

Usage:
    python scripts/refactor.py [command] [options]

Commands:
    update-imports     - Update import statements throughout the codebase
    restructure-files  - Move files according to the new structure
    consolidate        - Consolidate multiple files into a single module
    validate           - Validate the project structure
    find-unused        - Find potentially unused code
    clean              - Remove empty directories and dead files
    run-task           - Run a specific task from TASK-012

Examples:
    python scripts/refactor.py update-imports --old "pepperpy.llm.errors" --new "pepperpy.core.errors"
    python scripts/refactor.py restructure-files --mapping mapping.json
    python scripts/refactor.py consolidate --files "file1.py,file2.py" --output "output.py"
    python scripts/refactor.py validate
    python scripts/refactor.py find-unused
    python scripts/refactor.py clean
    python scripts/refactor.py run-task --task "2.1.1"
"""

import argparse
import ast
import importlib.util
import json
import logging
import os
import re
import shutil
import sys
from pathlib import Path
from typing import Dict, List

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("refactor")

# Define the project root
PROJECT_ROOT = Path(__file__).parent.parent

# Constants
DEAD_FILES = ["public.py", "core.py"]
REQUIRED_INIT = ["__init__.py"]

# Task mapping - maps task IDs to functions that implement them
TASK_MAP = {}


def register_task(task_id):
    """Decorator to register a function as a task handler."""

    def decorator(func):
        TASK_MAP[task_id] = func
        return func

    return decorator


def update_imports(directory: str, old_import_map: Dict[str, str]) -> None:
    """
    Update imports in all Python files in a directory.

    Args:
        directory: Directory to process
        old_import_map: Dictionary with {old_import: new_import}
    """
    logger.info(f"Updating imports in {directory}...")

    files = Path(directory).glob("**/*.py")
    for file in files:
        content = file.read_text(encoding="utf-8")
        updated = content

        for old, new in old_import_map.items():
            # Update direct imports (from x import y, import x)
            pattern = rf"(from|import)\s+{re.escape(old)}(\s|\.|,|$)"
            updated = re.sub(pattern, rf"\1 {new}\2", updated)

        if content != updated:
            file.write_text(updated, encoding="utf-8")
            logger.info(f"Updated imports in: {file}")


def restructure_files(file_mapping: Dict[str, str]) -> None:
    """
    Move files according to mapping and ensure __init__.py exists.

    Args:
        file_mapping: Dictionary with {old_path: new_path}
    """
    logger.info("Restructuring files according to mapping...")

    for old_path, new_path in file_mapping.items():
        old = Path(old_path)
        new = Path(new_path)

        if not old.exists():
            logger.warning(f"Warning: {old} does not exist.")
            continue

        # Create intermediate directories
        new.parent.mkdir(parents=True, exist_ok=True)

        # Create __init__.py in each directory
        for parent in new.parents:
            init_file = parent / "__init__.py"
            if not init_file.exists() and parent.name:
                init_file.touch()
                logger.info(f"Created: {init_file}")

        # Move the file
        shutil.copy2(old, new)
        logger.info(f"Moved: {old} -> {new}")


def consolidate_modules(
    files_to_consolidate: List[str], output_file: str, header: str = ""
) -> None:
    """
    Consolidate multiple files into a single file.

    Args:
        files_to_consolidate: List of file paths to consolidate
        output_file: Path of the output file
        header: Optional text to add at the beginning of the file
    """
    logger.info(f"Consolidating modules into {output_file}...")

    output = Path(output_file)
    content = header + "\n\n" if header else ""

    for file in files_to_consolidate:
        path = Path(file)
        if not path.exists():
            logger.warning(f"Warning: {path} does not exist.")
            continue

        file_content = path.read_text(encoding="utf-8")

        content += f"# From {path}\n"
        content += file_content
        content += "\n\n"

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(content, encoding="utf-8")
    logger.info(f"Consolidated into: {output}")


def validate_structure(directory: str) -> None:
    """
    Validate the project structure after refactoring.

    Args:
        directory: Directory to validate
    """
    logger.info(f"Validating structure of {directory}...")

    # Check for dead files
    dead_files = []
    for pattern in DEAD_FILES:
        dead_files.extend(list(Path(directory).glob(f"**/{pattern}")))

    if dead_files:
        logger.warning("Found files that should be removed:")
        for file in dead_files:
            logger.warning(f"  - {file}")

    # Test importability
    try:
        spec = importlib.util.find_spec(directory)
        if spec:
            logger.info(f"Module {directory} can be imported successfully.")
        else:
            logger.warning(f"Failed to find module {directory}.")
    except Exception as e:
        logger.error(f"Error importing {directory}: {e}")

    # Check for empty directories
    empty_dirs = []
    for path in Path(directory).glob("**"):
        if path.is_dir() and not list(path.iterdir()):
            empty_dirs.append(path)

    if empty_dirs:
        logger.warning("Empty directories found:")
        for dir_path in empty_dirs:
            logger.warning(f"  - {dir_path}")


def find_unused_code(directory: str) -> None:
    """
    Detect potentially unused code.

    Args:
        directory: Directory to analyze
    """
    logger.info(f"Finding potentially unused code in {directory}...")

    # Collect all definitions and imports
    all_definitions = {}
    all_imports = {}

    # Collect all usages
    all_usages = set()

    files = list(Path(directory).glob("**/*.py"))

    # First pass: collect definitions
    for file in files:
        try:
            with open(file, "r", encoding="utf-8") as f:
                tree = ast.parse(f.read(), filename=str(file))

            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                    all_definitions[node.name] = str(file)
                elif isinstance(node, ast.Import):
                    for name in node.names:
                        all_imports[name.name] = str(file)
                elif isinstance(node, ast.ImportFrom):
                    module = node.module if node.module else ""
                    for name in node.names:
                        all_imports[f"{module}.{name.name}"] = str(file)
        except Exception as e:
            logger.error(f"Error analyzing {file}: {e}")

    # Second pass: collect usages
    for file in files:
        try:
            with open(file, "r", encoding="utf-8") as f:
                content = f.read()

            for definition in all_definitions:
                if definition in content:
                    all_usages.add(definition)
        except Exception as e:
            logger.error(f"Error analyzing usages in {file}: {e}")

    # Find unused code
    unused = set(all_definitions.keys()) - all_usages

    if unused:
        logger.warning("Potentially unused code:")
        for item in unused:
            logger.warning(f"  - {item} in {all_definitions[item]}")


def clean_directories(directory: str) -> None:
    """
    Remove empty directories and dead files.

    Args:
        directory: Directory to clean
    """
    logger.info(f"Cleaning {directory}...")

    # Remove dead files
    dead_files = []
    for pattern in DEAD_FILES:
        dead_files.extend(list(Path(directory).glob(f"**/{pattern}")))

    for file in dead_files:
        file.unlink()
        logger.info(f"Removed dead file: {file}")

    # Remove empty directories
    for root, dirs, files in os.walk(directory, topdown=False):
        for dir_name in dirs:
            dir_path = os.path.join(root, dir_name)
            if not os.listdir(dir_path):
                os.rmdir(dir_path)
                logger.info(f"Removed empty directory: {dir_path}")


def fix_imports_legacy(directory: str) -> None:
    """
    Fix imports using patterns from the original fix_imports.py script.

    Args:
        directory: Directory to process
    """
    logger.info(f"Fixing imports in {directory} (legacy method)...")

    # Get all Python files
    python_files = list(Path(directory).glob("**/*.py"))
    total_files = len(python_files)

    # Patterns to replace (from original fix_imports.py)
    patterns = [
        (r"from pepperpy\.", r"from pepperpy."),  # Keep absolute imports
        (r"import pepperpy\.", r"import pepperpy."),  # Keep absolute imports
        (r"from \.\.", r"from pepperpy."),  # Replace relative imports with absolute
        (r"from \.", r"from pepperpy."),  # Replace relative imports with absolute
    ]

    # Process each file
    for i, file_path in enumerate(python_files):
        logger.info(f"Processing file {i + 1}/{total_files}: {file_path}")

        # Read the file
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Apply replacements
        new_content = content
        for pattern, replacement in patterns:
            new_content = re.sub(pattern, replacement, new_content)

        # Write the file if changes were made
        if new_content != content:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(new_content)
            logger.info(f"  Updated imports in {file_path}")


# Register specific task implementations
@register_task("1.1.1")
def task_1_1_1():
    """Task 1.1.1: Consolidate exceptions from various error files into core/errors.py"""
    files_to_consolidate = [
        "pepperpy/llm/errors.py",
        "pepperpy/rag/errors.py",
        # Add other error files as needed
    ]
    output_file = "pepperpy/core/errors.py"
    header = """#!/usr/bin/env python
# -*- coding: utf-8 -*-
\"\"\"
Core exceptions for PepperPy.

This module centralizes all exceptions used throughout the PepperPy framework.
\"\"\"

from typing import Any, Dict, Optional, Type, Union

"""
    consolidate_modules(files_to_consolidate, output_file, header)

    # Update imports to reference the new error location
    error_import_map = {
        "pepperpy.llm.errors": "pepperpy.core.errors",
        "pepperpy.rag.errors": "pepperpy.core.errors",
        # Add other mappings as needed
    }
    update_imports("pepperpy", error_import_map)


@register_task("1.2.1")
def task_1_2_1():
    """Task 1.2.1: Consolidate events functionality into infra/events.py"""
    files_to_consolidate = [
        "pepperpy/events/base.py",
        "pepperpy/events/handlers.py",
        "pepperpy/events/registry.py",
        # Add other event files as needed
    ]
    output_file = "pepperpy/infra/events.py"
    header = """#!/usr/bin/env python
# -*- coding: utf-8 -*-
\"\"\"
Event system for PepperPy.

This module provides a centralized event system for the PepperPy framework.
\"\"\"

from typing import Any, Callable, Dict, List, Optional, Set, Type, Union

"""
    consolidate_modules(files_to_consolidate, output_file, header)

    # Update imports to reference the new events location
    events_import_map = {
        "pepperpy.events": "pepperpy.infra.events",
        # Add other mappings as needed
    }
    update_imports("pepperpy", events_import_map)


@register_task("1.2.2")
def task_1_2_2():
    """Task 1.2.2: Consolidate streaming functionality into infra/streaming.py"""
    files_to_consolidate = [
        "pepperpy/streaming/base.py",
        "pepperpy/streaming/handlers.py",
        "pepperpy/streaming/processors.py",
        # Add other streaming files as needed
    ]
    output_file = "pepperpy/infra/streaming.py"
    header = """#!/usr/bin/env python
# -*- coding: utf-8 -*-
\"\"\"
Streaming functionality for PepperPy.

This module provides streaming capabilities for the PepperPy framework.
\"\"\"

from typing import Any, Callable, Dict, Generator, Iterable, List, Optional, Union

"""
    consolidate_modules(files_to_consolidate, output_file, header)

    # Update imports to reference the new streaming location
    streaming_import_map = {
        "pepperpy.streaming": "pepperpy.infra.streaming",
        # Add other mappings as needed
    }
    update_imports("pepperpy", streaming_import_map)


@register_task("2.1.1")
def task_2_1_1():
    """Task 2.1.1: Organize embedding functionality in llm/embedding.py"""
    # This task requires organizing the embedding code
    files_to_consolidate = [
        "pepperpy/llm/embedding.py",
        # Add other embedding files if they exist
    ]
    output_file = "pepperpy/llm/embedding.py"
    header = """#!/usr/bin/env python
# -*- coding: utf-8 -*-
\"\"\"
Embedding functionality for LLM operations.

This module provides embedding capabilities for the PepperPy framework.
\"\"\"

from typing import Any, Dict, List, Optional, Union

"""
    consolidate_modules(files_to_consolidate, output_file, header)


@register_task("2.1.2")
def task_2_1_2():
    """Task 2.1.2: Implement LLM providers"""
    # Create provider directory structure
    providers_dir = Path("pepperpy/llm/providers")
    providers_dir.mkdir(parents=True, exist_ok=True)

    # Create __init__.py with factory and API
    init_content = """#!/usr/bin/env python
# -*- coding: utf-8 -*-
\"\"\"
LLM providers for PepperPy.

This module provides access to various LLM providers through a unified API.
\"\"\"

from typing import Any, Dict, Optional, Type, Union

from pepperpy.llm.providers.base import LLMProvider

__all__ = ["create_model", "get_provider", "list_providers", "LLMProvider"]

_PROVIDERS = {}  # Registry of providers

def register_provider(name: str, provider_class: Type[LLMProvider]) -> None:
    \"\"\"Register a new LLM provider.\"\"\"
    _PROVIDERS[name] = provider_class

def get_provider(name: str) -> Type[LLMProvider]:
    \"\"\"Get a provider class by name.\"\"\"
    if name not in _PROVIDERS:
        raise ValueError(f"Provider {name} not found")
    return _PROVIDERS[name]

def list_providers() -> Dict[str, Type[LLMProvider]]:
    \"\"\"List all available providers.\"\"\"
    return _PROVIDERS.copy()

def create_model(provider_name: str, **kwargs: Any) -> LLMProvider:
    \"\"\"Create a new LLM model instance from the specified provider.\"\"\"
    provider_class = get_provider(provider_name)
    return provider_class(**kwargs)

# Import and register all providers
# This will be populated as providers are implemented
"""
    (providers_dir / "__init__.py").write_text(init_content, encoding="utf-8")

    # Create base.py with provider base classes
    base_content = """#!/usr/bin/env python
# -*- coding: utf-8 -*-
\"\"\"
Base classes for LLM providers.

This module defines the base interfaces for LLM providers.
\"\"\"

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union

class LLMProvider(ABC):
    \"\"\"Base class for all LLM providers.\"\"\"
    
    @abstractmethod
    def generate(self, prompt: str, **kwargs: Any) -> str:
        \"\"\"Generate text from a prompt.\"\"\"
        pass
    
    @abstractmethod
    def generate_stream(self, prompt: str, **kwargs: Any) -> Any:
        \"\"\"Generate text from a prompt as a stream.\"\"\"
        pass
    
    @abstractmethod
    def embed(self, text: str, **kwargs: Any) -> List[float]:
        \"\"\"Generate embeddings for text.\"\"\"
        pass
"""
    (providers_dir / "base.py").write_text(base_content, encoding="utf-8")


@register_task("2.2.1")
def task_2_2_1():
    """Task 2.2.1: Finalize RAG models and essential functionality"""
    files_to_consolidate = [
        "pepperpy/rag/models.py",
        # Add other relevant RAG model files
    ]
    output_file = "pepperpy/rag/models.py"
    header = """#!/usr/bin/env python
# -*- coding: utf-8 -*-
\"\"\"
Core models for RAG operations.

This module defines the core models and functionality for Retrieval Augmented Generation.
\"\"\"

from typing import Any, Dict, List, Optional, Union

"""
    consolidate_modules(files_to_consolidate, output_file, header)


def run_task(task_id: str) -> None:
    """
    Run a specific task by ID.

    Args:
        task_id: The ID of the task to run
    """
    if task_id in TASK_MAP:
        logger.info(f"Running task {task_id}...")
        TASK_MAP[task_id]()
        logger.info(f"Task {task_id} completed.")
    else:
        logger.error(
            f"Task {task_id} not found. Available tasks: {', '.join(TASK_MAP.keys())}"
        )


def update_task_file(task_file: str) -> None:
    """
    Update the task file with refactor.py commands for each task.

    Args:
        task_file: Path to the task file
    """
    logger.info(f"Updating task file: {task_file}")

    task_path = Path(task_file)
    if not task_path.exists():
        logger.error(f"Task file {task_file} not found.")
        return

    content = task_path.read_text(encoding="utf-8")

    # Define patterns for tasks
    task_patterns = [
        (
            r"- \[ \] \*\*(.+?)\*\* - (.+?)$",
            r"- [ ] **\1** - \2\n  - `python scripts/refactor.py run-task --task \"{0}\"`",
        ),
    ]

    # Apply replacements for each registered task
    updated_content = content
    for task_id, task_func in TASK_MAP.items():
        for pattern, replacement in task_patterns:
            updated_content = re.sub(
                pattern,
                replacement.format(task_id),
                updated_content,
                flags=re.MULTILINE,
            )

    # Write updated content
    if content != updated_content:
        task_path.write_text(updated_content, encoding="utf-8")
        logger.info(f"Updated {task_file} with refactor.py commands.")
    else:
        logger.info(f"No updates needed for {task_file}.")


def main() -> int:
    """Main function."""
    parser = argparse.ArgumentParser(
        description="PepperPy Refactor Script",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Update imports command
    update_imports_parser = subparsers.add_parser(
        "update-imports", help="Update import statements"
    )
    update_imports_parser.add_argument(
        "--mapping", help="JSON file with old->new import mapping"
    )
    update_imports_parser.add_argument("--old", help="Old import path")
    update_imports_parser.add_argument("--new", help="New import path")
    update_imports_parser.add_argument(
        "--directory", default="pepperpy", help="Directory to process"
    )

    # Restructure files command
    restructure_parser = subparsers.add_parser(
        "restructure-files", help="Restructure files"
    )
    restructure_parser.add_argument(
        "--mapping", required=True, help="JSON file with old->new file mapping"
    )

    # Consolidate command
    consolidate_parser = subparsers.add_parser("consolidate", help="Consolidate files")
    consolidate_parser.add_argument(
        "--files", required=True, help="Comma-separated list of files to consolidate"
    )
    consolidate_parser.add_argument("--output", required=True, help="Output file path")
    consolidate_parser.add_argument(
        "--header", help="Optional header to add to the consolidated file"
    )

    # Validate command
    validate_parser = subparsers.add_parser("validate", help="Validate structure")
    validate_parser.add_argument(
        "--directory", default="pepperpy", help="Directory to validate"
    )

    # Find unused code command
    unused_parser = subparsers.add_parser("find-unused", help="Find unused code")
    unused_parser.add_argument(
        "--directory", default="pepperpy", help="Directory to analyze"
    )

    # Clean command
    clean_parser = subparsers.add_parser("clean", help="Clean directories")
    clean_parser.add_argument(
        "--directory", default="pepperpy", help="Directory to clean"
    )

    # Fix imports legacy command
    fix_imports_parser = subparsers.add_parser(
        "fix-imports", help="Fix imports (legacy method)"
    )
    fix_imports_parser.add_argument(
        "--directory", default="pepperpy", help="Directory to process"
    )

    # Run task command
    task_parser = subparsers.add_parser(
        "run-task", help="Run a specific task from TASK-012"
    )
    task_parser.add_argument("--task", required=True, help="Task ID to run")

    # Update task file command
    update_task_parser = subparsers.add_parser(
        "update-task-file", help="Update the task file with refactor commands"
    )
    update_task_parser.add_argument(
        "--file",
        default=".product/tasks/TASK-012/TASK-012.md",
        help="Path to the task file",
    )

    args = parser.parse_args()

    if args.command == "update-imports":
        import_map = {}
        if args.mapping:
            with open(args.mapping, "r", encoding="utf-8") as f:
                import_map = json.load(f)
        elif args.old and args.new:
            import_map = {args.old: args.new}
        else:
            logger.error("Either --mapping or both --old and --new are required")
            return 1

        update_imports(args.directory, import_map)

    elif args.command == "restructure-files":
        with open(args.mapping, "r", encoding="utf-8") as f:
            file_mapping = json.load(f)

        restructure_files(file_mapping)

    elif args.command == "consolidate":
        files = args.files.split(",")
        consolidate_modules(files, args.output, args.header or "")

    elif args.command == "validate":
        validate_structure(args.directory)

    elif args.command == "find-unused":
        find_unused_code(args.directory)

    elif args.command == "clean":
        clean_directories(args.directory)

    elif args.command == "fix-imports":
        fix_imports_legacy(args.directory)

    elif args.command == "run-task":
        run_task(args.task)

    elif args.command == "update-task-file":
        update_task_file(args.file)

    else:
        parser.print_help()

    return 0


if __name__ == "__main__":
    sys.exit(main())
