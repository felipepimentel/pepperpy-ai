"""
Standalone adapter for repository analyzer workflow.

This module demonstrates how to create a simplified workflow adapter
that can be used independently of the full framework.
"""

import asyncio
import os
from pathlib import Path
from typing import Any

# Import the workflow_task decorator and SimpleWorkflow base class
# In a real plugin, these would be imported from the framework
from examples.simple_repo_analyzer import SimpleWorkflow, workflow_task


class StandaloneRepoAnalyzer(SimpleWorkflow):
    """A standalone repository analyzer workflow."""

    def __init__(self, **config):
        """Initialize the workflow.

        Args:
            **config: Configuration options
        """
        super().__init__(
            name="standalone_repo_analyzer",
            description="Analyzes repository structure using minimal standalone implementation",
        )

        # Parse configuration with defaults
        self.config = config or {}
        self.repo_path = Path(self.config.get("repository_path", ".")).resolve()
        self.include_patterns = self.config.get("include_patterns", ["**/*.py"])
        self.exclude_patterns = self.config.get(
            "exclude_patterns",
            ["**/node_modules/**", "**/__pycache__/**", "**/.git/**", "**/.venv/**"],
        )
        self.max_files = self.config.get("max_files", 1000)

        # State variables
        self.git_repo = None
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

        # Try to initialize git repository
        try:
            import git

            try:
                self.git_repo = git.Repo(self.repo_path)
                print(f"Initialized Git repository at {self.repo_path}")
            except (git.InvalidGitRepositoryError, git.NoSuchPathError):
                print(f"Not a Git repository: {self.repo_path}")
                self.git_repo = None
        except ImportError:
            print("GitPython not installed, Git functionality disabled")

        self.initialized = True

    async def cleanup(self) -> None:
        """Clean up resources."""
        if not self.initialized:
            return

        self.git_repo = None
        self.initialized = False
        print("Cleaned up repository analyzer resources")

    @workflow_task()
    async def analyze_structure(self, **kwargs) -> dict[str, Any]:
        """Analyze repository structure.

        Returns:
            Repository structure analysis
        """
        # Get list of files
        files = self._get_repository_files()

        # Analyze directory structure
        structure = self._analyze_structure(files)

        # Get Git repository information if available
        git_info = self._get_git_info() if self.git_repo else None

        return {
            "status": "success",
            "total_files": len(files),
            "structure": structure,
            "git_info": git_info,
        }

    @workflow_task()
    async def count_file_types(
        self, file_types: list[str] | None = None, **kwargs
    ) -> dict[str, Any]:
        """Count files by type.

        Args:
            file_types: Optional list of file extensions to count

        Returns:
            File count statistics
        """
        file_types = file_types or [".py", ".js", ".md", ".txt", ".html", ".css"]

        # Get list of files
        files = self._get_repository_files()

        # Count by extension
        counts = {ext: 0 for ext in file_types}
        other_count = 0

        for file_path in files:
            _, ext = os.path.splitext(file_path)
            if ext in counts:
                counts[ext] += 1
            else:
                other_count += 1

        return {
            "status": "success",
            "total_files": len(files),
            "counts_by_type": counts,
            "other_files": other_count,
        }

    @workflow_task(
        name="find_large_files",
        description="Find unusually large files in the repository",
    )
    async def find_large_files(
        self, min_size_kb: int = 500, limit: int = 20, **kwargs
    ) -> dict[str, Any]:
        """Find large files in the repository.

        Args:
            min_size_kb: Minimum file size in KB to report
            limit: Maximum number of files to return

        Returns:
            List of large files
        """
        min_size = min_size_kb * 1024  # Convert to bytes

        # Get list of files
        all_files = self._get_repository_files()

        # Find large files
        large_files = []
        for file_path in all_files:
            full_path = os.path.join(self.repo_path, file_path)
            try:
                size = os.path.getsize(full_path)
                if size >= min_size:
                    large_files.append({
                        "path": file_path,
                        "size_kb": size / 1024,
                        "size_mb": size / (1024 * 1024),
                    })
            except (OSError, FileNotFoundError):
                pass

        # Sort by size (largest first)
        large_files.sort(key=lambda x: x["size_kb"], reverse=True)

        # Limit number of results
        large_files = large_files[:limit]

        return {
            "status": "success",
            "large_files": large_files,
            "count": len(large_files),
            "min_size_kb": min_size_kb,
        }

    def _get_repository_files(self) -> list[str]:
        """Get files from repository based on include/exclude patterns.

        Returns:
            List of file paths relative to repository root
        """
        import glob

        files = []

        # Apply include patterns
        for pattern in self.include_patterns:
            matched_files = glob.glob(str(self.repo_path / pattern), recursive=True)
            files.extend(matched_files)

        # Convert to relative paths
        files = [os.path.relpath(f, self.repo_path) for f in files]

        # Apply exclude patterns
        for pattern in self.exclude_patterns:
            exclude_matches = glob.glob(str(self.repo_path / pattern), recursive=True)
            exclude_files = [
                os.path.relpath(f, self.repo_path) for f in exclude_matches
            ]
            files = [f for f in files if f not in exclude_files]

        # Limit number of files
        files = files[: self.max_files]

        return files

    def _analyze_structure(self, files: list[str]) -> dict[str, Any]:
        """Analyze repository structure.

        Args:
            files: List of files

        Returns:
            Structure analysis
        """
        import os

        # Count files by directory
        dirs = {}
        for file_path in files:
            directory = os.path.dirname(file_path) or "."
            dirs[directory] = dirs.get(directory, 0) + 1

        # Count files by extension
        extensions = {}
        for file_path in files:
            _, ext = os.path.splitext(file_path)
            if ext:
                extensions[ext] = extensions.get(ext, 0) + 1

        # Get top directories and extensions
        top_dirs = sorted(dirs.items(), key=lambda x: x[1], reverse=True)[:10]
        top_exts = sorted(extensions.items(), key=lambda x: x[1], reverse=True)

        # Build directory tree
        tree = {}
        for file_path in files:
            parts = file_path.split(os.sep)
            current = tree
            for i, part in enumerate(parts):
                if i == len(parts) - 1:  # File
                    current.setdefault("files", []).append(part)
                else:  # Directory
                    current = current.setdefault("dirs", {}).setdefault(part, {})

        return {
            "directories": dirs,
            "top_directories": top_dirs,
            "extensions": extensions,
            "top_extensions": top_exts,
            "tree": tree,
        }

    def _get_git_info(self) -> dict[str, Any]:
        """Get Git repository information.

        Returns:
            Git repository information
        """
        if not self.git_repo:
            return {}

        try:
            # Get basic info
            try:
                active_branch = self.git_repo.active_branch.name
            except Exception:
                active_branch = "DETACHED_HEAD"

            # Get commit count
            commit_count = len(list(self.git_repo.iter_commits()))

            # Get last commit
            last_commit = self.git_repo.head.commit
            last_commit_info = {
                "hash": last_commit.hexsha,
                "author": f"{last_commit.author.name} <{last_commit.author.email}>",
                "date": last_commit.committed_datetime.isoformat(),
                "message": last_commit.message.strip(),
            }

            return {
                "active_branch": active_branch,
                "commit_count": commit_count,
                "last_commit": last_commit_info,
            }
        except Exception as e:
            return {"error": str(e)}


class StandaloneAdapter:
    """Adapter for standalone repository analyzer workflow."""

    def __init__(self, **config):
        """Initialize the adapter.

        Args:
            **config: Configuration options
        """
        self.config = config
        self.workflow = None
        self.initialized = False

    async def initialize(self) -> None:
        """Initialize the workflow."""
        if self.initialized:
            return

        # Create workflow instance
        self.workflow = StandaloneRepoAnalyzer(**self.config)

        # Initialize workflow
        await self.workflow.initialize()
        self.initialized = True

    async def cleanup(self) -> None:
        """Clean up resources."""
        if not self.initialized:
            return

        if self.workflow:
            await self.workflow.cleanup()
            self.workflow = None

        self.initialized = False

    async def execute(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """Execute a workflow task.

        Args:
            input_data: Input data containing task and parameters

        Returns:
            Task execution result
        """
        if not self.initialized:
            await self.initialize()

        if not self.workflow:
            raise RuntimeError("Workflow was not properly initialized")

        # Add topic to satisfy validation, if not present
        if "topic" not in input_data:
            input_data["topic"] = "repository analysis"

        return await self.workflow.execute(input_data)

    # Plugin compatibility methods
    async def create_workflow(self, *args, **kwargs) -> None:
        """Method for plugin system compatibility."""
        return None

    async def execute_workflow(self, *args, **kwargs) -> None:
        """Method for plugin system compatibility."""
        return None


# For easy import in plugin system
__all__ = ["StandaloneAdapter"]


# Simple test code
async def test_standalone():
    """Test the standalone adapter."""
    print("Testing standalone repository analyzer...")

    adapter = StandaloneAdapter(repository_path=".")
    await adapter.initialize()

    tasks = adapter.workflow.get_available_tasks()
    print(f"Available tasks: {[t['name'] for t in tasks]}")

    print("\nAnalyzing structure...")
    result = await adapter.execute({"task": "analyze_structure"})
    print(f"Found {result['total_files']} files")
    print(f"Top file types: {result['structure']['top_extensions'][:3]}")

    print("\nFinding large files...")
    result = await adapter.execute({
        "task": "find_large_files",
        "min_size_kb": 1000,
        "limit": 3,
    })
    print(f"Found {result['count']} large files")
    for file in result.get("large_files", []):
        print(f"  {file['path']} - {file['size_mb']:.2f} MB")

    await adapter.cleanup()
    print("\nTest completed")


if __name__ == "__main__":
    asyncio.run(test_standalone())
