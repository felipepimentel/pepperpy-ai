"""Repository analyzer workflow provider."""

import os
import pathlib
from typing import Any

from pepperpy.plugin.provider import BasePluginProvider
from pepperpy.utils.file import get_file_stats
from pepperpy.workflow.base import WorkflowError, WorkflowProvider


class RepositoryAnalyzerProvider(WorkflowProvider, BasePluginProvider):
    """Analyzes code repositories and provides insights."""

    async def initialize(self) -> None:
        """Initialize the provider.

        This method is called automatically when the provider is first used.
        """
        # Call the base class implementation first
        await super().initialize()

        # Repository configuration
        self.repository_path = self.config.get("repository_path", ".")
        self.analysis_types = self.config.get(
            "analysis_types", ["code_quality", "structure"]
        )
        self.include_patterns = self.config.get(
            "include_patterns", ["**/*.py", "**/*.js"]
        )
        self.exclude_patterns = self.config.get(
            "exclude_patterns", ["**/node_modules/**"]
        )
        self.max_files = self.config.get("max_files", 1000)

        # Output configuration
        self.output_dir = self.config.get("output_dir", "./output/analysis")

        try:
            # Initialize repository access
            self.repo = await self._setup_repository()

            # Create output directory
            await self._setup_output_dir()

            self.logger.debug(
                f"Initialized with repository path={self.repository_path}"
            )

        except Exception as e:
            self.logger.error(f"Failed to initialize analyzer: {e}")
            raise WorkflowError(f"Failed to initialize analyzer: {e}") from e

    async def cleanup(self) -> None:
        """Clean up provider resources.

        This method is called automatically when the context manager exits.
        """
        # Clean up specific resources
        self.repo = None

        # Call the base class cleanup
        await super().cleanup()

    async def execute(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """Execute repository analysis.

        Args:
            input_data: Input data with keys:
                - analysis_types: Optional list of analysis types to run
                - repository_path: Optional repository path override
                - options: Optional analysis options

        Returns:
            Analysis results with keys:
                - summary: Overall analysis summary
                - code_quality: Code quality metrics (if requested)
                - structure: Repository structure analysis (if requested)
                - insights: AI-generated insights
                - recommendations: Improvement recommendations
        """
        # Get analysis configuration
        analysis_types = input_data.get("analysis_types", self.analysis_types)
        repo_path = input_data.get("repository_path", self.repository_path)
        options = input_data.get("options", {})

        try:
            # Run requested analyses
            results = {}

            if "code_quality" in analysis_types:
                results["code_quality"] = await self._analyze_code_quality(
                    repo_path, options
                )

            if "structure" in analysis_types:
                results["structure"] = await self._analyze_structure(repo_path, options)

            # Generate insights and recommendations based on rules without LLM
            results["insights"] = await self._generate_insights(results)
            results["recommendations"] = await self._generate_recommendations(results)
            results["summary"] = await self._create_summary(results)

            return results

        except Exception as e:
            self.logger.error(f"Analysis failed: {e}")
            raise WorkflowError(f"Analysis failed: {e}") from e

    async def _setup_repository(self) -> Any:
        """Set up repository access."""
        repo_path = pathlib.Path(self.repository_path)
        if not repo_path.exists():
            raise WorkflowError(f"Repository path does not exist: {repo_path}")
        return repo_path

    async def _setup_output_dir(self) -> None:
        """Set up output directory."""
        output_path = pathlib.Path(self.output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

    async def _analyze_code_quality(
        self, repo_path: str, options: dict[str, Any]
    ) -> dict[str, Any]:
        """Analyze code quality."""
        results = {"metrics": {}, "issues": [], "stats": {}}

        try:
            # Get all Python files
            python_files = list(pathlib.Path(repo_path).rglob("*.py"))

            # Basic stats
            total_lines = 0
            total_files = len(python_files)

            for file_path in python_files[: self.max_files]:
                try:
                    stats = get_file_stats(file_path)
                    total_lines += stats["total_lines"]

                    # Add file stats
                    results["stats"][str(file_path)] = {
                        "lines": stats["total_lines"],
                        "code_lines": stats["code_lines"],
                        "comment_lines": stats["comment_lines"],
                        "blank_lines": stats["blank_lines"],
                    }

                except Exception as e:
                    self.logger.warning(f"Error analyzing file {file_path}: {e}")
                    continue

            # Overall metrics
            results["metrics"] = {
                "total_files": total_files,
                "total_lines": total_lines,
                "files_analyzed": len(results["stats"]),
                "average_lines_per_file": total_lines / total_files
                if total_files > 0
                else 0,
            }

            return results

        except Exception as e:
            self.logger.error(f"Code quality analysis failed: {e}")
            return {"metrics": {}, "issues": [str(e)], "stats": {}}

    async def _analyze_structure(
        self, repo_path: str, options: dict[str, Any]
    ) -> dict[str, Any]:
        """Analyze repository structure."""
        results = {
            "directories": {},
            "file_types": {},
            "top_level_structure": [],
            "stats": {},
        }

        try:
            repo = pathlib.Path(repo_path)

            # Analyze directory structure
            for root, dirs, files in os.walk(repo):
                rel_path = os.path.relpath(root, repo)
                if rel_path == ".":
                    rel_path = ""

                # Skip excluded directories
                if any(p in root for p in self.exclude_patterns):
                    continue

                # Collect files that match include patterns
                matching_files = []
                for file in files:
                    file_path = os.path.join(rel_path, file)
                    # Include all files if no patterns specified
                    if not self.include_patterns or any(
                        p in file_path for p in self.include_patterns
                    ):
                        matching_files.append(file)

                # Add directory info if it has matching files
                if matching_files:
                    results["directories"][rel_path or "."] = {
                        "file_count": len(matching_files),
                        "files": matching_files,
                    }

                    # Add to top level if depth is 0 or 1
                    if rel_path == "" or "/" not in rel_path:
                        results["top_level_structure"].append(
                            {
                                "name": rel_path or ".",
                                "type": "directory",
                                "items": len(matching_files),
                            }
                        )

                    # Collect file types
                    for file in matching_files:
                        ext = os.path.splitext(file)[1] or "no_extension"
                        if ext not in results["file_types"]:
                            results["file_types"][ext] = 0
                        results["file_types"][ext] += 1

            # Overall stats
            total_files = sum(d["file_count"] for d in results["directories"].values())
            results["stats"] = {
                "total_files": total_files,
                "directory_count": len(results["directories"]),
                "extension_count": len(results["file_types"]),
                "top_extensions": dict(
                    sorted(
                        results["file_types"].items(), key=lambda x: x[1], reverse=True
                    )[:5]
                ),
            }

            return results

        except Exception as e:
            self.logger.error(f"Structure analysis failed: {e}")
            return {
                "directories": {},
                "file_types": {},
                "top_level_structure": [],
                "stats": {},
                "error": str(e),
            }

    async def _generate_insights(self, results: dict[str, Any]) -> dict[str, Any]:
        """Generate insights from analysis results."""
        insights = {"code_quality": [], "structure": [], "general": []}

        try:
            # Add code quality insights if available
            if "code_quality" in results:
                code_quality = results["code_quality"]
                metrics = code_quality.get("metrics", {})

                if metrics:
                    # Insight on codebase size
                    total_files = metrics.get("total_files", 0)
                    if total_files > 100:
                        insights["code_quality"].append(
                            "Large codebase with over 100 files"
                        )
                    elif total_files > 50:
                        insights["code_quality"].append("Medium-sized codebase")
                    else:
                        insights["code_quality"].append("Small codebase")

                    # Insight on average file size
                    avg_lines = metrics.get("average_lines_per_file", 0)
                    if avg_lines > 300:
                        insights["code_quality"].append(
                            "Files are very large on average"
                        )
                    elif avg_lines > 100:
                        insights["code_quality"].append(
                            "Files have typical size on average"
                        )
                    else:
                        insights["code_quality"].append("Files are small on average")

            # Add structure insights if available
            if "structure" in results:
                structure = results["structure"]
                stats = structure.get("stats", {})

                if stats:
                    # Directory structure insights
                    dir_count = stats.get("directory_count", 0)
                    if dir_count > 20:
                        insights["structure"].append(
                            "Deep directory structure with many subdirectories"
                        )

                    # File type insights
                    file_types = structure.get("file_types", {})
                    if len(file_types) > 10:
                        insights["structure"].append(
                            "Diverse file types indicate complex project"
                        )

                    # Top-level structure insights
                    top_level = structure.get("top_level_structure", [])
                    if len(top_level) > 10:
                        insights["structure"].append(
                            "Flat top-level structure with many entries"
                        )

            # Add general insights
            insights["general"].append("Standard repository structure detected")

            return insights

        except Exception as e:
            self.logger.error(f"Failed to generate insights: {e}")
            return {
                "code_quality": [],
                "structure": [],
                "general": ["Failed to generate insights due to an error"],
            }

    async def _generate_recommendations(
        self, results: dict[str, Any]
    ) -> dict[str, Any]:
        """Generate recommendations from analysis results."""
        recommendations = {"code_quality": [], "structure": [], "general": []}

        try:
            # Add code quality recommendations if available
            if "code_quality" in results:
                code_quality = results["code_quality"]
                metrics = code_quality.get("metrics", {})

                if metrics:
                    # Recommendation on large files
                    avg_lines = metrics.get("average_lines_per_file", 0)
                    if avg_lines > 300:
                        recommendations["code_quality"].append(
                            "Consider breaking down large files into smaller modules"
                        )

                    # Recommendation on comments
                    stats = code_quality.get("stats", {})
                    if stats:
                        total_comment_lines = sum(
                            s.get("comment_lines", 0) for s in stats.values()
                        )
                        total_code_lines = sum(
                            s.get("code_lines", 0) for s in stats.values()
                        )

                        if total_code_lines > 0:
                            comment_ratio = total_comment_lines / total_code_lines
                            if comment_ratio < 0.1:
                                recommendations["code_quality"].append(
                                    "Consider adding more comments to improve code documentation"
                                )

            # Add structure recommendations if available
            if "structure" in results:
                structure = results["structure"]
                file_types = structure.get("file_types", {})

                # Recommendations on project structure
                if ".py" in file_types and "setup.py" not in structure.get(
                    "directories", {}
                ).get(".", {}).get("files", []):
                    recommendations["structure"].append(
                        "Consider adding setup.py for better Python packaging"
                    )

                if not any(
                    f == "README.md"
                    for f in structure.get("directories", {})
                    .get(".", {})
                    .get("files", [])
                ):
                    recommendations["structure"].append(
                        "Add a README.md file to document the project"
                    )

            # Add general recommendations
            recommendations["general"].append(
                "Consider using static code analysis tools for deeper insights"
            )

            return recommendations

        except Exception as e:
            self.logger.error(f"Failed to generate recommendations: {e}")
            return {
                "code_quality": [],
                "structure": [],
                "general": ["Failed to generate recommendations due to an error"],
            }

    async def _create_summary(self, results: dict[str, Any]) -> dict[str, Any]:
        """Create summary from analysis results."""
        summary = {"overview": "", "key_metrics": {}, "findings": []}

        try:
            # Overview section
            code_quality_metrics = results.get("code_quality", {}).get("metrics", {})
            structure_stats = results.get("structure", {}).get("stats", {})

            total_files = code_quality_metrics.get(
                "total_files", 0
            ) or structure_stats.get("total_files", 0)
            total_dirs = structure_stats.get("directory_count", 0)

            summary["overview"] = (
                f"Repository analysis found {total_files} files across {total_dirs} directories."
            )

            # Key metrics
            summary["key_metrics"] = {
                "total_files": total_files,
                "total_directories": total_dirs,
                "file_types": len(structure_stats.get("top_extensions", {})),
                "average_file_size": code_quality_metrics.get(
                    "average_lines_per_file", 0
                ),
            }

            # Findings from insights and recommendations
            for insight in results.get("insights", {}).get("general", []):
                summary["findings"].append({"type": "insight", "description": insight})

            for recommendation in results.get("recommendations", {}).get("general", []):
                summary["findings"].append(
                    {"type": "recommendation", "description": recommendation}
                )

            return summary

        except Exception as e:
            self.logger.error(f"Failed to create summary: {e}")
            return {
                "overview": "Failed to create summary due to an error",
                "key_metrics": {},
                "findings": [],
            }
