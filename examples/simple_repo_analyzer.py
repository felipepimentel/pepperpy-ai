#!/usr/bin/env python3
"""
Simple Repository Analyzer Example.

This example demonstrates a standalone simplified workflow that can be used
without relying on the full PepperPy framework.
"""

import asyncio

# Simple logger
import logging
import os
import sys
from functools import wraps
from pathlib import Path
from typing import Any

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("simple_workflow")


def workflow_task(name: str | None = None, description: str | None = None):
    """
    Decorator for marking methods as workflow tasks.
    """

    def decorator(func):
        @wraps(func)
        async def wrapper(self, *args, **kwargs):
            task_name = name or func.__name__

            logger.info(f"Executing task {task_name}")
            try:
                result = await func(self, *args, **kwargs)
                logger.info(f"Task {task_name} completed successfully")
                return result
            except Exception as e:
                logger.error(f"Task {task_name} failed: {e}")
                raise

        # Store metadata as attributes
        wrapper.__workflow_task__ = True
        wrapper.__task_name__ = name or func.__name__
        wrapper.__task_description__ = description or func.__doc__

        return wrapper

    return decorator


class SimpleWorkflow:
    """Simple standalone workflow base class."""

    def __init__(self, name: str, description: str | None = None):
        """Initialize the workflow."""
        self.name = name
        self.description = description or f"Simple workflow: {name}"
        self._tasks = {}
        self.initialized = False

    async def initialize(self) -> None:
        """Initialize the workflow."""
        self.initialized = True

    async def cleanup(self) -> None:
        """Clean up resources."""
        self.initialized = False

    async def execute(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """Execute a task based on input data."""
        if not isinstance(input_data, dict):
            raise ValueError("Input data must be a dictionary")

        # Get task name
        task_name = input_data.get("task")
        if not task_name:
            raise ValueError("Task name must be provided in the input data")

        # Find task function
        task_func = self._tasks.get(task_name)
        if not task_func:
            available_tasks = list(self._tasks.keys())
            raise ValueError(
                f"Task '{task_name}' not found. Available tasks: {available_tasks}"
            )

        # Extract parameters (removing task name)
        params = {k: v for k, v in input_data.items() if k != "task"}

        # Execute task
        logger.info(f"Executing task '{task_name}' with parameters: {params}")
        result = await task_func(**params)

        # Ensure result is a dictionary
        if result is None:
            result = {"status": "success"}
        elif not isinstance(result, dict):
            result = {"result": result, "status": "success"}

        return result

    def get_available_tasks(self) -> list[dict[str, str]]:
        """Get information about available tasks."""
        tasks = []
        for name, func in self._tasks.items():
            description = getattr(func, "__task_description__", "") or ""
            if description and isinstance(description, str):
                description = description.strip()

            tasks.append({"name": name, "description": description})
        return tasks

    async def __aenter__(self):
        """Async context manager enter."""
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.cleanup()


class MinimalRepoAnalyzer(SimpleWorkflow):
    """A minimal repository analyzer workflow."""

    def __init__(self, repo_path=None, **kwargs):
        """Initialize the workflow.

        Args:
            repo_path: Path to the repository to analyze
        """
        super().__init__(
            name="minimal_repo_analyzer",
            description="Analyzes repository structure with minimal code",
        )

        # Set up configuration
        self.repo_path = Path(repo_path or ".").resolve()
        self.initialized = False

        # Discover workflow tasks through inspection
        self._discover_tasks()

    def _discover_tasks(self):
        """Discover workflow tasks by inspecting methods."""
        for name in dir(self):
            if name.startswith("_"):
                continue

            attr = getattr(self, name)
            if (
                callable(attr)
                and asyncio.iscoroutinefunction(attr)
                and hasattr(attr, "__workflow_task__")
            ):
                task_name = getattr(attr, "__task_name__", name)
                self._tasks[task_name] = attr

    async def initialize(self) -> None:
        """Initialize the workflow."""
        if self.initialized:
            return

        # Validate repository path
        if not self.repo_path.exists():
            raise ValueError(f"Repository path does not exist: {self.repo_path}")

        logger.info(f"Initialized repository analyzer for {self.repo_path}")
        self.initialized = True

    @workflow_task()
    async def count_files(self, file_types=None, **kwargs):
        """Count files in the repository by type.

        Args:
            file_types: List of file extensions to count (default: all files)

        Returns:
            File count statistics
        """
        file_types = file_types or [".py", ".js", ".md", ".txt"]

        # Count files by type
        counts = {ext: 0 for ext in file_types}
        total_count = 0

        for root, _, files in os.walk(self.repo_path):
            for file in files:
                total_count += 1
                _, ext = os.path.splitext(file)
                if ext in counts:
                    counts[ext] += 1

        return {
            "total_files": total_count,
            "counts_by_type": counts,
            "repository": str(self.repo_path),
        }

    @workflow_task()
    async def analyze_structure(self, max_depth=3, **kwargs):
        """Analyze the directory structure.

        Args:
            max_depth: Maximum directory depth to analyze

        Returns:
            Directory structure analysis
        """
        # Analyze directory structure
        structure = {}

        def scan_dir(path, current_dict, depth=0):
            if depth > max_depth:
                return

            for item in os.listdir(path):
                if item.startswith("."):  # Skip hidden files
                    continue

                full_path = os.path.join(path, item)
                if os.path.isdir(full_path):
                    current_dict[item] = {}
                    scan_dir(full_path, current_dict[item], depth + 1)
                else:
                    current_dict.setdefault("files", []).append(item)

        scan_dir(self.repo_path, structure)

        return {
            "structure": structure,
            "depth": max_depth,
            "repository": str(self.repo_path),
        }

    @workflow_task(
        name="find_large_files",
        description="Find unusually large files in the repository",
    )
    async def find_large_files(self, min_size_kb=100, **kwargs):
        """Find large files in the repository.

        Args:
            min_size_kb: Minimum file size in KB to report

        Returns:
            List of large files
        """
        min_size = min_size_kb * 1024  # Convert to bytes

        large_files = []

        for root, _, files in os.walk(self.repo_path):
            for file in files:
                file_path = os.path.join(root, file)
                try:
                    size = os.path.getsize(file_path)
                    if size >= min_size:
                        large_files.append({
                            "path": os.path.relpath(file_path, self.repo_path),
                            "size_kb": size / 1024,
                            "size_mb": size / (1024 * 1024),
                        })
                except (OSError, FileNotFoundError):
                    pass

        # Sort by size (largest first)
        large_files.sort(key=lambda x: x["size_kb"], reverse=True)

        return {
            "large_files": large_files,
            "count": len(large_files),
            "min_size_kb": min_size_kb,
        }


async def main():
    """Run the example."""
    # Get repository path from command line or use current directory
    repo_path = sys.argv[1] if len(sys.argv) > 1 else "."

    print(f"Analyzing repository: {repo_path}")

    # Create workflow
    analyzer = MinimalRepoAnalyzer(repo_path=repo_path)

    # Using async context manager (initializes and cleans up automatically)
    async with analyzer:
        # List available tasks
        tasks = analyzer.get_available_tasks()
        print("\nAvailable tasks:")
        for task in tasks:
            print(f"- {task['name']}: {task.get('description', 'No description')}")

        # Execute count_files task
        print("\nCounting files...")
        count_result = await analyzer.execute({"task": "count_files"})
        print(f"Total files: {count_result['total_files']}")
        print("Files by type:")
        for ext, count in count_result["counts_by_type"].items():
            print(f"  {ext}: {count}")

        # Execute analyze_structure task
        print("\nAnalyzing structure...")
        structure_result = await analyzer.execute({
            "task": "analyze_structure",
            "max_depth": 2,
        })
        print(f"Structure analyzed to depth {structure_result['depth']}")

        # Execute find_large_files task
        print("\nFinding large files...")
        large_files_result = await analyzer.execute({
            "task": "find_large_files",
            "min_size_kb": 500,
        })
        print(
            f"Found {large_files_result['count']} files larger than {large_files_result['min_size_kb']} KB"
        )

        # Show large files
        if large_files_result["large_files"]:
            print("\nLargest files:")
            for file in large_files_result["large_files"][:5]:  # Show top 5
                print(f"  {file['path']} - {file['size_mb']:.2f} MB")

    print("\nWorkflow completed!")


if __name__ == "__main__":
    asyncio.run(main())
