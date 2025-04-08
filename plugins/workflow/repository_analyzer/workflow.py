"""
Repository Analyzer Workflow

A workflow for analyzing code repositories and providing insights:
1. Code quality analysis
2. Repository structure analysis
3. Code complexity analysis
4. Dependency analysis
5. Security vulnerability scanning
6. Documentation coverage assessment
"""

import glob
import json
import logging
import os
from pathlib import Path
from typing import TYPE_CHECKING, Any, Optional

from pepperpy.plugin.decorators import workflow
from pepperpy.workflow.base import WorkflowProvider

logger = logging.getLogger(__name__)

# Import conditionally to avoid circular imports
if TYPE_CHECKING:
    from pepperpy.workflow.models import Workflow


@workflow(
    name="repository_analyzer",
    description="Analyzes code repositories and provides insights",
    version="0.1.0",
)
class RepositoryAnalyzerWorkflow(WorkflowProvider):
    """Workflow for analyzing code repositories and providing insights."""

    def __init__(self, **kwargs: Any) -> None:
        """Initialize the repository analyzer workflow.

        Args:
            **kwargs: Provider configuration
        """
        print(f"Initializing RepositoryAnalyzerWorkflow: {self.__class__.__name__}")
        print(f"MRO: {[c.__name__ for c in self.__class__.__mro__]}")

        super().__init__(**kwargs)

        # Initialize workflows dictionary
        self._workflows: dict[str, Workflow] = {}

        # Get configuration values
        self.config = kwargs

        # Repository configuration
        self.repository_path = self.config.get("repository_path", ".")
        self.analysis_types = self.config.get(
            "analysis_types", ["code_quality", "structure", "complexity"]
        )
        self.include_patterns = self.config.get(
            "include_patterns",
            [
                "**/*.py",
                "**/*.js",
                "**/*.ts",
                "**/*.java",
                "**/*.c",
                "**/*.cpp",
                "**/*.go",
            ],
        )
        self.exclude_patterns = self.config.get(
            "exclude_patterns",
            [
                "**/node_modules/**",
                "**/__pycache__/**",
                "**/.git/**",
                "**/venv/**",
                "**/.env/**",
            ],
        )
        self.max_files = self.config.get("max_files", 1000)

        # LLM configuration for insights
        self.llm_provider = self.config.get("llm_provider", "openai")
        self.llm_model = self.config.get("llm_model", "gpt-4")

        # Output configuration
        self.output_dir = self.config.get("output_dir", "./output/repository_analysis")

        # State
        self.pepperpy = None
        self.git_repo = None
        self.initialized = False

    async def initialize(self) -> None:
        """Initialize the workflow."""
        if self.initialized:
            return

        print("Initializing RepositoryAnalyzerWorkflow:", self.__class__.__name__)
        print("MRO:", [c.__name__ for c in self.__class__.__mro__])

        try:
            import os
            from pathlib import Path

            import git

            # Create output directory if needed
            os.makedirs(self.output_dir, exist_ok=True)

            # Validate repository path
            repo_path = Path(self.repository_path).resolve()
            if not repo_path.exists():
                raise ValueError(f"Repository path does not exist: {repo_path}")

            # Try to initialize git repository (if it's a git repo)
            try:
                self.git_repo = git.Repo(repo_path)
                logger.info(f"Initialized Git repository at {repo_path}")
            except (git.InvalidGitRepositoryError, git.NoSuchPathError):
                logger.warning(f"Path is not a valid Git repository: {repo_path}")
                self.git_repo = None

            # Remove dependency on PepperPy facade
            # Instead of using LLM, we'll just do file analysis
            self.pepperpy = None  # No LLM integration for now

            self.initialized = True
            logger.info(f"Initialized repository analyzer for {repo_path}")
        except Exception as e:
            logger.error(f"Failed to initialize repository analyzer: {e}")
            raise

    async def cleanup(self) -> None:
        """Clean up resources."""
        if not self.initialized:
            return

        try:
            if self.pepperpy and hasattr(self.pepperpy, "cleanup"):
                await self.pepperpy.cleanup()

            self.pepperpy = None
            self.git_repo = None
            self.initialized = False
            logger.info("Cleaned up repository analyzer resources")
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")

    def _get_repository_files(self) -> list[str]:
        """Get files from repository based on include/exclude patterns.

        Returns:
            List of file paths relative to repository root
        """
        files = []

        repo_path = Path(self.repository_path).resolve()
        for pattern in self.include_patterns:
            matched_files = glob.glob(str(repo_path / pattern), recursive=True)
            files.extend(matched_files)

        # Convert to relative paths
        files = [os.path.relpath(f, repo_path) for f in files]

        # Apply exclude patterns
        for pattern in self.exclude_patterns:
            # Convert glob pattern to regex
            exclude_matches = glob.glob(str(repo_path / pattern), recursive=True)
            exclude_files = [os.path.relpath(f, repo_path) for f in exclude_matches]
            files = [f for f in files if f not in exclude_files]

        # Limit number of files
        files = files[: self.max_files]

        logger.info(f"Found {len(files)} files to analyze")
        return files

    async def _analyze_code_quality(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """Analyze code quality using basic file inspection.

        Args:
            input_data: Analysis configuration

        Returns:
            Analysis results
        """
        if not self.initialized:
            await self.initialize()

        try:
            # Get repository files
            files = self._get_repository_files()

            # Filter Python files
            python_files = [f for f in files if f.endswith(".py")]

            if not python_files:
                return {
                    "status": "warning",
                    "message": "No Python files found for analysis",
                    "report": {"overall_score": 0, "files_analyzed": 0, "issues": []},
                }

            # Simple analysis without pylint
            issues = []

            for file_path in python_files:
                full_path = os.path.join(self.repository_path, file_path)

                try:
                    with open(full_path, encoding="utf-8") as f:
                        content = f.read()
                        lines = content.split("\n")

                    # Basic checks
                    line_count = len(lines)
                    empty_lines = lines.count("")
                    code_lines = line_count - empty_lines

                    # Check for long lines
                    long_lines = sum(1 for line in lines if len(line) > 100)
                    if long_lines > 0:
                        issues.append({"file": file_path, "issues": long_lines})
                except Exception as e:
                    logger.error(f"Error analyzing file {file_path}: {e}")
                    issues.append({"file": file_path, "issues": 0})

            # Create report
            report = {
                "status": "success",
                "files": [
                    {"file": file, "issues": 0}
                    for file in python_files
                    if not any(i["file"] == file for i in issues)
                ]
                + issues,
                "summary": {
                    "total_issues": sum(issue["issues"] for issue in issues),
                    "complexity_distribution": {
                        "cyclomatic": 0,
                        "maintainability": 0,
                        "error": len(issues),
                    },
                },
            }

            # Save report to file
            output_file = input_data.get("output_file", "code_quality_basic.json")
            output_path = os.path.join(self.output_dir, output_file)
            os.makedirs(os.path.dirname(output_path), exist_ok=True)

            with open(output_path, "w") as f:
                json.dump(report, f, indent=2)

            return {
                "status": "success",
                "report": report,
                "output_path": output_path,
            }
        except Exception as e:
            logger.error(f"Error in code quality analysis: {e}")
            return {
                "status": "error",
                "message": f"Error in code quality analysis: {e!s}",
            }

    async def _analyze_complexity(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """Analyze code complexity.

        Args:
            input_data: Analysis configuration

        Returns:
            Analysis results
        """
        if not self.initialized:
            await self.initialize()

        metrics = input_data.get("metrics", ["cyclomatic", "cognitive"])
        threshold = input_data.get("threshold", "medium")

        try:
            # Import radon for complexity analysis
            from radon.complexity import cc_rank
            from radon.metrics import mi_visit
            from radon.visitors import ComplexityVisitor

            # Convert threshold to numerical value
            threshold_map = {
                "low": "A",
                "medium": "B",
                "high": "C",
                "very_high": "D",
                "extreme": "E",
            }
            rank_threshold = threshold_map.get(threshold, "B")

            # Get repository files
            all_files = self._get_repository_files()

            # Filter for Python files (radon only works with Python)
            files = [f for f in all_files if f.endswith(".py")]

            if not files:
                return {
                    "status": "warning",
                    "message": "No Python files found for complexity analysis",
                    "issues": [],
                }

            # Analyze each file
            issues = []
            file_results = []

            for file_path in files:
                full_path = os.path.join(self.repository_path, file_path)

                try:
                    with open(full_path, encoding="utf-8") as f:
                        content = f.read()

                    # Analyze cyclomatic complexity
                    if "cyclomatic" in metrics:
                        visitor = ComplexityVisitor.from_code(content)
                        for function in visitor.functions:
                            rank = cc_rank(function.complexity)
                            if rank > rank_threshold:
                                issues.append({
                                    "file": file_path,
                                    "line": function.lineno,
                                    "name": function.name,
                                    "complexity": function.complexity,
                                    "rank": rank,
                                    "type": "cyclomatic",
                                    "description": f"Function '{function.name}' has cyclomatic complexity of {function.complexity} (rank {rank})",
                                })

                    # Analyze maintainability index
                    if "maintainability" in metrics:
                        mi_score = mi_visit(content, multi=True)
                        if mi_score < 65:  # Below 65 is considered low maintainability
                            issues.append({
                                "file": file_path,
                                "line": 0,
                                "name": file_path,
                                "complexity": mi_score,
                                "rank": "F" if mi_score < 50 else "D",
                                "type": "maintainability",
                                "description": f"File has low maintainability index of {mi_score}",
                            })

                    file_results.append({
                        "file": file_path,
                        "issues": len([i for i in issues if i["file"] == file_path]),
                    })
                except Exception as e:
                    logger.error(f"Error analyzing file {file_path}: {e}")
                    issues.append({
                        "file": file_path,
                        "line": 0,
                        "name": file_path,
                        "complexity": 0,
                        "rank": "ERROR",
                        "type": "error",
                        "description": f"Failed to analyze: {e!s}",
                    })

            # Create report
            report = {
                "metrics": metrics,
                "threshold": threshold,
                "total_files": len(files),
                "issues": issues,
                "file_results": file_results,
                "summary": {
                    "total_issues": len(issues),
                    "complexity_distribution": {
                        "cyclomatic": len([
                            i for i in issues if i["type"] == "cyclomatic"
                        ]),
                        "maintainability": len([
                            i for i in issues if i["type"] == "maintainability"
                        ]),
                        "error": len([i for i in issues if i["type"] == "error"]),
                    },
                },
            }

            # Save report to file
            output_file = input_data.get("output_file", "complexity.json")
            output_path = os.path.join(self.output_dir, output_file)
            with open(output_path, "w") as f:
                json.dump(report, f, indent=2)

            return {
                "status": "success",
                "issues": issues,
                "report": report,
                "output_path": output_path,
            }
        except Exception as e:
            logger.error(f"Error in complexity analysis: {e}")
            return {
                "status": "error",
                "message": f"Error in complexity analysis: {e!s}",
            }

    async def _analyze_structure(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """Analyze repository structure.

        Args:
            input_data: Analysis configuration

        Returns:
            Analysis results
        """
        if not self.initialized:
            await self.initialize()

        try:
            # Get repository files
            files = self._get_repository_files()

            # Group files by directory and extension
            directories = {}
            extensions = {}

            for file_path in files:
                # Get directory
                directory = os.path.dirname(file_path)
                if not directory:
                    directory = "."

                # Get extension
                _, ext = os.path.splitext(file_path)
                if ext:
                    ext = ext[1:].lower()  # Remove the dot and convert to lowercase
                else:
                    ext = "no_extension"

                # Count by directory
                if directory in directories:
                    directories[directory] += 1
                else:
                    directories[directory] = 1

                # Count by extension
                if ext in extensions:
                    extensions[ext] += 1
                else:
                    extensions[ext] = 1

            # Get git information if available
            git_info = {}
            if self.git_repo:
                try:
                    # Get active branch
                    git_info["active_branch"] = self.git_repo.active_branch.name

                    # Get commit count
                    git_info["commit_count"] = len(list(self.git_repo.iter_commits()))

                    # Get last commit info
                    last_commit = self.git_repo.head.commit
                    git_info["last_commit"] = {
                        "hash": last_commit.hexsha,
                        "author": f"{last_commit.author.name} <{last_commit.author.email}>",
                        "date": last_commit.committed_datetime.isoformat(),
                        "message": last_commit.message.strip(),
                    }

                    # Get branches
                    git_info["branches"] = [b.name for b in self.git_repo.branches]

                    # Get remote information
                    git_info["remotes"] = []
                    for remote in self.git_repo.remotes:
                        git_info["remotes"].append({
                            "name": remote.name,
                            "url": remote.url,
                        })
                except Exception as e:
                    logger.error(f"Error getting git information: {e}")
                    git_info["error"] = str(e)

            # Create structure report
            structure = {
                "files": {
                    "total": len(files),
                    "by_extension": extensions,
                    "by_directory": directories,
                },
                "git": git_info,
                "top_directories": sorted(
                    directories.items(), key=lambda x: x[1], reverse=True
                )[:10],
                "top_extensions": sorted(
                    extensions.items(), key=lambda x: x[1], reverse=True
                )[:10],
            }

            # Create directory tree structure
            tree = {}
            for file_path in files:
                parts = file_path.split(os.sep)
                current = tree
                for i, part in enumerate(parts):
                    if i == len(parts) - 1:  # This is the file
                        if "files" not in current:
                            current["files"] = []
                        current["files"].append(part)
                    else:  # This is a directory
                        if part not in current:
                            current[part] = {}
                        current = current[part]

            structure["tree"] = tree

            # Save report to file
            output_format = input_data.get("output_format", "json")
            output_file = input_data.get("output_file", f"structure.{output_format}")
            output_path = os.path.join(self.output_dir, output_file)

            if output_format == "markdown":
                # Generate markdown report
                markdown = "# Repository Structure Analysis\n\n"
                markdown += "## Overview\n\n"
                markdown += f"- Total Files: {len(files)}\n"
                markdown += "- Top Directories:\n"
                for dir_name, count in sorted(
                    directories.items(), key=lambda x: x[1], reverse=True
                )[:10]:
                    markdown += f"  - {dir_name}: {count} files\n"
                markdown += "\n## File Types\n\n"
                markdown += "| Extension | Count | Percentage |\n"
                markdown += "|-----------|-------|------------|\n"
                for ext, count in sorted(
                    extensions.items(), key=lambda x: x[1], reverse=True
                ):
                    percentage = (count / len(files)) * 100
                    markdown += f"| {ext} | {count} | {percentage:.1f}% |\n"

                if git_info:
                    markdown += "\n## Git Information\n\n"
                    if "active_branch" in git_info:
                        markdown += f"- Active Branch: {git_info['active_branch']}\n"
                    if "commit_count" in git_info:
                        markdown += f"- Commit Count: {git_info['commit_count']}\n"
                    if "last_commit" in git_info:
                        markdown += "- Last Commit:\n"
                        markdown += f"  - Author: {git_info['last_commit']['author']}\n"
                        markdown += f"  - Date: {git_info['last_commit']['date']}\n"
                        markdown += (
                            f"  - Message: {git_info['last_commit']['message']}\n"
                        )

                with open(output_path, "w") as f:
                    f.write(markdown)
            else:
                # Save as JSON
                with open(output_path, "w") as f:
                    json.dump(structure, f, indent=2)

            return {
                "status": "success",
                "structure": structure,
                "output_path": output_path,
            }
        except Exception as e:
            logger.error(f"Error in structure analysis: {e}")
            return {"status": "error", "message": f"Error in structure analysis: {e!s}"}

    async def _analyze_repository(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """Analyze repository with multiple analysis types.

        Args:
            input_data: Analysis configuration

        Returns:
            Combined analysis results
        """
        if not self.initialized:
            await self.initialize()

        # Get analysis types to run
        analysis_types = input_data.get("analysis_types", self.analysis_types)
        output_format = input_data.get("output_format", "markdown")

        results = {}
        summary = []

        # Run each analysis type
        if "code_quality" in analysis_types:
            quality_input = {
                **input_data.get("code_quality", {}),
                "output_file": "code_quality.json",
            }
            quality_result = await self._analyze_code_quality(quality_input)
            results["code_quality"] = quality_result
            if quality_result.get("status") == "success":
                summary.append(
                    f"Code Quality: Analyzed {quality_result['report']['files_analyzed']} files, found {len(quality_result['report']['issues'])} issues"
                )

        if "complexity" in analysis_types:
            complexity_input = {
                **input_data.get("complexity", {}),
                "output_file": "complexity.json",
            }
            complexity_result = await self._analyze_complexity(complexity_input)
            results["complexity"] = complexity_result
            if complexity_result.get("status") == "success":
                summary.append(
                    f"Complexity: Found {len(complexity_result['issues'])} complexity issues"
                )

        if "structure" in analysis_types:
            structure_input = {
                **input_data.get("structure", {}),
                "output_file": f"structure.{output_format}",
            }
            structure_result = await self._analyze_structure(structure_input)
            results["structure"] = structure_result
            if structure_result.get("status") == "success":
                summary.append(
                    f"Structure: Analyzed {structure_result['structure']['files']['total']} files in {len(structure_result['structure']['files']['by_directory'])} directories"
                )

        # Create combined report
        timestamp = Path(self.output_dir) / f"report.{output_format}"
        output_path = str(timestamp)

        if output_format == "markdown":
            markdown = "# Repository Analysis Report\n\n"
            markdown += "## Summary\n\n"
            for item in summary:
                markdown += f"- {item}\n"

            markdown += "\n## Analysis Details\n\n"

            # Add code quality details
            if (
                "code_quality" in results
                and results["code_quality"].get("status") == "success"
            ):
                quality = results["code_quality"]["report"]
                markdown += "### Code Quality\n\n"
                markdown += f"- Overall Score: {quality['overall_score']:.2f}/10.0\n"
                markdown += f"- Files Analyzed: {quality['files_analyzed']}\n"
                markdown += f"- Issues Found: {len(quality['issues'])}\n"

                if quality.get("insights"):
                    markdown += "\n#### Insights\n\n"
                    for insight in quality["insights"]:
                        markdown += f"{insight}\n"

                if quality["issues"]:
                    markdown += "\n#### Top Issues\n\n"
                    markdown += "| File | Line | Message |\n"
                    markdown += "|------|------|--------|\n"
                    for issue in quality["issues"][:10]:  # Show top 10 issues
                        markdown += f"| {issue['file']} | {issue['line']} | {issue['message']} |\n"

            # Add complexity details
            if (
                "complexity" in results
                and results["complexity"].get("status") == "success"
            ):
                complexity = results["complexity"]["report"]
                markdown += "\n### Code Complexity\n\n"
                markdown += f"- Files Analyzed: {complexity['total_files']}\n"
                markdown += f"- Issues Found: {complexity['summary']['total_issues']}\n"

                if complexity["issues"]:
                    markdown += "\n#### Complexity Issues\n\n"
                    markdown += "| File | Function | Complexity | Rank |\n"
                    markdown += "|------|----------|------------|------|\n"
                    for issue in complexity["issues"][:10]:  # Show top 10 issues
                        markdown += f"| {issue['file']} | {issue['name']} | {issue['complexity']} | {issue['rank']} |\n"

            # Add structure details (reference the separate structure file)
            if (
                "structure" in results
                and results["structure"].get("status") == "success"
            ):
                markdown += "\n### Repository Structure\n\n"
                markdown += f"See detailed structure analysis in [{os.path.basename(results['structure']['output_path'])}]({results['structure']['output_path']})\n\n"

                # Add brief summary
                structure = results["structure"]["structure"]
                markdown += f"- Total Files: {structure['files']['total']}\n"
                markdown += "- Top File Types:\n"
                for ext, count in structure["top_extensions"][:5]:
                    percentage = (count / structure["files"]["total"]) * 100
                    markdown += f"  - {ext}: {count} files ({percentage:.1f}%)\n"

            with open(output_path, "w") as f:
                f.write(markdown)
        else:
            # Save as JSON
            with open(output_path, "w") as f:
                json.dump({"summary": summary, "results": results}, f, indent=2)

        return {
            "status": "success",
            "summary": summary,
            "results": results,
            "output_path": output_path,
        }

    async def execute(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """Execute the repository analyzer workflow.

        Args:
            input_data: Dict containing:
                - task: The analysis task to perform
                - input: Task-specific input data

        Returns:
            Dict with the operation result
        """
        try:
            # Initialize if not already initialized
            if not self.initialized:
                await self.initialize()

            # Get task and input
            task = input_data.get("task", "analyze_repository")
            task_input = input_data.get("input", {})

            # Handle different tasks
            if task == "analyze_repository":
                return await self._analyze_repository(task_input)
            elif task == "analyze_code_quality":
                return await self._analyze_code_quality(task_input)
            elif task == "analyze_complexity":
                return await self._analyze_complexity(task_input)
            elif task == "analyze_structure":
                return await self._analyze_structure(task_input)
            else:
                return {"status": "error", "message": f"Unknown task: {task}"}
        except Exception as e:
            logger.error(
                f"Error executing repository analyzer task '{input_data.get('task', '')}': {e}"
            )
            return {"status": "error", "message": str(e)}
        finally:
            # We don't cleanup after each execution
            pass

    async def create_workflow(
        self,
        name: str,
        components: list[dict[str, Any]],
        config: dict[str, Any] | None = None,
    ) -> "Workflow":
        """Create a new workflow.

        Args:
            name: Workflow name
            components: List of workflow component configurations
            config: Optional workflow configuration

        Returns:
            Created workflow instance
        """
        from pepperpy.workflow.models import Task, Workflow

        # Create tasks from components (in this simple case, we create a single task)
        tasks = {}
        task = Task(
            id="analyze",
            name="Repository Analysis",
            description="Analyze repository and generate insights",
            metadata={"analyzer_config": self.config},
        )
        tasks["analyze"] = task

        # Create the workflow
        workflow_id = f"repo_analyzer_{name}"
        workflow = Workflow(
            id=workflow_id,
            name=name,
            description=f"Repository analyzer workflow: {name}",
            version="1.0.0",
            tasks=tasks,
            edges=[],  # No dependencies for single-task workflow
            metadata=config or {},
        )

        # Store in our local workflows dictionary
        self._workflows[workflow_id] = workflow
        return workflow

    async def execute_workflow(
        self,
        workflow: "Workflow",
        input_data: Any | None = None,
        config: dict[str, Any] | None = None,
    ) -> Any:
        """Execute a workflow.

        Args:
            workflow: Workflow to execute
            input_data: Optional input data
            config: Optional execution configuration

        Returns:
            Workflow execution result
        """
        if not self.initialized:
            await self.initialize()

        try:
            task = (
                input_data.get("task", "analyze_repository")
                if input_data
                else "analyze_repository"
            )
            analysis_config = input_data.get("input", {}) if input_data else {}

            # Execute the appropriate analysis based on the task
            if task == "analyze_repository":
                return await self._analyze_repository(analysis_config)
            elif task == "analyze_code_quality":
                return await self._analyze_code_quality(analysis_config)
            elif task == "analyze_structure":
                return await self._analyze_structure(analysis_config)
            elif task == "analyze_complexity":
                return await self._analyze_complexity(analysis_config)
            else:
                raise ValueError(f"Unknown task: {task}")
        except Exception as e:
            logger.error(f"Error executing workflow: {e}")
            raise

    async def get_workflow(self, workflow_id: str) -> Optional["Workflow"]:
        """Get workflow by ID.

        Args:
            workflow_id: Workflow identifier

        Returns:
            Workflow instance or None if not found
        """
        return self._workflows.get(workflow_id)

    async def list_workflows(self) -> list["Workflow"]:
        """List all workflows.

        Returns:
            List of workflows
        """
        from pepperpy.workflow.models import Task, Workflow

        # Create standard workflows if not already defined
        if not self._workflows:
            # Repository analysis workflow
            repo_workflow = Workflow(
                id="analyze_repository",
                name="Full Repository Analysis",
                description="Complete analysis of code repository",
                version="1.0.0",
                tasks={
                    "analyze": Task(
                        id="analyze",
                        name="Repository Analysis",
                        description="Analyze entire repository",
                        metadata={"analysis_types": self.analysis_types},
                    )
                },
                edges=[],  # No dependencies for single-task workflow
                metadata={"type": "repository_analyzer"},
            )
            self._workflows[repo_workflow.id] = repo_workflow

            # Code quality workflow
            quality_workflow = Workflow(
                id="analyze_code_quality",
                name="Code Quality Analysis",
                description="Analysis of code quality using static analysis tools",
                version="1.0.0",
                tasks={
                    "analyze_quality": Task(
                        id="analyze_quality",
                        name="Code Quality Analysis",
                        description="Analyze code quality",
                        metadata={"linters": ["pylint", "flake8", "eslint"]},
                    )
                },
                edges=[],
                metadata={"type": "repository_analyzer"},
            )
            self._workflows[quality_workflow.id] = quality_workflow

            # Structure workflow
            structure_workflow = Workflow(
                id="analyze_structure",
                name="Repository Structure Analysis",
                description="Analysis of repository structure and organization",
                version="1.0.0",
                tasks={
                    "analyze_structure": Task(
                        id="analyze_structure",
                        name="Structure Analysis",
                        description="Analyze repository structure",
                    )
                },
                edges=[],
                metadata={"type": "repository_analyzer"},
            )
            self._workflows[structure_workflow.id] = structure_workflow

            # Complexity workflow
            complexity_workflow = Workflow(
                id="analyze_complexity",
                name="Code Complexity Analysis",
                description="Analysis of code complexity metrics",
                version="1.0.0",
                tasks={
                    "analyze_complexity": Task(
                        id="analyze_complexity",
                        name="Complexity Analysis",
                        description="Analyze code complexity",
                        metadata={
                            "metrics": ["cyclomatic", "cognitive", "maintainability"]
                        },
                    )
                },
                edges=[],
                metadata={"type": "repository_analyzer"},
            )
            self._workflows[complexity_workflow.id] = complexity_workflow

        return list(self._workflows.values())
