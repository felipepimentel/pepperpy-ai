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
from typing import Any

from pepperpy.workflow.provider import WorkflowProvider

logger = logging.getLogger(__name__)


class RepositoryAnalyzerWorkflow(WorkflowProvider):
    """Workflow for analyzing code repositories and providing insights."""

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        """Initialize the repository analyzer workflow.

        Args:
            config: Configuration parameters
        """
        super().__init__(config or {})

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
        """Initialize repository analyzer and resources."""
        if self.initialized:
            return

        try:
            # Import dependencies
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

            # Import and initialize PepperPy for LLM insights if needed
            if any(
                analysis_type in ["code_quality", "documentation"]
                for analysis_type in self.analysis_types
            ):
                from pepperpy.facade import PepperPyFacade

                self.pepperpy = PepperPyFacade()
                self.pepperpy.with_llm(
                    self.llm_provider,
                    model=self.llm_model,
                )
                await self.pepperpy.initialize()
                logger.info(
                    f"Initialized LLM provider for insights: {self.llm_provider}"
                )

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
        """Analyze code quality using linters.

        Args:
            input_data: Analysis configuration

        Returns:
            Analysis results
        """
        if not self.initialized:
            await self.initialize()

        linter = input_data.get("linter", "pylint")
        min_score = input_data.get("min_score", 7.0)

        try:
            # Get repository files
            files = self._get_repository_files()

            # Filter files based on linter
            if linter == "pylint":
                files = [f for f in files if f.endswith(".py")]

            if not files:
                return {
                    "status": "warning",
                    "message": f"No files found for {linter} analysis",
                    "report": {"overall_score": 0, "files_analyzed": 0, "issues": []},
                }

            # Run appropriate linter
            issues = []
            total_score = 0.0

            if linter == "pylint":
                # Import pylint modules
                from io import StringIO

                from pylint import lint
                from pylint.reporters.text import TextReporter

                # Run pylint on each file
                for file_path in files:
                    full_path = os.path.join(self.repository_path, file_path)

                    # Create string io for output capture
                    pylint_output = StringIO()
                    reporter = TextReporter(pylint_output)

                    try:
                        # Run pylint
                        lint.Run(
                            [full_path, "--output-format=text"],
                            reporter=reporter,
                            exit=False,
                        )

                        # Parse output
                        output = pylint_output.getvalue()

                        # Extract score (last line typically contains "Your code has been rated at X.XX/10")
                        score_line = [
                            line
                            for line in output.split("\n")
                            if "Your code has been rated at" in line
                        ]

                        if score_line:
                            # Extract score value
                            score_text = (
                                score_line[0]
                                .split("Your code has been rated at")[1]
                                .split("/")[0]
                                .strip()
                            )
                            try:
                                score = float(score_text)
                                total_score += score
                            except ValueError:
                                score = 0.0
                        else:
                            score = 0.0

                        # Extract issues
                        issue_lines = [
                            line
                            for line in output.split("\n")
                            if ":" in line
                            and any(
                                level in line
                                for level in [
                                    "error",
                                    "warning",
                                    "convention",
                                    "refactor",
                                ]
                            )
                        ]

                        for issue in issue_lines:
                            parts = issue.split(":", 3)
                            if len(parts) >= 4:
                                issues.append({
                                    "file": file_path,
                                    "line": parts[1],
                                    "code": parts[2].strip(),
                                    "message": parts[3].strip(),
                                })
                    except Exception as e:
                        logger.error(f"Error analyzing file {file_path}: {e}")
                        issues.append({
                            "file": file_path,
                            "line": "0",
                            "code": "ERROR",
                            "message": f"Failed to analyze: {e!s}",
                        })

                # Calculate average score
                average_score = total_score / len(files) if files else 0.0

                # LLM-based insights if available
                insights = []
                if self.pepperpy and hasattr(self.pepperpy, "llm") and len(issues) > 0:
                    # Create a prompt for the LLM to get insights
                    issues_text = "\n".join([
                        f"{i['file']} (line {i['line']}): {i['message']}"
                        for i in issues[:10]
                    ])
                    prompt = f"""Analyze these code quality issues from a Python project:
                    
{issues_text}

Provide 3-5 specific recommendations to improve code quality based on these issues.
Focus on patterns and recurring issues, not just individual fixes.
Format as a bulleted list."""

                    try:
                        messages = [
                            {
                                "role": "system",
                                "content": "You are a code quality expert helping analyze a Python project.",
                            },
                            {"role": "user", "content": prompt},
                        ]
                        insights_text = await self.pepperpy.llm.chat(messages)
                        insights = insights_text.split("\n")
                    except Exception as e:
                        logger.error(f"Error getting LLM insights: {e}")
                        insights = ["Failed to generate insights due to an error."]

                # Create report
                report = {
                    "overall_score": average_score,
                    "files_analyzed": len(files),
                    "issues": issues,
                    "insights": insights,
                    "failed_threshold": average_score < min_score,
                }

                # Save report to file
                output_file = input_data.get(
                    "output_file", f"code_quality_{linter}.json"
                )
                output_path = os.path.join(self.output_dir, output_file)
                with open(output_path, "w") as f:
                    json.dump(report, f, indent=2)

                return {
                    "status": "success",
                    "report": report,
                    "output_path": output_path,
                }
            else:
                return {"status": "error", "message": f"Unsupported linter: {linter}"}
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
