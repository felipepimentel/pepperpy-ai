#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Module consolidation utilities.

This module provides functions for consolidating duplicate modules
in the codebase, ensuring all functionality is preserved.
"""

import ast
import os
import re
from typing import Dict, List

from .common import RefactoringContext, logger
from .imports_manager import update_imports_regex


def analyze_module_structure(module_path: str) -> Dict:
    """
    Analyze the structure of a module.

    Args:
        module_path: Path to the module

    Returns:
        Dict containing information about the module structure
    """
    with open(module_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Parse the module
    try:
        tree = ast.parse(content)
    except SyntaxError as e:
        logger.error(f"Error parsing {module_path}: {e}")
        return {
            "path": module_path,
            "classes": [],
            "functions": [],
            "imports": [],
            "docstring": None,
            "error": str(e),
        }

    # Extract module docstring
    docstring = ast.get_docstring(tree)

    # Extract classes
    classes = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            class_info = {
                "name": node.name,
                "lineno": node.lineno,
                "methods": [
                    m.name for m in node.body if isinstance(m, ast.FunctionDef)
                ],
                "docstring": ast.get_docstring(node),
            }
            classes.append(class_info)

    # Extract functions
    functions = []
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and not any(
            isinstance(parent, ast.ClassDef) for parent in ast.iter_fields(tree)
        ):
            function_info = {
                "name": node.name,
                "lineno": node.lineno,
                "args": [arg.arg for arg in node.args.args],
                "docstring": ast.get_docstring(node),
            }
            functions.append(function_info)

    # Extract imports
    imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for name in node.names:
                imports.append({
                    "type": "import",
                    "name": name.name,
                    "asname": name.asname,
                    "lineno": node.lineno,
                })
        elif isinstance(node, ast.ImportFrom):
            for name in node.names:
                imports.append({
                    "type": "from",
                    "module": node.module,
                    "name": name.name,
                    "asname": name.asname,
                    "lineno": node.lineno,
                })

    return {
        "path": module_path,
        "classes": classes,
        "functions": functions,
        "imports": imports,
        "docstring": docstring,
    }


def identify_duplicates(module_structures: List[Dict]) -> Dict:
    """
    Identify duplicated elements between modules.

    Args:
        module_structures: List of module structure dictionaries

    Returns:
        Dict containing information about duplicated elements
    """
    # Track elements by name
    class_by_name = {}
    function_by_name = {}

    # Track duplicates
    duplicate_classes = {}
    duplicate_functions = {}

    # Identify duplicate classes
    for module in module_structures:
        for class_info in module["classes"]:
            name = class_info["name"]
            if name in class_by_name:
                if name not in duplicate_classes:
                    duplicate_classes[name] = [class_by_name[name]]
                duplicate_classes[name].append({
                    "module": module["path"],
                    "info": class_info,
                })
            else:
                class_by_name[name] = {"module": module["path"], "info": class_info}

    # Identify duplicate functions
    for module in module_structures:
        for function_info in module["functions"]:
            name = function_info["name"]
            if name in function_by_name:
                if name not in duplicate_functions:
                    duplicate_functions[name] = [function_by_name[name]]
                duplicate_functions[name].append({
                    "module": module["path"],
                    "info": function_info,
                })
            else:
                function_by_name[name] = {
                    "module": module["path"],
                    "info": function_info,
                }

    return {
        "duplicate_classes": duplicate_classes,
        "duplicate_functions": duplicate_functions,
    }


def merge_modules(
    source_paths: List[str], target_path: str, context: RefactoringContext
) -> None:
    """
    Merge multiple source modules into a target module.

    Args:
        source_paths: Paths to source modules
        target_path: Path where the merged module will be created/updated
        context: Refactoring context
    """
    logger.info(f"Merging modules: {', '.join(source_paths)} -> {target_path}")

    # If the target is one of the sources, make it the first source
    if target_path in source_paths:
        source_paths.remove(target_path)
        source_paths.insert(0, target_path)

    # Analyze module structures
    module_structures = [analyze_module_structure(path) for path in source_paths]

    # Identify duplicates
    duplicates = identify_duplicates(module_structures)

    # Create report for the user
    report = ["Module Consolidation Report:"]
    report.append(f"- Target: {target_path}")
    report.append(f"- Sources: {', '.join(source_paths)}")

    if duplicates["duplicate_classes"]:
        report.append("\nDuplicate Classes:")
        for name, instances in duplicates["duplicate_classes"].items():
            report.append(f"- {name}:")
            for instance in instances:
                report.append(f"  - {instance['module']}")

    if duplicates["duplicate_functions"]:
        report.append("\nDuplicate Functions:")
        for name, instances in duplicates["duplicate_functions"].items():
            report.append(f"- {name}:")
            for instance in instances:
                report.append(f"  - {instance['module']}")

    logger.info("\n".join(report))

    # If this is a dry run, stop here
    if context.dry_run:
        logger.info("[DRY RUN] Would merge modules")
        return

    # Ensure the target directory exists
    os.makedirs(os.path.dirname(target_path), exist_ok=True)

    # If the target doesn't exist, create it from the first source
    if not os.path.exists(target_path) or target_path not in source_paths:
        # Create the target by copying the first source
        with open(source_paths[0], "r", encoding="utf-8") as f:
            target_content = f.read()

        with open(target_path, "w", encoding="utf-8") as f:
            f.write(target_content)

    # Process each additional source module
    target_structure = analyze_module_structure(target_path)

    # Keep track of elements already in the target
    target_classes = {cls["name"] for cls in target_structure["classes"]}
    target_functions = {func["name"] for func in target_structure["functions"]}

    # Process each source module (skipping the target if it's in the sources)
    for path in [p for p in source_paths if p != target_path]:
        source_structure = analyze_module_structure(path)

        # Append new classes and functions to the target
        with open(target_path, "a", encoding="utf-8") as f:
            # Add classes that aren't already in the target
            for cls in source_structure["classes"]:
                if cls["name"] not in target_classes:
                    logger.info(f"Adding class {cls['name']} from {path}")

                    # Extract the class definition from the source file
                    with open(path, "r", encoding="utf-8") as source_file:
                        source_lines = source_file.readlines()

                    # Find the end of the class
                    start_line = cls["lineno"] - 1
                    end_line = start_line
                    indentation = None

                    while end_line < len(source_lines):
                        line = source_lines[end_line]

                        # Determine indentation of the class
                        if indentation is None and line.strip():
                            indentation = len(line) - len(line.lstrip())

                        # Check if we've reached the end of the class
                        if (
                            end_line > start_line
                            and line.strip()
                            and indentation
                            is not None  # Garantir que indentation não é None
                            and (len(line) - len(line.lstrip())) <= indentation
                        ):
                            break

                        end_line += 1

                    # Extract the class definition
                    class_def = "".join(source_lines[start_line:end_line])

                    # Add to target file
                    f.write("\n\n")
                    f.write(class_def)
                    target_classes.add(cls["name"])

            # Add functions that aren't already in the target
            for func in source_structure["functions"]:
                if func["name"] not in target_functions:
                    logger.info(f"Adding function {func['name']} from {path}")

                    # Extract the function definition from the source file
                    with open(path, "r", encoding="utf-8") as source_file:
                        source_lines = source_file.readlines()

                    # Find the end of the function
                    start_line = func["lineno"] - 1
                    end_line = start_line
                    indentation = None

                    while end_line < len(source_lines):
                        line = source_lines[end_line]

                        # Determine indentation of the function
                        if indentation is None and line.strip():
                            indentation = len(line) - len(line.lstrip())

                        # Check if we've reached the end of the function
                        if (
                            end_line > start_line
                            and line.strip()
                            and indentation
                            is not None  # Garantir que indentation não é None
                            and (len(line) - len(line.lstrip())) <= indentation
                        ):
                            break

                        end_line += 1

                    # Extract the function definition
                    func_def = "".join(source_lines[start_line:end_line])

                    # Add to target file
                    f.write("\n\n")
                    f.write(func_def)
                    target_functions.add(func["name"])

    # Update the __all__ list if it exists
    with open(target_path, "r", encoding="utf-8") as f:
        content = f.read()

    all_pattern = r"__all__\s*=\s*\[(.*?)\]"
    all_match = re.search(all_pattern, content, re.DOTALL)

    if all_match:
        all_list = all_match.group(1)
        current_items = re.findall(r'"([^"]+)"|\'([^\']+)\'', all_list)
        current_items = {item[0] or item[1] for item in current_items}

        # Add new classes and functions to __all__
        new_items = target_classes.union(target_functions) - current_items

        if new_items:
            # Format new items to match existing style (single or double quotes)
            quote_style = '"' if '"' in all_list else "'"
            formatted_items = [
                f"{quote_style}{item}{quote_style}" for item in new_items
            ]

            # Add to __all__ list
            new_all_list = all_list.rstrip()
            if new_all_list.rstrip().endswith(","):
                new_all_list += " " + ", ".join(formatted_items)
            else:
                new_all_list += ", " + ", ".join(formatted_items)

            # Replace in content
            new_content = content.replace(all_list, new_all_list)

            with open(target_path, "w", encoding="utf-8") as f:
                f.write(new_content)

    logger.info(f"Successfully merged modules into {target_path}")

    # Update imports in all files to point to the new module
    for path in [p for p in source_paths if p != target_path]:
        # Determine import mappings
        old_import = path.replace("/", ".").replace(".py", "")
        if old_import.startswith("pepperpy."):
            old_import = old_import
        else:
            old_import = "pepperpy." + old_import

        new_import = target_path.replace("/", ".").replace(".py", "")
        if new_import.startswith("pepperpy."):
            new_import = new_import
        else:
            new_import = "pepperpy." + new_import

        # Update imports
        import_map = {old_import: new_import}
        logger.info(f"Updating imports: {old_import} -> {new_import}")
        update_imports_regex("pepperpy", import_map, context)

        # Remove the source file if it's not the target
        if context.backup:
            # Create a backup
            backup_path = path + ".bak"
            with open(path, "r", encoding="utf-8") as src:
                with open(backup_path, "w", encoding="utf-8") as dst:
                    dst.write(src.read())
            logger.info(f"Backed up {path} to {backup_path}")

        os.unlink(path)
        logger.info(f"Removed {path}")


def consolidate_modules(
    source_paths: List[str], target_path: str, context: RefactoringContext
) -> None:
    """
    Consolidate multiple modules into a single module.

    Args:
        source_paths: Paths to source modules
        target_path: Path where the consolidated module will be created
        context: Refactoring context
    """
    try:
        merge_modules(source_paths, target_path, context)
    except Exception as e:
        logger.error(f"Error consolidating modules: {e}")
        if context.verbose:
            import traceback

            traceback.print_exc()
