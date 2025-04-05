"""Repository analysis workflow plugin."""

import json
import logging
import os
from typing import Any

from radon.complexity import cc_visit
from radon.raw import analyze

from pepperpy.workflow.base import PipelineContext, PipelineStage, WorkflowProvider


class RepoStructureStage(PipelineStage):
    """Stage for analyzing repository structure."""

    def __init__(self, max_files: int = 100, **kwargs: Any) -> None:
        """Initialize repo structure stage.

        Args:
            max_files: Maximum number of files to analyze
            **kwargs: Additional configuration options
        """
        super().__init__(
            name="repo_structure", description="Analyze repository structure"
        )
        self._max_files = max_files
        self._include_patterns = kwargs.get("include_patterns", ["**/*.py", "**/*.js"])
        self._exclude_patterns = kwargs.get(
            "exclude_patterns", ["**/node_modules/**", "**/.git/**"]
        )

    async def process(
        self, input_data: dict[str, Any], context: PipelineContext
    ) -> dict[str, Any]:
        """Analyze repository structure.

        Args:
            input_data: Input data with repository path
            context: Pipeline context

        Returns:
            Repository structure information
        """
        try:
            repo_path = input_data.get("repo_path", "")

            if not repo_path:
                raise ValueError("No repository path provided")

            repo_path = os.path.expanduser(repo_path)

            if not os.path.exists(repo_path):
                raise ValueError(f"Repository path does not exist: {repo_path}")

            # Analyze repository structure
            files = self._scan_repository(repo_path)

            # Create structure report
            structure = self._analyze_structure(files)

            # Store metadata
            context.set_metadata("repo_path", repo_path)
            context.set_metadata("file_count", len(files))

            return {
                "structure": structure,
                "file_paths": files,  # Add file paths explicitly for easy access
                "file_count": len(files),
                "success": True,
                "message": f"Repository structure analyzed successfully: {len(files)} files",
                "metadata": {"repo_path": repo_path, "max_files": self._max_files},
            }
        except Exception as e:
            context.set_metadata("error", str(e))
            return {
                "structure": {},
                "file_paths": [],
                "file_count": 0,
                "success": False,
                "message": f"Repository structure analysis failed: {e}",
                "metadata": {},
            }

    def _scan_repository(self, repo_path: str) -> list[str]:
        """Scan repository for files.

        Simple implementation using os.walk with pattern matching.
        """
        import fnmatch

        all_files = []

        for root, _, filenames in os.walk(repo_path):
            for filename in filenames:
                file_path = os.path.join(root, filename)
                rel_path = os.path.relpath(file_path, repo_path)

                # Check include patterns
                included = any(
                    fnmatch.fnmatch(rel_path, pattern)
                    for pattern in self._include_patterns
                )

                # Check exclude patterns
                excluded = any(
                    fnmatch.fnmatch(rel_path, pattern)
                    for pattern in self._exclude_patterns
                )

                if included and not excluded:
                    all_files.append(rel_path)

                    # Respect max files limit
                    if len(all_files) >= self._max_files:
                        break

            if len(all_files) >= self._max_files:
                break

        return all_files

    def _analyze_structure(self, files: list[str]) -> dict[str, Any]:
        """Analyze repository structure.

        Creates a directory tree and file type statistics.
        """
        # Count file types
        file_types = {}

        for file_path in files:
            ext = os.path.splitext(file_path)[1]
            if ext:
                file_types[ext] = file_types.get(ext, 0) + 1
            else:
                file_types["(no extension)"] = file_types.get("(no extension)", 0) + 1

        # Create directory tree structure (simplified)
        directory_structure = {}

        for file_path in files:
            parts = file_path.split(os.sep)
            current = directory_structure

            # Build tree structure
            for i, part in enumerate(parts):
                if i == len(parts) - 1:  # File
                    if "files" not in current:
                        current["files"] = []
                    current["files"].append(part)
                else:  # Directory
                    if "dirs" not in current:
                        current["dirs"] = {}
                    if part not in current["dirs"]:
                        current["dirs"][part] = {}
                    current = current["dirs"][part]

        return {"file_types": file_types, "directory_structure": directory_structure}


class CodeQualityStage(PipelineStage):
    """Stage for analyzing code quality."""

    def __init__(self, analysis_depth: str = "standard", **kwargs: Any) -> None:
        """Initialize code quality analysis stage.

        Args:
            analysis_depth: Depth of analysis to perform
            **kwargs: Additional configuration options
        """
        super().__init__(name="code_quality", description="Analyze code quality")
        self._analysis_depth = analysis_depth
        self._include_metrics = kwargs.get("include_metrics", True)

    async def process(
        self, input_data: dict[str, Any], context: PipelineContext
    ) -> dict[str, Any]:
        """Analyze code quality.

        Args:
            input_data: Input data with file paths
            context: Pipeline context

        Returns:
            Code quality metrics
        """
        try:
            repo_path = input_data.get("repo_path", "")
            files = input_data.get("file_paths", [])

            if not repo_path:
                raise ValueError("No repository path provided")

            repo_path = os.path.expanduser(repo_path)

            if not files:
                files = input_data.get("structure", {}).get("file_paths", [])

            if not files:
                raise ValueError("No files provided for analysis")

            # Analyze code quality
            quality_metrics = self._analyze_quality(repo_path, files)

            # Store metadata
            context.set_metadata("file_count", len(files))
            context.set_metadata("analysis_depth", self._analysis_depth)

            return {
                "metrics": quality_metrics,
                "file_count": len(files),
                "success": True,
                "message": f"Code quality analyzed successfully: {len(files)} files",
                "metadata": {
                    "analysis_depth": self._analysis_depth,
                    "include_metrics": self._include_metrics,
                },
            }
        except Exception as e:
            context.set_metadata("error", str(e))
            return {
                "metrics": {},
                "file_count": 0,
                "success": False,
                "message": f"Code quality analysis failed: {e}",
                "metadata": {},
            }

    def _analyze_quality(self, repo_path: str, files: list[str]) -> dict[str, Any]:
        """Analyze code quality.

        Uses radon to calculate complexity metrics.
        """
        metrics = {
            "overall": {
                "loc": 0,
                "lloc": 0,
                "sloc": 0,
                "comments": 0,
                "complexity": 0,
                "num_files": 0,
                "avg_complexity": 0,
            },
            "files": {},
        }

        total_complexity = 0

        for file_path in files:
            full_path = os.path.join(repo_path, file_path)

            # Only analyze Python files for now
            if not file_path.endswith(".py"):
                continue

            try:
                with open(full_path, encoding="utf-8") as f:
                    content = f.read()

                # Raw metrics
                raw_metrics = analyze(content)

                # Complexity metrics
                complexity_metrics = cc_visit(content)

                # Calculate average complexity
                file_complexity = sum(item.complexity for item in complexity_metrics)
                total_complexity += file_complexity

                # Store file metrics
                metrics["files"][file_path] = {
                    "loc": raw_metrics.loc,
                    "lloc": raw_metrics.lloc,
                    "sloc": raw_metrics.sloc,
                    "comments": raw_metrics.comments,
                    "complexity": file_complexity,
                    "functions": len(complexity_metrics),
                }

                # Update overall metrics
                metrics["overall"]["loc"] += raw_metrics.loc
                metrics["overall"]["lloc"] += raw_metrics.lloc
                metrics["overall"]["sloc"] += raw_metrics.sloc
                metrics["overall"]["comments"] += raw_metrics.comments
                metrics["overall"]["complexity"] += file_complexity
                metrics["overall"]["num_files"] += 1

            except Exception:
                # Skip files that cannot be analyzed
                continue

        # Calculate average complexity
        if metrics["overall"]["num_files"] > 0:
            metrics["overall"]["avg_complexity"] = (
                metrics["overall"]["complexity"] / metrics["overall"]["num_files"]
            )

        return metrics


class ReportGenerationStage(PipelineStage):
    """Stage for generating repository analysis reports."""

    def __init__(self, summary_format: str = "markdown", **kwargs: Any) -> None:
        """Initialize report generation stage.

        Args:
            summary_format: Format for summary output
            **kwargs: Additional configuration options
        """
        super().__init__(
            name="report_generation", description="Generate repository analysis reports"
        )
        self._summary_format = summary_format

    async def process(
        self, input_data: dict[str, Any], context: PipelineContext
    ) -> dict[str, Any]:
        """Generate repository analysis reports.

        Args:
            input_data: Input data with structure and metrics
            context: Pipeline context

        Returns:
            Generated reports
        """
        try:
            structure = input_data.get("structure", {})
            metrics = input_data.get("metrics", {})

            # Generate summary report
            summary = self._generate_summary(structure, metrics)

            # Generate detailed report
            report = self._generate_report(structure, metrics)

            # Store metadata
            context.set_metadata("summary_format", self._summary_format)

            return {
                "summary": summary,
                "report": report,
                "success": True,
                "message": "Reports generated successfully",
                "metadata": {
                    "summary_format": self._summary_format,
                },
            }
        except Exception as e:
            context.set_metadata("error", str(e))
            return {
                "summary": "",
                "report": "",
                "success": False,
                "message": f"Report generation failed: {e}",
                "metadata": {},
            }

    def _generate_summary(
        self, structure: dict[str, Any], metrics: dict[str, Any]
    ) -> str:
        """Generate summary report.

        Creates a concise summary based on the analysis results.
        """
        file_types = structure.get("file_types", {})
        overall_metrics = metrics.get("overall", {})

        if self._summary_format == "markdown":
            # Generate Markdown summary
            summary = ["# Repository Analysis Summary\n"]

            # File statistics
            summary.append("## File Statistics\n")
            summary.append(
                f"- Total files analyzed: {overall_metrics.get('num_files', 0)}\n"
            )

            if file_types:
                summary.append("- File types:\n")
                for ext, count in sorted(
                    file_types.items(), key=lambda x: x[1], reverse=True
                ):
                    summary.append(f"  - {ext}: {count}\n")

            # Quality metrics
            if overall_metrics:
                summary.append("\n## Code Quality Metrics\n")
                summary.append(f"- Lines of code: {overall_metrics.get('loc', 0)}\n")
                summary.append(
                    f"- Logical lines of code: {overall_metrics.get('lloc', 0)}\n"
                )
                summary.append(
                    f"- Comment lines: {overall_metrics.get('comments', 0)}\n"
                )
                summary.append(
                    f"- Average complexity: {overall_metrics.get('avg_complexity', 0):.2f}\n"
                )

            return "".join(summary)

        elif self._summary_format == "json":
            # Return as JSON string
            summary_data = {
                "file_statistics": {
                    "total_files": overall_metrics.get("num_files", 0),
                    "file_types": file_types,
                },
                "quality_metrics": overall_metrics,
            }
            return json.dumps(summary_data, indent=2)

        else:
            # Plain text format
            summary = ["Repository Analysis Summary\n\n"]

            # File statistics
            summary.append("File Statistics:\n")
            summary.append(
                f"- Total files analyzed: {overall_metrics.get('num_files', 0)}\n"
            )

            if file_types:
                summary.append("- File types:\n")
                for ext, count in sorted(
                    file_types.items(), key=lambda x: x[1], reverse=True
                ):
                    summary.append(f"  {ext}: {count}\n")

            # Quality metrics
            if overall_metrics:
                summary.append("\nCode Quality Metrics:\n")
                summary.append(f"- Lines of code: {overall_metrics.get('loc', 0)}\n")
                summary.append(
                    f"- Logical lines of code: {overall_metrics.get('lloc', 0)}\n"
                )
                summary.append(
                    f"- Comment lines: {overall_metrics.get('comments', 0)}\n"
                )
                summary.append(
                    f"- Average complexity: {overall_metrics.get('avg_complexity', 0):.2f}\n"
                )

            return "".join(summary)

    def _generate_report(
        self, structure: dict[str, Any], metrics: dict[str, Any]
    ) -> str:
        """Generate detailed report.

        Creates a comprehensive report with all analysis details.
        """
        # Similar to summary but with more details
        # For this simple implementation, just add file-level metrics

        summary = self._generate_summary(structure, metrics)

        if self._summary_format == "markdown":
            report = [summary, "\n## Detailed Metrics\n\n"]

            file_metrics = metrics.get("files", {})
            if file_metrics:
                report.append("### File-level Metrics\n\n")
                report.append("| File | Lines | Complexity | Functions |\n")
                report.append("|------|-------|------------|----------|\n")

                for file_path, file_metric in sorted(file_metrics.items()):
                    report.append(
                        f"| {file_path} | {file_metric.get('loc', 0)} | "
                        f"{file_metric.get('complexity', 0)} | "
                        f"{file_metric.get('functions', 0)} |\n"
                    )

            return "".join(report)

        elif self._summary_format == "json":
            # Return full data as JSON
            return json.dumps(
                {
                    "summary": json.loads(summary),
                    "details": {"structure": structure, "metrics": metrics},
                },
                indent=2,
            )

        else:
            # Plain text format - add file details
            report = [summary, "\n\nDetailed Metrics:\n\n"]

            file_metrics = metrics.get("files", {})
            if file_metrics:
                report.append("File-level Metrics:\n\n")

                for file_path, file_metric in sorted(file_metrics.items()):
                    report.append(f"File: {file_path}\n")
                    report.append(f"  Lines: {file_metric.get('loc', 0)}\n")
                    report.append(f"  Complexity: {file_metric.get('complexity', 0)}\n")
                    report.append(f"  Functions: {file_metric.get('functions', 0)}\n\n")

            return "".join(report)


class RepoAnalysisWorkflow(WorkflowProvider):
    """Workflow for repository analysis."""

    def __init__(self, **config: Any) -> None:
        """Initialize workflow provider.

        Args:
            **config: Provider configuration
        """
        super().__init__(**config)

        # Set default configuration
        self.max_files = config.get("max_files", 100)
        self.include_patterns = config.get("include_patterns", ["**/*.py", "**/*.js"])
        self.exclude_patterns = config.get(
            "exclude_patterns", ["**/node_modules/**", "**/.git/**"]
        )
        self.analysis_depth = config.get("analysis_depth", "standard")
        self.include_metrics = config.get("include_metrics", True)
        self.summary_format = config.get("summary_format", "markdown")

        # Initialize pipeline stages
        self._repo_structure: RepoStructureStage | None = None
        self._code_quality: CodeQualityStage | None = None
        self._report_generation: ReportGenerationStage | None = None

        # Initialize logger
        self.logger = logging.getLogger(__name__)

        # Track initialization state
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize workflow components."""
        if self._initialized:
            return

        self.logger.info("Initializing repository analysis workflow")

        # Create pipeline stages
        self._repo_structure = RepoStructureStage(
            max_files=self.max_files,
            include_patterns=self.include_patterns,
            exclude_patterns=self.exclude_patterns,
        )

        self._code_quality = CodeQualityStage(
            analysis_depth=self.analysis_depth, include_metrics=self.include_metrics
        )

        self._report_generation = ReportGenerationStage(
            summary_format=self.summary_format
        )

        self._initialized = True
        self.logger.info("Repository analysis workflow initialized")

    async def cleanup(self) -> None:
        """Clean up resources."""
        self.logger.info("Cleaning up repository analysis workflow resources")
        self._initialized = False

    async def create_workflow(self, workflow_config: dict[str, Any]) -> dict[str, Any]:
        """Create a workflow configuration.

        Args:
            workflow_config: Workflow configuration

        Returns:
            Workflow configuration object
        """
        # Combine default config with provided config
        config = {**self.config, **workflow_config}
        return config

    async def analyze_repo(self, repo_path: str, **options: Any) -> dict[str, Any]:
        """Analyze a repository.

        Args:
            repo_path: Path to the repository
            **options: Additional options

        Returns:
            Analysis results
        """
        if not self._initialized:
            await self.initialize()

        # Create workflow config with options
        workflow = await self.create_workflow(options)

        # Create pipeline context
        context = PipelineContext()

        # Verify that all required stages are initialized
        if (
            not self._repo_structure
            or not self._code_quality
            or not self._report_generation
        ):
            raise RuntimeError("Workflow components not properly initialized")

        # Step 1: Analyze repository structure
        structure_result = await self._repo_structure.process(
            {"repo_path": repo_path}, context
        )

        if not structure_result.get("success", False):
            raise ValueError(
                f"Repository structure analysis failed: {structure_result.get('message')}"
            )

        # Step 2: Analyze code quality
        quality_result = await self._code_quality.process(
            {
                "repo_path": repo_path,
                "file_paths": structure_result.get("file_paths", []),
                "structure": structure_result.get("structure", {}),
            },
            context,
        )

        if not quality_result.get("success", False):
            raise ValueError(
                f"Code quality analysis failed: {quality_result.get('message')}"
            )

        # Step 3: Generate reports
        report_result = await self._report_generation.process(
            {
                "structure": structure_result.get("structure", {}),
                "metrics": quality_result.get("metrics", {}),
            },
            context,
        )

        if not report_result.get("success", False):
            raise ValueError(
                f"Report generation failed: {report_result.get('message')}"
            )

        # Combine results
        return {
            "structure": structure_result.get("structure", {}),
            "metrics": quality_result.get("metrics", {}),
            "summary": report_result.get("summary", ""),
            "report": report_result.get("report", ""),
            "success": True,
            "message": "Repository analysis completed successfully",
            "metadata": {
                "repo_path": repo_path,
                "file_count": structure_result.get("file_count", 0),
                "analysis_depth": self.analysis_depth,
            },
        }

    async def analyze_component(
        self, repo_path: str, component_path: str, **options: Any
    ) -> dict[str, Any]:
        """Analyze a specific component in a repository.

        Args:
            repo_path: Path to the repository
            component_path: Path to the component within the repository
            **options: Additional options

        Returns:
            Component analysis results
        """
        if not self._initialized:
            await self.initialize()

        # Combine paths
        full_component_path = os.path.join(repo_path, component_path)

        # Adjust include patterns to focus on the component
        include_patterns = [os.path.join(component_path, "**/*")]

        # Create custom options for component analysis
        component_options = {**options, "include_patterns": include_patterns}

        # Use analyze_repo with component-specific options
        result = await self.analyze_repo(repo_path, **component_options)

        # Update metadata
        result["metadata"]["component_path"] = component_path
        result["message"] = (
            f"Component analysis completed successfully: {component_path}"
        )

        return result

    async def execute(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """Execute the workflow with the given input.

        Args:
            input_data: Input data with the following structure:
                {
                    "task": str,             # Task type (analyze_repo, analyze_component)
                    "input": Dict[str, Any], # Task-specific input
                    "options": Dict[str, Any] # Task options (optional)
                }

        Returns:
            Dictionary with task results
        """
        if not self._initialized:
            await self.initialize()

        task = input_data.get("task")
        task_input = input_data.get("input", {})
        options = input_data.get("options", {})

        if not task:
            raise ValueError("Input must contain 'task' field")

        if task == "analyze_repo":
            repo_path = task_input.get("repo_path")
            if not repo_path:
                raise ValueError("Repository path is required")
            return await self.analyze_repo(repo_path, **options)

        elif task == "analyze_component":
            repo_path = task_input.get("repo_path")
            component_path = task_input.get("component_path")

            if not repo_path:
                raise ValueError("Repository path is required")

            if not component_path:
                raise ValueError("Component path is required")

            return await self.analyze_component(repo_path, component_path, **options)

        else:
            raise ValueError(f"Unknown task type: {task}")
