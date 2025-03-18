#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Common utilities for refactoring tools.

This module provides shared functionality used across refactoring tools,
including logging configuration and common data structures.
"""

import logging
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import List

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

# Create a logger for the refactoring tools
logger = logging.getLogger("refactor")

# Define the project root
PROJECT_ROOT = Path(os.path.abspath(__file__)).parent.parent.parent

# Constants
DEAD_FILES = ["public.py", "core.py"]
REQUIRED_INIT = ["__init__.py"]

# Code templates for rapid generation
CODE_TEMPLATES = {
    "module_header": """#!/usr/bin/env python
# -*- coding: utf-8 -*-
\"\"\"
{module_description}
\"\"\"

{imports}
""",
    "class": """
class {class_name}:
    \"\"\"
    {class_description}
    \"\"\"
    
    def __init__(self{init_args}):
        {init_body}
    
    {methods}
""",
    "function": """
def {function_name}({args}){return_type}:
    \"\"\"
    {function_description}
    
    {param_docs}
    {return_doc}
    \"\"\"
    {body}
""",
    "factory": """
class {class_name}Factory:
    \"\"\"Factory for creating {class_name} instances.\"\"\"
    
    _registry: Dict[str, Type[{class_name}]] = {}
    
    @classmethod
    def register(cls, name: str, implementation: Type[{class_name}]) -> None:
        \"\"\"Register a new implementation.\"\"\"
        cls._registry[name] = implementation
    
    @classmethod
    def create(cls, factory_type: str, **kwargs: Any) -> {class_name}:
        \"\"\"Create a new instance of the specified type.\"\"\"
        if factory_type not in cls._registry:
            raise ValueError(f"Unknown factory type: {{factory_type}}")
        return cls._registry[factory_type](**kwargs)
    
    @classmethod
    def list_types(cls) -> List[str]:
        \"\"\"List all registered factory types.\"\"\"
        return list(cls._registry.keys())
""",
    "provider": """
class {provider_name}Provider(LLMProvider):
    \"\"\"
    {provider_description}
    \"\"\"
    
    def __init__(self, {init_args}):
        {init_body}
    
    def generate(self, prompt: str, **kwargs: Any) -> str:
        \"\"\"Generate text from a prompt.\"\"\"
        {generate_body}
    
    def generate_stream(self, prompt: str, **kwargs: Any) -> Any:
        \"\"\"Generate text from a prompt as a stream.\"\"\"
        {generate_stream_body}
    
    def embed(self, text: str, **kwargs: Any) -> List[float]:
        \"\"\"Generate embeddings for text.\"\"\"
        {embed_body}
""",
}

# Task registry
TASK_MAP = {}


def register_task(task_id):
    """Decorator to register a function as a task handler."""

    def decorator(func):
        TASK_MAP[task_id] = func
        return func

    return decorator


@dataclass
class RefactoringContext:
    """Context for refactoring operations."""

    root_dir: Path
    dry_run: bool = False
    verbose: bool = False
    backup: bool = True
    exclude_dirs: List[str] = field(default_factory=list)

    def __post_init__(self):
        """Initialize default values after initialization."""
        if self.exclude_dirs is None:
            self.exclude_dirs = []
