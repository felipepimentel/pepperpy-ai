#!/usr/bin/env python3
"""
Command line interface for repository analyzer.

This script provides a direct way to run the repository analyzer workflow
without using the PepperPy CLI system.
"""

import argparse
import asyncio
import json
import sys
from pathlib import Path

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from plugins.workflow.repository_analyzer.simplified_adapter import (
    SimpleRepositoryAnalyzerAdapter,
)


async def run_workflow(task, **kwargs):
    """Run the repository analyzer workflow with specified task and parameters."""
    print(f"Running repository analyzer task: {task}")

    # Create the config dict with correct parameters
    config = {
        "repository_path": kwargs.pop("repository_path", "."),
        "max_files": kwargs.pop("max_files", 1000),
    }

    # Handle include/exclude patterns
    if "include_patterns" in kwargs:
        config["include_patterns"] = kwargs.pop("include_patterns")
    if "exclude_patterns" in kwargs:
        config["exclude_patterns"] = kwargs.pop("exclude_patterns")

    # Create workflow with proper config
    adapter = SimpleRepositoryAnalyzerAdapter(**config)

    # Initialize
    await adapter.initialize()

    try:
        # Prepare task input
        input_data = {"task": task}
        input_data.update(kwargs)

        # Execute the task
        result = await adapter.execute(input_data)

        # Print result
        print(json.dumps(result, indent=2))

        # Return the result for potential further processing
        return result
    finally:
        # Clean up
        await adapter.cleanup()


def main():
    """Parse command line arguments and run the workflow."""
    parser = argparse.ArgumentParser(description="Repository Analyzer Workflow CLI")

    # Add task argument (required)
    parser.add_argument(
        "task", help="Task to execute (analyze_structure, analyze_repository, etc.)"
    )

    # Add common options
    parser.add_argument(
        "--repository-path", default=".", help="Path to repository to analyze"
    )
    parser.add_argument(
        "--max-files", type=int, default=1000, help="Maximum number of files to analyze"
    )
    parser.add_argument(
        "--output-json", help="Output file for JSON result (default: print to stdout)"
    )

    # Task-specific parameters
    parser.add_argument(
        "--min-size-kb",
        type=int,
        default=500,
        help="Minimum file size in KB for large file search",
    )
    parser.add_argument("--limit", type=int, default=50, help="Limit number of results")
    parser.add_argument(
        "--include",
        action="append",
        help="Include file patterns (can be specified multiple times)",
    )
    parser.add_argument(
        "--exclude",
        action="append",
        help="Exclude file patterns (can be specified multiple times)",
    )

    args = parser.parse_args()

    # Build kwargs from args, excluding None values
    kwargs = {
        k: v
        for k, v in vars(args).items()
        if v is not None and k not in ["task", "output_json"]
    }

    # Handle include/exclude patterns
    if args.include:
        kwargs["include_patterns"] = args.include
    if args.exclude:
        kwargs["exclude_patterns"] = args.exclude

    # Run the workflow
    result = asyncio.run(run_workflow(args.task, **kwargs))

    # Save results to file if requested
    if args.output_json:
        with open(args.output_json, "w") as f:
            json.dump(result, f, indent=2)
            print(f"Results written to {args.output_json}")


if __name__ == "__main__":
    main()
