#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Refactoring tool for the PepperPy framework.

This script provides commands to refactor the codebase.

Usage:
    python scripts/refactor.py [command] [options]

Commands:
    import-management:
        update-imports    - Update import statements throughout the codebase
        fix-imports       - Fix relative imports by converting to absolute imports

    file-operations:
        restructure-files - Move files according to the new structure
        consolidate       - Consolidate multiple files into a single module
        clean             - Remove empty directories and dead files

    code-analysis:
        validate          - Validate the project structure
        find-unused       - Find potentially unused code
        detect-circular   - Detect circular dependencies in the codebase
        analyze-impact    - Analyze the impact of refactoring operations

    code-modernization:
        modernize         - Modernize code using current best practices
        improve-types     - Improve type hints in the codebase
        detect-smells     - Detect code smells in the codebase

    ast-transformations:
        extract-method    - Extract a code block into a new method
        to-protocol       - Convert a class to a Protocol interface
        func-to-class     - Convert a function to a class
        extract-api       - Extract public API into __init__.py file
        gen-factory       - Generate a Factory pattern implementation
        analyze-cohesion  - Analyze module cohesion and suggest refactorings

    code-generation:
        gen-module        - Generate a new module from a template
        gen-class         - Generate a new class from a template
        gen-function      - Generate a new function from a template
        gen-provider      - Generate a new LLM provider implementation

    task-execution:
        run-task          - Run a specific task from TASK-012
        update-task-file  - Update the task file with refactor commands
        run-phase         - Run all tasks in a specific phase

    reporting:
        gen-report        - Generate a progress report of refactoring tasks
        gen-checklist     - Generate a checklist of refactoring tasks
        update-task-md    - Update TASK-012.md with execution commands
        gen-consolidation - Generate a report of consolidated directories
        gen-impact-report - Generate a report of the impact of consolidations

    directory-management:
        find-small-dirs   - Find directories with few Python files
        auto-consolidate  - Automatically consolidate small directories

Examples:
    python scripts/refactor.py update-imports --map import_mapping.json --directory pepperpy
    python scripts/refactor.py detect-circular --directory pepperpy
    python scripts/refactor.py extract-method --file path/to/file.py --start 10 --end 20 --name new_method
    python scripts/refactor.py run-task --task "2.1.1"
    python scripts/refactor.py find-small-dirs --directory pepperpy --max-files 2
    python scripts/refactor.py auto-consolidate --directory pepperpy --max-files 2
"""

import argparse
import json
import logging
import os
import sys
from pathlib import Path

# Add the current directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Try importing the required modules, with informative error messages
try:
    import astor
except ImportError:
    logger.warning("astor module not available. Some functionality will be limited.")
    astor = None

try:
    import libcst
except ImportError:
    logger.warning("libcst module not available. Some functionality will be limited.")
    libcst = None

try:
    import ast_decompiler
except ImportError:
    logger.warning(
        "ast_decompiler module not available. Using alternative implementation."
    )
    ast_decompiler = None

# Import refactoring tools
try:
    from scripts.refactoring_tools.common import RefactoringContext
    from scripts.refactoring_tools.dir_consolidation import process_dir_consolidation
    from scripts.refactoring_tools.impact_calculator import calculate_impact
    from scripts.refactoring_tools.module_consolidation import consolidate_modules
    from scripts.refactoring_tools.tasks_executor import (
        run_phase,
        run_task,
        update_task_file,
    )
except ImportError as e:
    print(f"Error importing refactoring tools: {e}")
    print(f"Current sys.path: {sys.path}")
    sys.exit(1)


def find_small_directories(
    directory: str, max_files: int, context: RefactoringContext
) -> list:
    """Find directories with few Python files.

    Args:
        directory: The directory to search in
        max_files: The maximum number of Python files for a directory to be considered small
        context: The refactoring context

    Returns:
        List of small directories
    """
    logger.info(f"Searching for directories with at most {max_files} Python files...")

    root_path = Path(directory)
    small_dirs = []

    # Track all directories with their Python file count
    dir_stats = {}

    # Walk through the directory structure
    for root, dirs, files in os.walk(root_path):
        # Skip hidden directories and __pycache__
        if (
            any(part.startswith(".") for part in Path(root).parts)
            or "__pycache__" in root
        ):
            continue

        path = Path(root)

        # Count Python files in this directory
        py_files = [f for f in files if f.endswith(".py")]
        py_file_count = len(py_files)

        # Skip empty directories or those without Python files
        if py_file_count == 0:
            continue

        # Skip directories that aren't part of a Python package
        # unless they're the root directory itself
        if not (path / "__init__.py").exists() and path != root_path:
            continue

        # Track this directory's stats
        try:
            rel_path = path.relative_to(root_path)
        except ValueError:
            # Handle case where path is not relative to root_path
            continue

        dir_path = str(rel_path) if rel_path != Path(".") else ""

        dir_stats[dir_path] = {
            "path": str(path),
            "rel_path": dir_path,
            "file_count": py_file_count,
            "files": [str(Path(path) / f) for f in py_files],
        }

    # Filter for small directories
    for dir_path, stats in dir_stats.items():
        if 0 < stats["file_count"] <= max_files:
            small_dirs.append(stats)

    # Sort by file count (ascending) and then by path
    small_dirs.sort(key=lambda x: (x["file_count"], x["path"]))

    logger.info(f"Found {len(small_dirs)} small directories")

    if context.verbose and small_dirs:
        for dir_info in small_dirs:
            logger.info(f"  - {dir_info['path']} ({dir_info['file_count']} files)")

    return small_dirs


def auto_consolidate_directories(
    directory: str, max_files: int, context: RefactoringContext
) -> None:
    """Automatically consolidate small directories.

    Args:
        directory: The directory to search in
        max_files: The maximum number of Python files for a directory to be considered small
        context: The refactoring context
    """
    small_dirs = find_small_directories(directory, max_files, context)

    if not small_dirs:
        logger.info("No small directories found")
        return

    logger.info(f"Found {len(small_dirs)} small directories")

    # Check if specific directories should be excluded
    exclude_dirs = getattr(context, "exclude_dirs", [])
    if exclude_dirs:
        logger.info(f"Excluding directories: {', '.join(exclude_dirs)}")

        # Filter out excluded directories
        filtered_dirs = []
        for dir_info in small_dirs:
            excluded = False
            dir_path = dir_info["path"]
            for exclude in exclude_dirs:
                if dir_path.startswith(exclude) or exclude in dir_path:
                    excluded = True
                    logger.info(f"Skipping excluded directory: {dir_path}")
                    break
            if not excluded:
                filtered_dirs.append(dir_info)

        small_dirs = filtered_dirs
        logger.info(f"After exclusions: {len(small_dirs)} directories to consolidate")

    for dir_info in small_dirs:
        dir_path = dir_info["path"]
        py_files = dir_info["files"]
        file_count = dir_info["file_count"]

        # Skip if no Python files
        if not py_files:
            continue

        # Determine output file path
        path = Path(dir_path)
        parent_dir = path.parent
        dir_name = path.name
        output_file = parent_dir / f"{dir_name}.py"

        # Check if output file already exists
        if output_file.exists():
            logger.warning(f"Output file already exists: {output_file}")
            continue

        # Generate header
        header = f"Consolidated module from {dir_path}"

        # Consolidate files
        logger.info(
            f"Consolidating {file_count} files from {dir_path} into {output_file}"
        )

        if not context.dry_run:
            try:
                consolidate_modules(py_files, str(output_file), header, context)

                # Remove original directory if consolidation was successful
                if output_file.exists():
                    logger.info(f"Removing original directory: {dir_path}")
                    # Make sure we're not deleting important stuff
                    if dir_path.startswith(directory) and "__pycache__" not in dir_path:
                        shutil.rmtree(dir_path)
            except Exception as e:
                logger.error(f"Failed to consolidate {dir_path}: {str(e)}")
                if context.verbose:
                    import traceback

                    traceback.print_exc()
        else:
            logger.info(
                f"[DRY RUN] Would consolidate {len(py_files)} files from {dir_path} into {output_file}"
            )


def main() -> int:
    """Main function that parses arguments and dispatches to appropriate handlers."""
    parser = argparse.ArgumentParser(
        description="PepperPy Refactoring CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    # Common arguments
    parser.add_argument("--directory", "-d", type=str, help="Target directory")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without making changes",
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument(
        "--no-backup", action="store_true", help="Do not create backups"
    )

    # Create subparsers for commands
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Import Management Commands
    # -------------------------------------------------------------------------
    # Update imports command
    update_imports_parser = subparsers.add_parser(
        "update-imports", help="Update import statements"
    )
    update_imports_parser.add_argument(
        "--map", type=str, help="JSON file with old->new import mapping"
    )
    update_imports_parser.add_argument("--old", help="Old import path")
    update_imports_parser.add_argument("--new", help="New import path")
    update_imports_parser.add_argument(
        "--use-ast",
        action="store_true",
        help="Use AST-based import updating (more precise)",
    )

    # Fix imports command
    fix_imports_parser = subparsers.add_parser(
        "fix-imports", help="Fix relative imports by converting to absolute"
    )

    # File Operations Commands
    # -------------------------------------------------------------------------
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

    # Clean command
    clean_parser = subparsers.add_parser("clean", help="Clean directories")

    # Code Analysis Commands
    # -------------------------------------------------------------------------
    # Validate command
    validate_parser = subparsers.add_parser("validate", help="Validate structure")

    # Find unused code command
    unused_parser = subparsers.add_parser("find-unused", help="Find unused code")

    # Detect circular dependencies command
    circular_parser = subparsers.add_parser(
        "detect-circular", help="Detect circular dependencies"
    )

    # Analyze impact command
    impact_parser = subparsers.add_parser(
        "analyze-impact", help="Analyze the impact of refactoring operations"
    )
    impact_parser.add_argument(
        "--operation",
        choices=["imports", "files", "task", "phase"],
        required=True,
        help="Type of operation to analyze",
    )
    impact_parser.add_argument("--task", help="Task ID to analyze")
    impact_parser.add_argument("--phase", type=int, help="Phase number to analyze")
    impact_parser.add_argument(
        "--mapping", help="JSON file with mapping (for imports or files)"
    )

    # Detect code smells command
    smells_parser = subparsers.add_parser("detect-smells", help="Detect code smells")
    smells_parser.add_argument("--file", help="Specific file to analyze")

    # Analyze cohesion command
    cohesion_parser = subparsers.add_parser(
        "analyze-cohesion", help="Analyze module cohesion"
    )
    cohesion_parser.add_argument("--file", required=True, help="File to analyze")

    # AST Transformation Commands
    # -------------------------------------------------------------------------
    # Extract method command
    extract_method_parser = subparsers.add_parser(
        "extract-method", help="Extract method"
    )
    extract_method_parser.add_argument("--file", required=True, help="File to process")
    extract_method_parser.add_argument(
        "--start", type=int, required=True, help="Start line (1-indexed)"
    )
    extract_method_parser.add_argument(
        "--end", type=int, required=True, help="End line (1-indexed)"
    )
    extract_method_parser.add_argument("--name", required=True, help="New method name")

    # Convert to protocol command
    protocol_parser = subparsers.add_parser(
        "to-protocol", help="Convert class to Protocol"
    )
    protocol_parser.add_argument("--file", required=True, help="File to process")
    protocol_parser.add_argument(
        "--class", required=True, dest="class_name", help="Class name to convert"
    )

    # Function to class command
    func_to_class_parser = subparsers.add_parser(
        "func-to-class", help="Convert function to class"
    )
    func_to_class_parser.add_argument("--file", required=True, help="File to process")
    func_to_class_parser.add_argument(
        "--function", required=True, help="Function name to convert"
    )

    # Extract public API command
    api_parser = subparsers.add_parser("extract-api", help="Extract public API")
    api_parser.add_argument("--module", required=True, help="Module directory")

    # Generate factory command
    factory_parser = subparsers.add_parser("gen-factory", help="Generate factory")
    factory_parser.add_argument(
        "--class", required=True, dest="class_name", help="Class name"
    )
    factory_parser.add_argument("--output", required=True, help="Output file path")

    # Code Generation Commands
    # -------------------------------------------------------------------------
    # Generate module command
    gen_module_parser = subparsers.add_parser(
        "gen-module", help="Generate a new module"
    )
    gen_module_parser.add_argument("--output", required=True, help="Output file path")
    gen_module_parser.add_argument("--desc", required=True, help="Module description")
    gen_module_parser.add_argument("--imports", help="Comma-separated list of imports")

    # Generate class command
    gen_class_parser = subparsers.add_parser("gen-class", help="Generate a new class")
    gen_class_parser.add_argument("--output", required=True, help="Output file path")
    gen_class_parser.add_argument("--name", required=True, help="Class name")
    gen_class_parser.add_argument("--desc", required=True, help="Class description")
    gen_class_parser.add_argument("--init-args", default="", help="__init__ arguments")
    gen_class_parser.add_argument("--init-body", default="pass", help="__init__ body")
    gen_class_parser.add_argument("--methods", default="", help="Additional methods")

    # Generate function command
    gen_func_parser = subparsers.add_parser(
        "gen-function", help="Generate a new function"
    )
    gen_func_parser.add_argument("--output", required=True, help="Output file path")
    gen_func_parser.add_argument("--name", required=True, help="Function name")
    gen_func_parser.add_argument("--desc", required=True, help="Function description")
    gen_func_parser.add_argument("--args", default="", help="Function arguments")
    gen_func_parser.add_argument("--return-type", default="", help="Return type")
    gen_func_parser.add_argument("--body", default="pass", help="Function body")

    # Generate provider command
    gen_provider_parser = subparsers.add_parser(
        "gen-provider", help="Generate a new LLM provider"
    )
    gen_provider_parser.add_argument("--output", required=True, help="Output file path")
    gen_provider_parser.add_argument("--name", required=True, help="Provider name")
    gen_provider_parser.add_argument(
        "--desc", required=True, help="Provider description"
    )
    gen_provider_parser.add_argument(
        "--init-args", default="", help="__init__ arguments"
    )

    # Task Execution Commands
    # -------------------------------------------------------------------------
    # Run task command
    task_parser = subparsers.add_parser("run-task", help="Run a specific task")
    task_parser.add_argument("--task", required=True, help="Task ID to run")

    # Run phase command
    phase_parser = subparsers.add_parser(
        "run-phase", help="Run all tasks in a specific phase"
    )
    phase_parser.add_argument(
        "--phase", required=True, type=int, help="Phase number to run"
    )
    phase_parser.add_argument("--skip", help="Comma-separated list of task IDs to skip")

    # Update task file command
    update_task_parser = subparsers.add_parser(
        "update-task-file", help="Update task file"
    )
    update_task_parser.add_argument(
        "--file",
        default=".product/tasks/TASK-012/TASK-012.md",
        help="Path to the task file",
    )

    # Reporting Commands
    # -------------------------------------------------------------------------
    # Generate progress report command
    report_parser = subparsers.add_parser(
        "gen-report", help="Generate a progress report"
    )
    report_parser.add_argument(
        "--output",
        default="reports/progress_report.md",
        help="Output file path",
    )

    # Generate task checklist command
    checklist_parser = subparsers.add_parser(
        "gen-checklist", help="Generate a task checklist"
    )
    checklist_parser.add_argument(
        "--output",
        default="reports/task_checklist.md",
        help="Output file path",
    )

    # Update TASK-012.md command
    update_task_md_parser = subparsers.add_parser(
        "update-task-md", help="Update TASK-012.md with execution commands"
    )
    update_task_md_parser.add_argument(
        "--file",
        default=".product/tasks/TASK-012/TASK-012.md",
        help="Path to the task file",
    )

    # Generate consolidation report command
    consolidation_parser = subparsers.add_parser(
        "gen-consolidation", help="Generate a consolidation report from the codebase"
    )
    consolidation_parser.add_argument(
        "--output", required=True, help="Output file path for the report"
    )
    consolidation_parser.set_defaults(func=gen_consolidation_report)

    # Create the consolidate-modules command
    consolidate_modules_parser = subparsers.add_parser(
        "consolidate-modules", help="Consolidate duplicate modules into a single module"
    )
    consolidate_modules_parser.add_argument(
        "--sources", required=True, nargs="+", help="Source module paths to consolidate"
    )
    consolidate_modules_parser.add_argument(
        "--target", required=True, help="Target path for the consolidated module"
    )
    consolidate_modules_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Do not make changes, only show what would happen",
    )
    consolidate_modules_parser.add_argument(
        "--backup",
        action="store_true",
        help="Create backup files before making changes",
    )
    consolidate_modules_parser.set_defaults(func=run_consolidate_modules)

    # Generate impact report command
    impact_report_parser = subparsers.add_parser(
        "gen-impact-report", help="Generate a report on the impact of consolidations"
    )
    impact_report_parser.add_argument(
        "--output",
        default="reports/impact_report.md",
        help="Output file path",
    )

    # Directory Management Commands
    # -------------------------------------------------------------------------
    # Find small directories command
    find_small_dirs_parser = subparsers.add_parser(
        "find-small-dirs", help="Find directories with few Python files"
    )
    find_small_dirs_parser.add_argument(
        "--max-files", type=int, default=2, help="Maximum number of Python files"
    )
    find_small_dirs_parser.add_argument(
        "--output", help="Output file path for the list of small directories"
    )

    # Auto-consolidate command
    auto_consolidate_parser = subparsers.add_parser(
        "auto-consolidate", help="Automatically consolidate small directories"
    )
    auto_consolidate_parser.add_argument(
        "--max-files", type=int, default=2, help="Maximum number of Python files"
    )
    auto_consolidate_parser.add_argument(
        "--exclude",
        help="Comma-separated list of directories to exclude from consolidation",
    )

    # Parse arguments
    args = parser.parse_args()

    # If no arguments are provided, show help
    if len(sys.argv) <= 1:
        parser.print_help()
        return 1

    # Setup the refactoring context
    context = RefactoringContext(
        root_dir=Path(args.directory or "."),
        dry_run=args.dry_run,
        verbose=args.verbose,
        backup=not args.no_backup,
    )

    try:
        # Import Management Commands
        # -------------------------------------------------------------------------
        if args.command == "update-imports":
            import_map = {}

            if args.map:
                with open(args.map, "r", encoding="utf-8") as f:
                    import_map = json.load(f)
            elif args.old and args.new:
                import_map = {args.old: args.new}
            else:
                logger.error("Either --map or both --old and --new are required")
                return 1

            if args.use_ast:
                update_imports_ast(args.directory or ".", import_map, context)
            else:
                update_imports_regex(args.directory or ".", import_map, context)

        elif args.command == "fix-imports":
            fix_relative_imports(args.directory or ".", context)

        # File Operations Commands
        # -------------------------------------------------------------------------
        elif args.command == "restructure-files":
            with open(args.mapping, "r", encoding="utf-8") as f:
                file_mapping = json.load(f)
            restructure_files(file_mapping, context)

        elif args.command == "consolidate":
            files = args.files.split(",")
            consolidate_modules(files, args.output, args.header or "", context)

        elif args.command == "clean":
            clean_directories(args.directory or ".", context)

        # Code Analysis Commands
        # -------------------------------------------------------------------------
        elif args.command == "validate":
            validate_structure(args.directory or ".", context)

        elif args.command == "find-unused":
            unused_code = find_unused_code(args.directory or ".", context)
            if unused_code:
                logger.warning(f"Found {len(unused_code)} potentially unused symbols")
                for name, file_path in unused_code:
                    logger.warning(f"  - {name} in {file_path}")

        elif args.command == "detect-circular":
            cycles = detect_circular_dependencies(args.directory or ".", context)
            if cycles:
                logger.warning(f"Found {len(cycles)} circular dependencies")
                for cycle in cycles:
                    logger.warning(f"  - {' -> '.join(cycle)}")
            else:
                logger.info("No circular dependencies found")

        elif args.command == "analyze-impact":
            if args.operation == "imports":
                if not args.mapping:
                    logger.error("--mapping is required for import impact analysis")
                    return 1

                with open(args.mapping, "r", encoding="utf-8") as f:
                    import_map = json.load(f)

                analyze_import_update_impact(args.directory or ".", import_map, context)

            elif args.operation == "files":
                if not args.mapping:
                    logger.error("--mapping is required for file move impact analysis")
                    return 1

                with open(args.mapping, "r", encoding="utf-8") as f:
                    file_mapping = json.load(f)

                analyze_file_move_impact(file_mapping, context)

            elif args.operation == "task":
                if not args.task:
                    logger.error("--task is required for task impact analysis")
                    return 1

                analyze_task_impact(args.task, context)

            elif args.operation == "phase":
                if not args.phase:
                    logger.error("--phase is required for phase impact analysis")
                    return 1

                analyze_phase_impact(args.phase, context)

        elif args.command == "detect-smells":
            detector = CodeSmellDetector(context)

            if args.file:
                # Analyze single file
                file_path = Path(args.file)
                smells = detector.detect_smells(file_path)
                if smells:
                    logger.warning(f"Found {len(smells)} code smells in {file_path}")
                    for smell in smells:
                        logger.warning(f"  - {smell}")
                else:
                    logger.info(f"No code smells found in {file_path}")
            else:
                # Analyze all files in directory
                python_files = list(Path(args.directory or ".").glob("**/*.py"))
                total_smells = 0
                files_with_smells = 0

                for file_path in python_files:
                    smells = detector.detect_smells(file_path)
                    if smells:
                        files_with_smells += 1
                        total_smells += len(smells)
                        logger.warning(
                            f"Found {len(smells)} code smells in {file_path}"
                        )
                        for smell in smells:
                            logger.warning(f"  - {smell}")

                logger.info(
                    f"Analysis complete: {total_smells} code smells found in {files_with_smells} files (out of {len(python_files)} files)"
                )

        elif args.command == "analyze-cohesion":
            metrics = analyze_cohesion(args.file, context)
            logger.info("Cohesion Metrics:")
            for metric_name, value in metrics.items():
                logger.info(f"  - {metric_name}: {value}")

        # AST Transformation Commands
        # -------------------------------------------------------------------------
        elif args.command == "extract-method":
            extract_method(args.file, args.start, args.end, args.name, context)

        elif args.command == "to-protocol":
            convert_to_protocol(args.file, args.class_name, context)

        elif args.command == "func-to-class":
            function_to_class(args.file, args.function, context)

        elif args.command == "extract-api":
            extract_public_api(args.module, context)

        elif args.command == "gen-factory":
            generate_factory(args.class_name, args.output, context)

        # Code Generation Commands
        # -------------------------------------------------------------------------
        elif args.command == "gen-module":
            imports = args.imports.split(",") if args.imports else None
            generate_module(
                output_path=args.output,
                module_description=args.desc,
                imports=imports,
                context=context,
            )

        elif args.command == "gen-class":
            # Create a class definition
            class_def = {
                "name": args.name,
                "description": args.desc,
                "init_args": args.init_args,
                "init_body": args.init_body,
                "methods": args.methods,
            }

            # Generate module with just this class
            generate_module(
                output_path=args.output,
                module_description=f"Module containing {args.name} class.",
                classes=[class_def],
                context=context,
            )

        elif args.command == "gen-function":
            # Create a function definition
            func_def = {
                "name": args.name,
                "description": args.desc,
                "args": args.args,
                "return_type": args.return_type,
                "body": args.body,
            }

            # Generate module with just this function
            generate_module(
                output_path=args.output,
                module_description=f"Module containing {args.name} function.",
                functions=[func_def],
                context=context,
            )

        elif args.command == "gen-provider":
            generate_provider(
                provider_name=args.name,
                description=args.desc,
                output_path=args.output,
                init_args=args.init_args,
                context=context,
            )

        # Task Execution Commands
        # -------------------------------------------------------------------------
        elif args.command == "run-task":
            run_task(args.task, context)

        elif args.command == "run-phase":
            skip_tasks = args.skip.split(",") if args.skip else []
            run_phase(args.phase, skip_tasks, context)

        elif args.command == "update-task-file":
            update_task_file(args.file, context)

        # Reporting Commands
        # -------------------------------------------------------------------------
        elif args.command == "gen-report":
            generate_progress_report(args.output, context)

        elif args.command == "gen-checklist":
            generate_task_checklist(args.output, context)

        elif args.command == "update-task-md":
            update_task_md(args.file, context)

        # Generate consolidation command
        elif args.command == "gen-consolidation":
            generate_consolidation_report(args.output, context)

        # Generate impact report command
        elif args.command == "gen-impact-report":
            generate_impact_report(args.output, context)

        # Directory Management Commands
        # -------------------------------------------------------------------------
        elif args.command == "find-small-dirs":
            small_dirs = find_small_directories(
                args.directory or ".", args.max_files, context
            )

            if small_dirs:
                logger.info(f"Found {len(small_dirs)} small directories:")
                for dir_info in small_dirs:
                    logger.info(
                        f"  - {dir_info['path']} ({dir_info['file_count']} files)"
                    )

                if args.output:
                    with open(args.output, "w", encoding="utf-8") as f:
                        json.dump(small_dirs, f, indent=2)
                    logger.info(f"Small directories list saved to {args.output}")
            else:
                logger.info("No small directories found")

        elif args.command == "auto-consolidate":
            # Process exclude directories if provided
            if args.exclude:
                context.exclude_dirs = args.exclude.split(",")
                logger.info(f"Excluding directories: {', '.join(context.exclude_dirs)}")

            auto_consolidate_directories(args.directory or ".", args.max_files, context)

        # Consolidate modules command
        elif args.command == "consolidate-modules":
            run_consolidate_modules(args)

        else:
            parser.print_help()
            return 1

    except Exception as e:
        logger.error(f"Error during execution: {e}")
        if context.verbose:
            import traceback

            traceback.print_exc()
        return 1

    return 0


def run_consolidate_modules(args: argparse.Namespace) -> None:
    """
    Run module consolidation based on command line arguments.

    Args:
        args: Command line arguments
    """
    context = RefactoringContext(
        root_dir=args.directory,
        dry_run=args.dry_run,
        backup=args.backup,
        verbose=args.verbose,
    )

    sources = [os.path.join(args.directory, s) for s in args.sources]
    target = os.path.join(args.directory, args.target)

    logger.info(f"Consolidating modules: {sources} -> {target}")

    consolidate_modules(sources, target, context)

    if not context.dry_run:
        logger.info(f"Successfully consolidated modules into {target}")
    else:
        logger.info("[DRY RUN] Would consolidate modules")


if __name__ == "__main__":
    sys.exit(main())
