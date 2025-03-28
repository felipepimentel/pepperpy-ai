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

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Add the current directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

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
    from scripts.refactoring_tools.ast_transformations import (
        convert_to_protocol,
        extract_method,
        extract_public_api,
        function_to_class,
        generate_factory,
    )
    from scripts.refactoring_tools.code_analysis import (
        analyze_cohesion,
        detect_circular_dependencies,
        find_unused_code,
        validate_structure,
    )
    from scripts.refactoring_tools.code_generator import (
        generate_module,
        generate_provider,
    )
    from scripts.refactoring_tools.code_quality import CodeSmellDetector
    from scripts.refactoring_tools.common import RefactoringContext
    from scripts.refactoring_tools.file_operations import (
        clean_directories,
        restructure_files,
    )
    from scripts.refactoring_tools.impact_analysis import (
        analyze_file_move_impact,
        analyze_import_update_impact,
        analyze_phase_impact,
        analyze_task_impact,
    )
    from scripts.refactoring_tools.imports_manager import (
        fix_relative_imports,
        update_imports_ast,
        update_imports_regex,
    )
    from scripts.refactoring_tools.module_consolidation import consolidate_modules
    from scripts.refactoring_tools.reporting import (
        generate_consolidation_report,
        generate_impact_report,
        generate_progress_report,
        generate_task_checklist,
        update_task_md,
    )
    from scripts.refactoring_tools.tasks_executor import (
        run_phase,
        run_task,
        update_task_file,
    )
except ImportError as e:
    print(f"Error importing refactoring tools: {e}")
    print(f"Current sys.path: {sys.path}")
    sys.exit(1)

from pepperpy.core.context import RefactoringContext
from pepperpy.core.logging import logger
from pepperpy.refactoring.code_analysis import (
    analyze_cohesion,
    detect_circular_dependencies,
    find_unused_code,
    validate_structure,
)
from pepperpy.refactoring.code_generation import (
    generate_factory,
    generate_module,
    generate_provider,
)
from pepperpy.refactoring.code_smells import CodeSmellDetector
from pepperpy.refactoring.directory_management import (
    auto_consolidate_directories,
    find_small_directories,
)
from pepperpy.refactoring.file_operations import (
    clean_directories,
    consolidate_modules,
    restructure_files,
)
from pepperpy.refactoring.impact_analysis import (
    analyze_file_move_impact,
    analyze_import_update_impact,
    analyze_phase_impact,
    analyze_task_impact,
)
from pepperpy.refactoring.import_management import (
    fix_relative_imports,
    update_imports_ast,
    update_imports_regex,
)
from pepperpy.refactoring.reporting import (
    generate_consolidation_report,
    generate_impact_report,
    generate_progress_report,
    generate_task_checklist,
)
from pepperpy.refactoring.task_management import (
    run_phase,
    run_task,
    update_task_file,
    update_task_md,
)
from pepperpy.refactoring.transformations import (
    convert_to_protocol,
    extract_method,
    extract_public_api,
    function_to_class,
)


def main() -> int:
    """Main entry point for the refactoring tool."""
    parser = argparse.ArgumentParser(description="PepperPy Refactoring Tool")

    # Global options
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show changes without applying them",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging",
    )
    parser.add_argument(
        "--no-backup",
        action="store_true",
        help="Skip creating backup files",
    )

    # Create subparsers for different commands
    subparsers = parser.add_subparsers(
        dest="command",
        help="Available commands",
    )

    # Import Management Commands
    # -------------------------------------------------------------------------
    # Update imports command
    update_imports_parser = subparsers.add_parser(
        "update-imports",
        help="Update import statements",
    )
    update_imports_parser.add_argument(
        "--directory",
        help="Directory to process",
    )
    update_imports_parser.add_argument(
        "--map",
        help="JSON file with old->new import mappings",
    )
    update_imports_parser.add_argument(
        "--old",
        help="Old import to replace",
    )
    update_imports_parser.add_argument(
        "--new",
        help="New import to use",
    )
    update_imports_parser.add_argument(
        "--use-ast",
        action="store_true",
        help="Use AST-based import updating",
    )

    # Fix imports command
    fix_imports_parser = subparsers.add_parser(
        "fix-imports",
        help="Fix relative imports",
    )
    fix_imports_parser.add_argument(
        "--directory",
        help="Directory to process",
    )

    # File Operations Commands
    # -------------------------------------------------------------------------
    # Restructure files command
    restructure_parser = subparsers.add_parser(
        "restructure-files",
        help="Move files to new locations",
    )
    restructure_parser.add_argument(
        "--mapping",
        required=True,
        help="JSON file with old->new path mappings",
    )

    # Consolidate command
    consolidate_parser = subparsers.add_parser(
        "consolidate",
        help="Consolidate multiple files",
    )
    consolidate_parser.add_argument(
        "--files",
        required=True,
        help="Comma-separated list of files",
    )
    consolidate_parser.add_argument(
        "--output",
        required=True,
        help="Output file path",
    )

    # Clean command
    clean_parser = subparsers.add_parser(
        "clean",
        help="Clean up directories",
    )
    clean_parser.add_argument(
        "--directory",
        help="Directory to clean",
    )

    # Code Analysis Commands
    # -------------------------------------------------------------------------
    # Validate command
    validate_parser = subparsers.add_parser(
        "validate",
        help="Validate project structure",
    )
    validate_parser.add_argument(
        "--directory",
        help="Directory to validate",
    )

    # Find unused code command
    unused_parser = subparsers.add_parser(
        "find-unused",
        help="Find unused code",
    )
    unused_parser.add_argument(
        "--directory",
        help="Directory to analyze",
    )

    # Detect circular dependencies command
    circular_parser = subparsers.add_parser(
        "detect-circular",
        help="Find circular dependencies",
    )
    circular_parser.add_argument(
        "--directory",
        help="Directory to analyze",
    )

    # Impact analysis command
    impact_parser = subparsers.add_parser(
        "analyze-impact",
        help="Analyze impact of changes",
    )
    impact_parser.add_argument(
        "--operation",
        choices=["imports", "files", "task", "phase"],
        required=True,
        help="Type of impact analysis",
    )
    impact_parser.add_argument(
        "--directory",
        help="Directory to analyze",
    )
    impact_parser.add_argument(
        "--mapping",
        help="JSON file with mappings",
    )
    impact_parser.add_argument(
        "--task",
        help="Task ID for task impact analysis",
    )
    impact_parser.add_argument(
        "--phase",
        type=int,
        help="Phase number for phase impact analysis",
    )

    # Code smell detection command
    smell_parser = subparsers.add_parser(
        "detect-smells",
        help="Detect code smells",
    )
    smell_parser.add_argument(
        "--file",
        help="Single file to analyze",
    )
    smell_parser.add_argument(
        "--directory",
        help="Directory to analyze",
    )

    # Cohesion analysis command
    cohesion_parser = subparsers.add_parser(
        "analyze-cohesion",
        help="Analyze code cohesion",
    )
    cohesion_parser.add_argument(
        "--file",
        required=True,
        help="File to analyze",
    )

    # AST Transformation Commands
    # -------------------------------------------------------------------------
    # Extract method command
    extract_method_parser = subparsers.add_parser(
        "extract-method",
        help="Extract code into a new method",
    )
    extract_method_parser.add_argument(
        "--file",
        required=True,
        help="File to modify",
    )
    extract_method_parser.add_argument(
        "--start",
        type=int,
        required=True,
        help="Start line number",
    )
    extract_method_parser.add_argument(
        "--end",
        type=int,
        required=True,
        help="End line number",
    )
    extract_method_parser.add_argument(
        "--name",
        required=True,
        help="New method name",
    )

    # Convert to protocol command
    protocol_parser = subparsers.add_parser(
        "to-protocol",
        help="Convert class to protocol",
    )
    protocol_parser.add_argument(
        "--file",
        required=True,
        help="File to modify",
    )
    protocol_parser.add_argument(
        "--class-name",
        required=True,
        help="Class to convert",
    )

    # Function to class command
    func_to_class_parser = subparsers.add_parser(
        "func-to-class",
        help="Convert function to class",
    )
    func_to_class_parser.add_argument(
        "--file",
        required=True,
        help="File to modify",
    )
    func_to_class_parser.add_argument(
        "--function",
        required=True,
        help="Function to convert",
    )

    # Extract API command
    extract_api_parser = subparsers.add_parser(
        "extract-api",
        help="Extract public API",
    )
    extract_api_parser.add_argument(
        "--module",
        required=True,
        help="Module to analyze",
    )

    # Generate factory command
    gen_factory_parser = subparsers.add_parser(
        "gen-factory",
        help="Generate factory class",
    )
    gen_factory_parser.add_argument(
        "--class-name",
        required=True,
        help="Class to create factory for",
    )
    gen_factory_parser.add_argument(
        "--output",
        required=True,
        help="Output file path",
    )

    # Code Generation Commands
    # -------------------------------------------------------------------------
    # Generate module command
    gen_module_parser = subparsers.add_parser(
        "gen-module",
        help="Generate a new module",
    )
    gen_module_parser.add_argument(
        "--output",
        required=True,
        help="Output file path",
    )
    gen_module_parser.add_argument(
        "--desc",
        required=True,
        help="Module description",
    )
    gen_module_parser.add_argument(
        "--imports",
        help="Comma-separated list of imports",
    )

    # Generate class command
    gen_class_parser = subparsers.add_parser(
        "gen-class",
        help="Generate a new class",
    )
    gen_class_parser.add_argument(
        "--output",
        required=True,
        help="Output file path",
    )
    gen_class_parser.add_argument(
        "--name",
        required=True,
        help="Class name",
    )
    gen_class_parser.add_argument(
        "--desc",
        required=True,
        help="Class description",
    )
    gen_class_parser.add_argument(
        "--init-args",
        default="",
        help="__init__ arguments",
    )
    gen_class_parser.add_argument(
        "--init-body",
        default="pass",
        help="__init__ body",
    )
    gen_class_parser.add_argument(
        "--methods",
        default="",
        help="Method definitions",
    )

    # Generate function command
    gen_func_parser = subparsers.add_parser(
        "gen-function",
        help="Generate a new function",
    )
    gen_func_parser.add_argument(
        "--output",
        required=True,
        help="Output file path",
    )
    gen_func_parser.add_argument(
        "--name",
        required=True,
        help="Function name",
    )
    gen_func_parser.add_argument(
        "--desc",
        required=True,
        help="Function description",
    )
    gen_func_parser.add_argument(
        "--args",
        default="",
        help="Function arguments",
    )
    gen_func_parser.add_argument(
        "--return-type",
        default="None",
        help="Return type annotation",
    )
    gen_func_parser.add_argument(
        "--body",
        default="pass",
        help="Function body",
    )

    # Generate provider command
    gen_provider_parser = subparsers.add_parser(
        "gen-provider",
        help="Generate a new provider",
    )
    gen_provider_parser.add_argument(
        "--name",
        required=True,
        help="Provider name",
    )
    gen_provider_parser.add_argument(
        "--desc",
        required=True,
        help="Provider description",
    )
    gen_provider_parser.add_argument(
        "--output",
        required=True,
        help="Output file path",
    )
    gen_provider_parser.add_argument(
        "--init-args",
        default="",
        help="__init__ arguments",
    )

    # Task Execution Commands
    # -------------------------------------------------------------------------
    # Run task command
    run_task_parser = subparsers.add_parser(
        "run-task",
        help="Run a specific task",
    )
    run_task_parser.add_argument(
        "--task",
        required=True,
        help="Task ID to run",
    )

    # Run phase command
    run_phase_parser = subparsers.add_parser(
        "run-phase",
        help="Run all tasks in a phase",
    )
    run_phase_parser.add_argument(
        "--phase",
        type=int,
        required=True,
        help="Phase number to run",
    )
    run_phase_parser.add_argument(
        "--skip",
        help="Comma-separated list of task IDs to skip",
    )

    # Update task file command
    update_task_parser = subparsers.add_parser(
        "update-task-file",
        help="Update task file",
    )
    update_task_parser.add_argument(
        "--file",
        required=True,
        help="Task file to update",
    )

    # Reporting Commands
    # -------------------------------------------------------------------------
    # Generate progress report command
    gen_report_parser = subparsers.add_parser(
        "gen-report",
        help="Generate progress report",
    )
    gen_report_parser.add_argument(
        "--output",
        required=True,
        help="Output file path",
    )

    # Generate task checklist command
    gen_checklist_parser = subparsers.add_parser(
        "gen-checklist",
        help="Generate task checklist",
    )
    gen_checklist_parser.add_argument(
        "--output",
        required=True,
        help="Output file path",
    )

    # Update task markdown command
    update_task_md_parser = subparsers.add_parser(
        "update-task-md",
        help="Update task markdown",
    )
    update_task_md_parser.add_argument(
        "--file",
        required=True,
        help="Markdown file to update",
    )

    # Generate consolidation report command
    gen_consolidation_parser = subparsers.add_parser(
        "gen-consolidation",
        help="Generate consolidation report",
    )
    gen_consolidation_parser.add_argument(
        "--output",
        required=True,
        help="Output file path",
    )

    # Generate impact report command
    gen_impact_parser = subparsers.add_parser(
        "gen-impact-report",
        help="Generate impact report",
    )
    gen_impact_parser.add_argument(
        "--output",
        required=True,
        help="Output file path",
    )

    # Directory Management Commands
    # -------------------------------------------------------------------------
    # Find small directories command
    find_small_dirs_parser = subparsers.add_parser(
        "find-small-dirs",
        help="Find directories with few Python files",
    )
    find_small_dirs_parser.add_argument(
        "--max-files",
        type=int,
        default=2,
        help=("Maximum number of files for a directory to be " "considered small"),
    )

    # Auto consolidate command
    auto_consolidate_parser = subparsers.add_parser(
        "auto-consolidate",
        help="Automatically consolidate small directories",
    )
    auto_consolidate_parser.add_argument(
        "--max-files",
        type=int,
        default=2,
        help=("Maximum number of files for a directory to be " "considered small"),
    )
    auto_consolidate_parser.add_argument(
        "--exclude",
        help="Comma-separated list of directories to exclude",
    )

    args = parser.parse_args()

    # Create refactoring context
    context = RefactoringContext(
        dry_run=args.dry_run,
        verbose=args.verbose,
        no_backup=args.no_backup,
    )

    try:
        # Import Management Commands
        # -------------------------------------------------------------------------
        if args.command == "update-imports":
            if args.map:
                with open(args.map, "r", encoding="utf-8") as f:
                    import_map = json.load(f)
            else:
                import_map = {args.old: args.new}

            if args.use_ast:
                update_imports_ast(
                    args.directory or ".",
                    import_map,
                    context,
                )
            else:
                update_imports_regex(
                    args.directory or ".",
                    import_map,
                    context,
                )

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
            consolidate_modules(files, args.output, context)

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
            cycles = detect_circular_dependencies(
                args.directory or ".",
                context,
            )
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

                analyze_import_update_impact(
                    args.directory or ".",
                    import_map,
                    context,
                )

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
                    f"Analysis complete: {total_smells} code smells found in "
                    f"{files_with_smells} files (out of {len(python_files)} "
                    "files)"
                )

        elif args.command == "analyze-cohesion":
            metrics = analyze_cohesion(args.file, context)
            logger.info("Cohesion Metrics:")
            for metric_name, value in metrics.items():
                logger.info(f"  - {metric_name}: {value}")

        # AST Transformation Commands
        # -------------------------------------------------------------------------
        elif args.command == "extract-method":
            extract_method(
                args.file,
                args.start,
                args.end,
                args.name,
                context,
            )

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

        elif args.command == "gen-consolidation":
            generate_consolidation_report(args.output, context)

        elif args.command == "gen-impact-report":
            generate_impact_report(args.output, context)

        # Directory Management Commands
        # -------------------------------------------------------------------------
        elif args.command == "find-small-dirs":
            small_dirs = find_small_directories(
                args.directory or ".",
                args.max_files,
                context,
            )
            if small_dirs:
                logger.info(
                    f"Found {len(small_dirs)} directories with "
                    f"{args.max_files} or fewer Python files:"
                )
                for dir_info in small_dirs:
                    logger.info(
                        f"  - {dir_info['path']} " f"({dir_info['file_count']} files)"
                    )
            else:
                logger.info("No small directories found")

        elif args.command == "auto-consolidate":
            exclude_dirs = args.exclude.split(",") if args.exclude else []
            context.exclude_dirs = exclude_dirs
            auto_consolidate_directories(
                args.directory or ".",
                args.max_files,
                context,
            )

        else:
            parser.print_help()
            return 1

        return 0

    except Exception as e:
        logger.error(f"Error: {e}")
        if context.verbose:
            import traceback

            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
