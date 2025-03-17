#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Code generation utilities.

This module provides functions for generating code from templates,
making it easier to quickly create new modules, classes, and functions.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional

from .common import CODE_TEMPLATES, RefactoringContext, logger


def generate_module(
    output_path: str,
    module_description: str,
    imports: Optional[List[str]] = None,
    classes: Optional[List[Dict[str, Any]]] = None,
    functions: Optional[List[Dict[str, Any]]] = None,
    context: Optional[RefactoringContext] = None,
) -> None:
    """
    Generate a new Python module with the given components.

    Args:
        output_path: Path where the module will be created
        module_description: Description for the module docstring
        imports: List of import statements
        classes: List of class definitions
        functions: List of function definitions
        context: Refactoring context
    """
    if context is None:
        context = RefactoringContext(Path("."))

    logger.info(f"Generating module at {output_path}")

    # Prepare imports
    import_str = "\n".join(imports or ["from typing import Any, Dict, List, Optional"])

    # Generate header
    content = CODE_TEMPLATES["module_header"].format(
        module_description=module_description, imports=import_str
    )

    # Add classes
    if classes:
        for class_def in classes:
            class_content = generate_class_content(class_def)
            content += class_content

    # Add functions
    if functions:
        for func_def in functions:
            func_content = generate_function_content(func_def)
            content += func_content

    # Write file
    output_file = Path(output_path)
    if context.backup and output_file.exists():
        backup_path = output_file.with_suffix(".py.bak")
        backup_path.write_text(
            output_file.read_text(encoding="utf-8"), encoding="utf-8"
        )
        logger.info(f"Created backup at {backup_path}")

    if not context.dry_run:
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(content, encoding="utf-8")
        logger.info(f"Generated module at {output_path}")
    else:
        logger.info(f"Would generate module at {output_path}")


def generate_class_content(class_def: Dict[str, Any]) -> str:
    """
    Generate a class definition from a template.

    Args:
        class_def: Dictionary with class definition parameters

    Returns:
        String with the class definition
    """
    class_name = class_def.get("name", "NewClass")
    class_desc = class_def.get("description", "A class.")

    # Handle init method
    init_args = class_def.get("init_args", "")
    init_body = class_def.get("init_body", "pass")

    # Handle other methods
    methods = class_def.get("methods", "")

    return CODE_TEMPLATES["class"].format(
        class_name=class_name,
        class_description=class_desc,
        init_args=init_args,
        init_body=init_body,
        methods=methods,
    )


def generate_function_content(func_def: Dict[str, Any]) -> str:
    """
    Generate a function definition from a template.

    Args:
        func_def: Dictionary with function definition parameters

    Returns:
        String with the function definition
    """
    func_name = func_def.get("name", "new_function")
    func_desc = func_def.get("description", "A function.")
    args = func_def.get("args", "")
    return_type = func_def.get("return_type", "")
    if return_type:
        return_type = f" -> {return_type}"

    param_docs = func_def.get("param_docs", "")
    return_doc = func_def.get("return_doc", "")

    body = func_def.get("body", "pass")

    return CODE_TEMPLATES["function"].format(
        function_name=func_name,
        function_description=func_desc,
        args=args,
        return_type=return_type,
        param_docs=param_docs,
        return_doc=return_doc,
        body=body,
    )


def generate_factory(
    class_name: str,
    output_path: str,
    context: Optional[RefactoringContext] = None,
) -> None:
    """
    Generate a factory for a specific class.

    Args:
        class_name: Name of the class to create a factory for
        output_path: Path where the factory will be created
        context: Refactoring context
    """
    if context is None:
        context = RefactoringContext(Path("."))

    logger.info(f"Generating factory for {class_name} at {output_path}")

    # Generate the module content
    module_desc = f"Factory for {class_name} instances."
    imports = [
        "from typing import Any, Dict, List, Optional, Type",
        f"from .{class_name.lower()} import {class_name}",
    ]

    # Generate the factory content
    factory_content = CODE_TEMPLATES["factory"].format(class_name=class_name)

    # Write the file
    output_file = Path(output_path)

    if context.backup and output_file.exists():
        backup_path = output_file.with_suffix(".py.bak")
        backup_path.write_text(
            output_file.read_text(encoding="utf-8"), encoding="utf-8"
        )
        logger.info(f"Created backup at {backup_path}")

    if not context.dry_run:
        output_file.parent.mkdir(parents=True, exist_ok=True)

        content = CODE_TEMPLATES["module_header"].format(
            module_description=module_desc, imports="\n".join(imports)
        )
        content += factory_content

        output_file.write_text(content, encoding="utf-8")
        logger.info(f"Generated factory at {output_path}")
    else:
        logger.info(f"Would generate factory at {output_path}")


def generate_provider(
    provider_name: str,
    description: str,
    output_path: str,
    init_args: str = "",
    init_body: str = "pass",
    generate_body: str = "pass",
    generate_stream_body: str = "pass",
    embed_body: str = "pass",
    context: Optional[RefactoringContext] = None,
) -> None:
    """
    Generate a new LLM provider implementation.

    Args:
        provider_name: Name of the provider
        description: Description of the provider
        output_path: Path where the provider will be created
        init_args: Arguments for the __init__ method
        init_body: Body of the __init__ method
        generate_body: Body of the generate method
        generate_stream_body: Body of the generate_stream method
        embed_body: Body of the embed method
        context: Refactoring context
    """
    if context is None:
        context = RefactoringContext(Path("."))

    logger.info(f"Generating provider {provider_name} at {output_path}")

    # Generate the module content
    module_desc = f"{provider_name} provider implementation for LLM operations."
    imports = [
        "from typing import Any, Dict, List, Optional",
        "from pepperpy.llm.providers.base import LLMProvider",
    ]

    # Generate the provider content
    provider_content = CODE_TEMPLATES["provider"].format(
        provider_name=provider_name,
        provider_description=description,
        init_args=init_args,
        init_body=init_body,
        generate_body=generate_body,
        generate_stream_body=generate_stream_body,
        embed_body=embed_body,
    )

    # Write the file
    output_file = Path(output_path)

    if context.backup and output_file.exists():
        backup_path = output_file.with_suffix(".py.bak")
        backup_path.write_text(
            output_file.read_text(encoding="utf-8"), encoding="utf-8"
        )
        logger.info(f"Created backup at {backup_path}")

    if not context.dry_run:
        output_file.parent.mkdir(parents=True, exist_ok=True)

        content = CODE_TEMPLATES["module_header"].format(
            module_description=module_desc, imports="\n".join(imports)
        )
        content += provider_content

        output_file.write_text(content, encoding="utf-8")
        logger.info(f"Generated provider at {output_path}")
    else:
        logger.info(f"Would generate provider at {output_path}")
