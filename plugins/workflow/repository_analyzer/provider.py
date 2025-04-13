"""Repository analyzer workflow provider."""

import logging
import os
import pathlib
from typing import Any, Dict, List

from pepperpy.workflow.base import WorkflowError, WorkflowProvider
from pepperpy.utils.file import get_file_stats

logger = logging.getLogger(__name__)


class RepositoryAnalyzerProvider(WorkflowProvider):
    """Analyzes code repositories and provides insights."""

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        """Initialize repository analyzer.

        Args:
            config: Optional configuration with keys:
                - repository_path: Path to repository (default: ".")
                - analysis_types: List of analysis types (default: ["code_quality", "structure"])
                - include_patterns: List of file patterns to include
                - exclude_patterns: List of file patterns to exclude
                - max_files: Maximum files to analyze (default: 1000)
                - output_dir: Output directory (default: "./output/analysis")
        """
        super().__init__(config)

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

    async def _initialize_resources(self) -> None:
        """Initialize analysis resources."""
        try:
            # Initialize repository access
            self.repo = await self._setup_repository()

            # Create output directory
            await self._setup_output_dir()

        except Exception as e:
            raise WorkflowError(f"Failed to initialize analyzer: {e}") from e

    async def _cleanup_resources(self) -> None:
        """Clean up analysis resources."""
        # Note: No resources to clean up currently,
        # but keeping this method for future extensibility
        pass

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
        if not self.initialized:
            await self.initialize()

        try:
            # Get analysis configuration
            analysis_types = input_data.get("analysis_types", self.analysis_types)
            repo_path = input_data.get("repository_path", self.repository_path)
            options = input_data.get("options", {})

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
        results = {
            "metrics": {},
            "issues": [],
            "stats": {}
        }

        try:
            # Get all Python files
            python_files = list(pathlib.Path(repo_path).rglob("*.py"))
            
            # Basic stats
            total_lines = 0
            total_files = len(python_files)
            
            for file_path in python_files[:self.max_files]:
                try:
                    stats = get_file_stats(file_path)
                    total_lines += stats["total_lines"]
                    
                    # Add file stats
                    results["stats"][str(file_path)] = {
                        "lines": stats["total_lines"],
                        "code_lines": stats["code_lines"],
                        "comment_lines": stats["comment_lines"],
                        "blank_lines": stats["blank_lines"]
                    }
                    
                except Exception as e:
                    logger.warning(f"Error analyzing file {file_path}: {e}")
                    continue
            
            # Overall metrics
            results["metrics"] = {
                "total_files": total_files,
                "total_lines": total_lines,
                "files_analyzed": len(results["stats"]),
                "average_lines_per_file": total_lines / total_files if total_files > 0 else 0
            }
            
            return results

        except Exception as e:
            logger.error(f"Code quality analysis failed: {e}")
            return {
                "metrics": {},
                "issues": [str(e)],
                "stats": {}
            }

    async def _analyze_structure(
        self, repo_path: str, options: dict[str, Any]
    ) -> dict[str, Any]:
        """Analyze repository structure."""
        results = {
            "directories": {},
            "file_types": {},
            "top_level_structure": [],
            "stats": {}
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
                
                # Count files by type
                for file in files:
                    ext = os.path.splitext(file)[1]
                    if ext:
                        results["file_types"][ext] = results["file_types"].get(ext, 0) + 1
                
                # Directory stats
                results["directories"][rel_path] = {
                    "files": len(files),
                    "subdirs": len(dirs),
                    "path": rel_path
                }
                
                # Top level structure (only for root)
                if not rel_path:
                    results["top_level_structure"] = [
                        d for d in dirs 
                        if not any(p.replace("**/", "") in d for p in self.exclude_patterns)
                    ]
            
            # Overall stats
            results["stats"] = {
                "total_directories": len(results["directories"]),
                "total_file_types": len(results["file_types"]),
                "top_file_types": dict(sorted(
                    results["file_types"].items(), 
                    key=lambda x: x[1], 
                    reverse=True
                )[:5])
            }
            
            return results

        except Exception as e:
            logger.error(f"Structure analysis failed: {e}")
            return {
                "directories": {},
                "file_types": {},
                "top_level_structure": [],
                "stats": {}
            }

    async def _generate_insights(self, results: dict[str, Any]) -> dict[str, Any]:
        """Generate insights from analysis results."""
        insights = {
            "code_quality": [],
            "structure": [],
            "general": []
        }
        
        try:
            # Code quality insights
            if "code_quality" in results:
                quality = results["code_quality"]
                metrics = quality.get("metrics", {})
                
                if metrics:
                    insights["code_quality"].extend([
                        f"Total files analyzed: {metrics.get('total_files', 0)}",
                        f"Average lines per file: {metrics.get('average_lines_per_file', 0):.1f}"
                    ])
            
            # Structure insights
            if "structure" in results:
                structure = results["structure"]
                stats = structure.get("stats", {})
                
                if stats:
                    insights["structure"].extend([
                        f"Total directories: {stats.get('total_directories', 0)}",
                        f"Most common file types: {', '.join(stats.get('top_file_types', {}).keys())}"
                    ])
                
                # Project organization
                top_level = structure.get("top_level_structure", [])
                if top_level:
                    insights["structure"].append(
                        f"Main project components: {', '.join(top_level)}"
                    )
            
            return insights

        except Exception as e:
            logger.error(f"Failed to generate insights: {e}")
            return {"error": str(e)}

    async def _generate_recommendations(
        self, results: dict[str, Any]
    ) -> dict[str, Any]:
        """Generate recommendations from analysis results."""
        recommendations = {
            "code_quality": [],
            "structure": [],
            "general": []
        }
        
        try:
            # Code quality recommendations
            if "code_quality" in results:
                quality = results["code_quality"]
                metrics = quality.get("metrics", {})
                
                if metrics.get("average_lines_per_file", 0) > 300:
                    recommendations["code_quality"].append(
                        "Consider breaking down large files into smaller modules"
                    )
            
            # Structure recommendations
            if "structure" in results:
                structure = results["structure"]
                
                # Check for common directories
                top_level = set(structure.get("top_level_structure", []))
                recommended = {"tests", "docs", "examples"}
                
                missing = recommended - top_level
                if missing:
                    recommendations["structure"].append(
                        f"Consider adding standard directories: {', '.join(missing)}"
                    )
            
            return recommendations

        except Exception as e:
            logger.error(f"Failed to generate recommendations: {e}")
            return {"error": str(e)}

    async def _create_summary(self, results: dict[str, Any]) -> dict[str, Any]:
        """Create analysis summary."""
        try:
            summary = {
                "overview": [],
                "key_metrics": {},
                "highlights": []
            }
            
            # Add code quality metrics
            if "code_quality" in results:
                quality = results["code_quality"]
                metrics = quality.get("metrics", {})
                
                if metrics:
                    summary["key_metrics"].update({
                        "total_files": metrics.get("total_files", 0),
                        "total_lines": metrics.get("total_lines", 0)
                    })
            
            # Add structure metrics
            if "structure" in results:
                structure = results["structure"]
                stats = structure.get("stats", {})
                
                if stats:
                    summary["key_metrics"].update({
                        "total_directories": stats.get("total_directories", 0),
                        "file_types": len(stats.get("top_file_types", {}))
                    })
            
            # Add insights highlights
            if "insights" in results:
                insights = results["insights"]
                for category in insights:
                    if insights[category]:
                        summary["highlights"].extend(insights[category][:2])
            
            # Create overview
            summary["overview"] = [
                f"Repository analysis completed successfully",
                f"Analyzed {summary['key_metrics'].get('total_files', 0)} files in {summary['key_metrics'].get('total_directories', 0)} directories",
                f"Found {summary['key_metrics'].get('file_types', 0)} different file types"
            ]
            
            return summary

        except Exception as e:
            logger.error(f"Failed to create summary: {e}")
            return {"error": str(e)}
