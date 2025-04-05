"""Repository analysis workflow plugin.

This plugin provides repository analysis capabilities for PepperPy,
including structure analysis, code quality metrics, and report generation.
"""

import fnmatch
import json
import logging
import os
from dataclasses import dataclass, field
from typing import Any

# Import optional dependencies for code quality metrics
try:
    from radon.complexity import cc_visit
    from radon.raw import analyze

    RADON_AVAILABLE = True
except ImportError:
    RADON_AVAILABLE = False


@dataclass
class PipelineContext:
    """Context for passing data between pipeline stages."""

    metadata: dict[str, Any] = field(default_factory=dict)

    def set_metadata(self, key: str, value: Any) -> None:
        """Set metadata value."""
        self.metadata[key] = value

    def get_metadata(self, key: str, default: Any = None) -> Any:
        """Get metadata value."""
        return self.metadata.get(key, default)


class RepoAnalysisPlugin:
    """Repository analysis plugin.

    This plugin provides repository analysis capabilities:
    - Repository structure analysis
    - Code quality metrics
    - Report generation
    """

    def __init__(self, **config: Any) -> None:
        """Initialize repository analysis plugin.

        Args:
            **config: Plugin configuration
        """
        # Set default configuration
        self.max_files = config.get("max_files", 100)
        self.include_patterns = config.get("include_patterns", ["**/*.py", "**/*.js"])
        self.exclude_patterns = config.get(
            "exclude_patterns",
            ["**/node_modules/**", "**/.git/**", "**/__pycache__/**"],
        )
        self.analysis_depth = config.get("analysis_depth", "standard")
        self.include_metrics = config.get("include_metrics", True)
        self.summary_format = config.get("summary_format", "markdown")

        # Initialize logger
        self.logger = logging.getLogger(__name__)

        # Track initialization state
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize plugin."""
        if self._initialized:
            return

        self.logger.info("Initializing repository analysis plugin")

        # Check for required dependencies
        if self.include_metrics and not RADON_AVAILABLE:
            self.logger.warning(
                "Radon package not available - code quality metrics will be limited"
            )

        self._initialized = True
        self.logger.info("Repository analysis plugin initialized")

    async def cleanup(self) -> None:
        """Clean up resources."""
        self.logger.info("Cleaning up repository analysis plugin resources")
        self._initialized = False

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

        # Create pipeline context
        context = PipelineContext()

        # Override default options with provided options
        max_files = options.get("max_files", self.max_files)
        include_patterns = options.get("include_patterns", self.include_patterns)
        exclude_patterns = options.get("exclude_patterns", self.exclude_patterns)
        analysis_depth = options.get("analysis_depth", self.analysis_depth)
        include_metrics = options.get("include_metrics", self.include_metrics)
        summary_format = options.get("summary_format", self.summary_format)

        try:
            # Step 1: Analyze repository structure
            structure_result = await self._analyze_structure(
                repo_path,
                max_files=max_files,
                include_patterns=include_patterns,
                exclude_patterns=exclude_patterns,
                context=context,
            )

            if not structure_result.get("success", False):
                raise ValueError(
                    f"Repository structure analysis failed: {structure_result.get('message')}"
                )

            # Step 2: Analyze code quality
            if include_metrics:
                quality_result = await self._analyze_quality(
                    repo_path,
                    files=structure_result.get("file_paths", []),
                    analysis_depth=analysis_depth,
                    context=context,
                )

                if not quality_result.get("success", False):
                    raise ValueError(
                        f"Code quality analysis failed: {quality_result.get('message')}"
                    )
            else:
                # Skip quality analysis
                quality_result = {
                    "metrics": {},
                    "success": True,
                    "message": "Code quality analysis skipped",
                }

            # Step 3: Generate reports
            report_result = await self._generate_reports(
                structure=structure_result.get("structure", {}),
                metrics=quality_result.get("metrics", {}),
                summary_format=summary_format,
                context=context,
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
                    "analysis_depth": analysis_depth,
                },
            }

        except Exception as e:
            self.logger.error(f"Repository analysis failed: {e}")
            return {
                "structure": {},
                "metrics": {},
                "summary": "",
                "report": "",
                "success": False,
                "message": f"Repository analysis failed: {e}",
                "metadata": context.metadata,
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

    async def _analyze_structure(
        self,
        repo_path: str,
        max_files: int = 100,
        include_patterns: list[str] | None = None,
        exclude_patterns: list[str] | None = None,
        context: PipelineContext | None = None,
    ) -> dict[str, Any]:
        """Analyze repository structure.

        Args:
            repo_path: Path to the repository
            max_files: Maximum number of files to analyze
            include_patterns: Glob patterns for files to include
            exclude_patterns: Glob patterns for files to exclude
            context: Pipeline context

        Returns:
            Structure analysis results
        """
        if context is None:
            context = PipelineContext()

        include_patterns = include_patterns or self.include_patterns
        exclude_patterns = exclude_patterns or self.exclude_patterns

        try:
            # Validate path
            repo_path = os.path.expanduser(repo_path)
            if not os.path.exists(repo_path):
                raise ValueError(f"Repository path does not exist: {repo_path}")

            # Scan repository for files
            files = self._scan_repository(
                repo_path,
                max_files=max_files,
                include_patterns=include_patterns,
                exclude_patterns=exclude_patterns,
            )

            # Create structure report
            structure = self._build_structure_report(files)

            # Store metadata
            context.set_metadata("repo_path", repo_path)
            context.set_metadata("file_count", len(files))

            return {
                "structure": structure,
                "file_paths": files,
                "file_count": len(files),
                "success": True,
                "message": f"Repository structure analyzed successfully: {len(files)} files",
                "metadata": {"repo_path": repo_path, "max_files": max_files},
            }
        except Exception as e:
            self.logger.error(f"Repository structure analysis failed: {e}")
            context.set_metadata("error", str(e))
            return {
                "structure": {},
                "file_paths": [],
                "file_count": 0,
                "success": False,
                "message": f"Repository structure analysis failed: {e}",
                "metadata": {},
            }

    def _scan_repository(
        self,
        repo_path: str,
        max_files: int = 100,
        include_patterns: list[str] | None = None,
        exclude_patterns: list[str] | None = None,
    ) -> list[str]:
        """Scan repository for files.

        Args:
            repo_path: Path to the repository
            max_files: Maximum number of files to analyze
            include_patterns: Glob patterns for files to include
            exclude_patterns: Glob patterns for files to exclude

        Returns:
            List of file paths
        """
        # Use default patterns if None is provided
        if include_patterns is None:
            include_patterns = self.include_patterns
        if exclude_patterns is None:
            exclude_patterns = self.exclude_patterns

        all_files = []

        for root, _, filenames in os.walk(repo_path):
            for filename in filenames:
                file_path = os.path.join(root, filename)
                rel_path = os.path.relpath(file_path, repo_path)

                # Check include patterns
                included = any(
                    fnmatch.fnmatch(rel_path, pattern) for pattern in include_patterns
                )

                # Check exclude patterns
                excluded = any(
                    fnmatch.fnmatch(rel_path, pattern) for pattern in exclude_patterns
                )

                if included and not excluded:
                    all_files.append(rel_path)

                    # Respect max files limit
                    if len(all_files) >= max_files:
                        break

            if len(all_files) >= max_files:
                break

        return all_files

    def _build_structure_report(self, files: list[str]) -> dict[str, Any]:
        """Build repository structure report.

        Args:
            files: List of file paths

        Returns:
            Structure report
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

    async def _analyze_quality(
        self,
        repo_path: str,
        files: list[str],
        analysis_depth: str = "standard",
        context: PipelineContext | None = None,
    ) -> dict[str, Any]:
        """Analyze code quality.

        Args:
            repo_path: Path to the repository
            files: List of file paths
            analysis_depth: Depth of analysis
            context: Pipeline context

        Returns:
            Quality analysis results
        """
        if context is None:
            context = PipelineContext()

        try:
            if not files:
                raise ValueError("No files provided for analysis")

            # Analyze code quality
            metrics = self._calculate_quality_metrics(repo_path, files, analysis_depth)

            # Store metadata
            context.set_metadata("file_count", len(files))
            context.set_metadata("analysis_depth", analysis_depth)

            return {
                "metrics": metrics,
                "file_count": len(files),
                "success": True,
                "message": f"Code quality analyzed successfully: {len(files)} files",
                "metadata": {
                    "analysis_depth": analysis_depth,
                },
            }
        except Exception as e:
            self.logger.error(f"Code quality analysis failed: {e}")
            context.set_metadata("error", str(e))
            return {
                "metrics": {},
                "file_count": 0,
                "success": False,
                "message": f"Code quality analysis failed: {e}",
                "metadata": {},
            }

    def _calculate_quality_metrics(
        self,
        repo_path: str,
        files: list[str],
        analysis_depth: str = "standard",
    ) -> dict[str, Any]:
        """Calculate code quality metrics.

        Args:
            repo_path: Path to the repository
            files: List of file paths
            analysis_depth: Depth of analysis

        Returns:
            Quality metrics
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

        # If radon is not available, provide basic metrics only
        if not RADON_AVAILABLE:
            for file_path in files:
                if file_path.endswith(".py"):
                    full_path = os.path.join(repo_path, file_path)
                    try:
                        with open(full_path, encoding="utf-8") as f:
                            content = f.readlines()

                        # Basic line counting
                        loc = len(content)
                        comment_lines = sum(
                            1 for line in content if line.strip().startswith("#")
                        )

                        metrics["files"][file_path] = {
                            "loc": loc,
                            "comments": comment_lines,
                        }

                        # Update overall metrics
                        metrics["overall"]["loc"] += loc
                        metrics["overall"]["comments"] += comment_lines
                        metrics["overall"]["num_files"] += 1
                    except Exception:
                        # Skip files that cannot be analyzed
                        pass

            return metrics

        # Use radon for detailed metrics
        total_complexity = 0

        for file_path in files:
            # Only analyze Python files for now
            if not file_path.endswith(".py"):
                continue

            try:
                full_path = os.path.join(repo_path, file_path)
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

    async def _generate_reports(
        self,
        structure: dict[str, Any],
        metrics: dict[str, Any],
        summary_format: str = "markdown",
        context: PipelineContext | None = None,
    ) -> dict[str, Any]:
        """Generate reports.

        Args:
            structure: Repository structure
            metrics: Code quality metrics
            summary_format: Format for summary output
            context: Pipeline context

        Returns:
            Generated reports
        """
        if context is None:
            context = PipelineContext()

        try:
            # Generate summary report
            summary = self._generate_summary(structure, metrics, summary_format)

            # Generate detailed report
            report = self._generate_report(structure, metrics, summary_format)

            # Store metadata
            context.set_metadata("summary_format", summary_format)

            return {
                "summary": summary,
                "report": report,
                "success": True,
                "message": "Reports generated successfully",
                "metadata": {
                    "summary_format": summary_format,
                },
            }
        except Exception as e:
            self.logger.error(f"Report generation failed: {e}")
            context.set_metadata("error", str(e))
            return {
                "summary": "",
                "report": "",
                "success": False,
                "message": f"Report generation failed: {e}",
                "metadata": {},
            }

    def _generate_summary(
        self,
        structure: dict[str, Any],
        metrics: dict[str, Any],
        output_format: str = "markdown",
    ) -> str:
        """Generate summary report.

        Args:
            structure: Repository structure
            metrics: Code quality metrics
            output_format: Output format

        Returns:
            Formatted summary
        """
        file_types = structure.get("file_types", {})
        overall_metrics = metrics.get("overall", {})

        if output_format == "markdown":
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

        elif output_format == "json":
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
        self,
        structure: dict[str, Any],
        metrics: dict[str, Any],
        output_format: str = "markdown",
    ) -> str:
        """Generate detailed report.

        Args:
            structure: Repository structure
            metrics: Code quality metrics
            output_format: Output format

        Returns:
            Formatted report
        """
        # Similar to summary but with more details
        summary = self._generate_summary(structure, metrics, output_format)

        if output_format == "markdown":
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

        elif output_format == "json":
            # Return full data as JSON
            return json.dumps(
                {
                    "summary": json.loads(summary)
                    if output_format == "json"
                    else summary,
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


# Plugin class for framework integration
class RepoAnalysisWorkflow:
    """Workflow for repository analysis.

    This is the main entry point for the plugin framework.
    """

    @classmethod
    def create_plugin(cls, **config: Any) -> RepoAnalysisPlugin:
        """Create plugin instance.

        Args:
            **config: Plugin configuration

        Returns:
            Plugin instance
        """
        return RepoAnalysisPlugin(**config)
