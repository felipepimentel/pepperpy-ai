#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Task execution for PepperPy refactoring.

This module implements specific tasks for the PepperPy refactoring project,
organized by phase and task ID.
"""

from pathlib import Path
from typing import List, Optional

from .common import logger, register_task
from .context import RefactoringContext
from .file_operations import consolidate_modules
from .imports_manager import update_imports_regex

# Phase 1: Core Architecture Tasks


@register_task("1.1.1")
def task_1_1_1(context: RefactoringContext) -> None:
    """
    Task 1.1.1: Consolidate exceptions from various error files into core/errors.py
    """
    logger.info("Executing Task 1.1.1: Consolidate exceptions")

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
    consolidate_modules(files_to_consolidate, output_file, header, context)

    # Update imports to reference the new error location
    error_import_map = {
        "pepperpy.llm.errors": "pepperpy.core.errors",
        "pepperpy.rag.errors": "pepperpy.core.errors",
        # Add other mappings as needed
    }
    update_imports_regex("pepperpy", error_import_map, context)


@register_task("1.2.1")
def task_1_2_1(context: RefactoringContext) -> None:
    """
    Task 1.2.1: Consolidate events functionality into infra/events.py
    """
    logger.info("Executing Task 1.2.1: Consolidate events")

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
    consolidate_modules(files_to_consolidate, output_file, header, context)

    # Update imports to reference the new events location
    events_import_map = {
        "pepperpy.events": "pepperpy.infra.events",
        # Add other mappings as needed
    }
    update_imports_regex("pepperpy", events_import_map, context)


@register_task("1.2.2")
def task_1_2_2(context: RefactoringContext) -> None:
    """
    Task 1.2.2: Consolidate streaming functionality into infra/streaming.py
    """
    logger.info("Executing Task 1.2.2: Consolidate streaming")

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
    consolidate_modules(files_to_consolidate, output_file, header, context)

    # Update imports to reference the new streaming location
    streaming_import_map = {
        "pepperpy.streaming": "pepperpy.infra.streaming",
        # Add other mappings as needed
    }
    update_imports_regex("pepperpy", streaming_import_map, context)


# Phase 2: Domain-Specific Tasks


@register_task("2.1.1")
def task_2_1_1(context: RefactoringContext) -> None:
    """
    Task 2.1.1: Organize embedding functionality in llm/embedding.py
    """
    logger.info("Executing Task 2.1.1: Organize embedding functionality")

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
    consolidate_modules(files_to_consolidate, output_file, header, context)


@register_task("2.1.2")
def task_2_1_2(context: RefactoringContext) -> None:
    """
    Task 2.1.2: Implement LLM providers
    """
    logger.info("Executing Task 2.1.2: Implement LLM providers")

    # Create provider directory structure
    providers_dir = Path("pepperpy/llm/providers")
    if not context.dry_run:
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
    if not context.dry_run:
        init_path = providers_dir / "__init__.py"
        init_path.write_text(init_content, encoding="utf-8")
        logger.info(f"Created {init_path}")
    else:
        logger.info(f"Would create {providers_dir}/__init__.py")

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
    if not context.dry_run:
        base_path = providers_dir / "base.py"
        base_path.write_text(base_content, encoding="utf-8")
        logger.info(f"Created {base_path}")
    else:
        logger.info(f"Would create {providers_dir}/base.py")


@register_task("2.2.1")
def task_2_2_1(context: RefactoringContext) -> None:
    """
    Task 2.2.1: Finalize RAG models and essential functionality
    """
    logger.info("Executing Task 2.2.1: Finalize RAG models")

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
    consolidate_modules(files_to_consolidate, output_file, header, context)


# Helper functions for task execution


def run_task(task_id: str, context: RefactoringContext) -> None:
    """
    Run a specific task by ID.

    Args:
        task_id: Task ID to run
        context: Refactoring context
    """
    from .common import TASK_MAP

    if task_id in TASK_MAP:
        logger.info(f"Running task {task_id}...")
        TASK_MAP[task_id](context)
        logger.info(f"Task {task_id} completed.")
    else:
        available_tasks = ", ".join(sorted(TASK_MAP.keys()))
        logger.error(f"Task {task_id} not found. Available tasks: {available_tasks}")


def run_phase(
    phase: int,
    skip_tasks: Optional[List[str]] = None,
    context: Optional[RefactoringContext] = None,
) -> None:
    """
    Run all tasks for a specific phase.

    Args:
        phase: Phase number (1, 2, 3, or 4)
        skip_tasks: List of task IDs to skip
        context: Refactoring context
    """
    from .common import TASK_MAP

    if context is None:
        context = RefactoringContext(Path("."))

    skip_tasks = skip_tasks or []
    phase_prefix = f"{phase}."

    # Find all tasks for the phase
    phase_tasks = [
        task_id
        for task_id in TASK_MAP.keys()
        if task_id.startswith(phase_prefix) and task_id not in skip_tasks
    ]

    if not phase_tasks:
        logger.error(f"No tasks found for phase {phase}")
        return

    # Sort tasks to ensure proper execution order
    phase_tasks.sort(key=lambda x: [int(p) for p in x.split(".")])

    logger.info(f"Running {len(phase_tasks)} tasks for phase {phase}")

    # Execute each task
    for task_id in phase_tasks:
        try:
            logger.info(f"Running task {task_id} as part of phase {phase}...")
            TASK_MAP[task_id](context)
            logger.info(f"Task {task_id} completed successfully.")
        except Exception as e:
            logger.error(f"Error executing task {task_id}: {e}")
            if context.verbose:
                import traceback

                traceback.print_exc()

    logger.info(f"Phase {phase} execution completed")


def update_task_file(task_file: str, context: RefactoringContext) -> None:
    """
    Update the task file with refactor.py commands for each task.

    Args:
        task_file: Path to the task file
        context: Refactoring context
    """
    import re

    from .common import TASK_MAP

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
    for task_id in TASK_MAP.keys():
        for pattern, replacement in task_patterns:
            updated_content = re.sub(
                pattern,
                replacement.format(task_id),
                updated_content,
                flags=re.MULTILINE,
            )

    # Write updated content if changed
    if content != updated_content:
        if not context.dry_run:
            task_path.write_text(updated_content, encoding="utf-8")
            logger.info(f"Updated {task_file} with refactor.py commands.")
        else:
            logger.info(f"Would update {task_file} with refactor.py commands.")
