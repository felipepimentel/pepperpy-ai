"""Refactoring script for the PepperPy project."""

import ast
import logging
from pathlib import Path
from typing import Optional

import click
import pytest

from scripts.refactoring_tools.ai_search import AICodeSearcher
from scripts.refactoring_tools.code_analysis import DependencyAnalyzer
from scripts.refactoring_tools.code_quality import (
    DocAnalyzer,
    SecurityChecker,
    StyleChecker,
)
from scripts.refactoring_tools.code_transformer import CodeFormatter, ImportOrganizer
from scripts.refactoring_tools.context import RefactoringContext
from scripts.refactoring_tools.pattern_analyzer import CodePatternAnalyzer
from scripts.refactoring_tools.performance import MemoryTracker, ProfileCollector
from scripts.refactoring_tools.test_generator import CoverageReporter, TestGenerator

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create context
context = RefactoringContext()

# Initialize tools
ai_searcher = AICodeSearcher(context)
pattern_analyzer = CodePatternAnalyzer(context)
dependency_analyzer = DependencyAnalyzer(context)
style_checker = StyleChecker(context)
doc_analyzer = DocAnalyzer(context)
security_checker = SecurityChecker(context)
import_organizer = ImportOrganizer(context)
code_formatter = CodeFormatter(context)
profile_collector = ProfileCollector(context)
memory_tracker = MemoryTracker(context)
test_generator = TestGenerator(context)
coverage_reporter = CoverageReporter(context)


@click.group()
def cli():
    """Refactoring tools for the PepperPy project."""
    pass


@cli.command()
@click.option("--pattern", help="Code pattern to search for")
@click.option("--similarity", type=float, default=0.8, help="Minimum similarity score")
def search_pattern(pattern: str, similarity: float):
    """Search for similar code patterns."""
    try:
        results = ai_searcher.search(pattern, min_similarity=similarity)
        for result in results:
            click.echo(f"\nMatch in {result.file_path}:")
            click.echo(f"Similarity: {result.similarity:.2f}")
            click.echo("Code:")
            click.echo(result.code)
    except Exception as e:
        logger.error(f"Failed to search patterns: {e}")


@cli.command()
@click.option("--module", help="Module to analyze")
@click.option("--base-class", help="Base class to analyze")
def analyze_pattern(module: Optional[str], base_class: Optional[str]):
    """Analyze implementation patterns."""
    try:
        if module:
            patterns = pattern_analyzer.extract_module_patterns(module)
            click.echo("\nModule patterns:")
            for pattern in patterns:
                click.echo(f"\nPattern type: {pattern.type}")
                click.echo(f"Name: {pattern.name}")
                click.echo(f"Description: {pattern.description}")
                click.echo("Implementation:")
                click.echo(pattern.implementation)

        if base_class:
            patterns = pattern_analyzer.extract_class_patterns(base_class)
            click.echo("\nClass patterns:")
            for pattern in patterns:
                click.echo(f"\nPattern type: {pattern.type}")
                click.echo(f"Name: {pattern.name}")
                click.echo(f"Description: {pattern.description}")
                click.echo("Implementation:")
                click.echo(pattern.implementation)
    except Exception as e:
        logger.error(f"Failed to analyze patterns: {e}")


@cli.command()
@click.option("--module", help="Module to analyze")
def analyze_dependencies(module: str):
    """Analyze module dependencies."""
    try:
        deps = dependency_analyzer.find_dependencies(module)
        click.echo("\nDirect dependencies:")
        for dep in deps.direct:
            click.echo(f"- {dep}")

        click.echo("\nFrom imports:")
        for imp in deps.from_imports:
            click.echo(f"- {imp}")

        click.echo("\nRelative imports:")
        for imp in deps.relative:
            click.echo(f"- {imp}")
    except Exception as e:
        logger.error(f"Failed to analyze dependencies: {e}")


@cli.command()
@click.option("--module", help="Module to check")
def check_quality(module: str):
    """Check code quality."""
    try:
        # Read module content
        with open(module, "r") as f:
            content = f.read()

        # Style check
        style_issues = style_checker.check_style(content)
        if style_issues:
            click.echo("\nStyle issues:")
            for issue in style_issues:
                click.echo(
                    f"Line {issue.line}, Col {issue.column}: "
                    f"{issue.message} ({issue.code})"
                )

        # Documentation check
        tree = ast.parse(content)
        doc_issues = doc_analyzer.check_documentation(tree)
        if doc_issues:
            click.echo("\nDocumentation issues:")
            for issue in doc_issues:
                click.echo(f"{issue.type}: {issue.message}")

        # Security check
        security_issues = security_checker.check_security(content)
        if security_issues:
            click.echo("\nSecurity issues:")
            for issue in security_issues:
                click.echo(f"- {issue}")
    except Exception as e:
        logger.error(f"Failed to check quality: {e}")


@cli.command()
@click.option("--module", help="Module to format")
def format_code(module: str):
    """Format code and organize imports."""
    try:
        # Read module content
        with open(module, "r") as f:
            content = f.read()

        # Organize imports
        content = import_organizer.organize_imports(content)

        # Format code
        content = code_formatter.format_code(content)

        # Write back
        with open(module, "w") as f:
            f.write(content)

        click.echo("Code formatted successfully")
    except Exception as e:
        logger.error(f"Failed to format code: {e}")


@cli.command()
@click.option("--module", help="Module to profile")
@click.option("--function", help="Function to profile")
def profile_code(module: str, function: str):
    """Profile code performance."""
    try:
        # Import module
        import importlib

        mod = importlib.import_module(module)
        func = getattr(mod, function)

        # Start profiling
        profile_collector.start_profiling()
        memory_tracker.start_tracking()

        try:
            # Run function
            func()
        finally:
            # Stop profiling
            profile_collector.stop_profiling()
            memory_tracker.stop_tracking()

        # Get stats
        profile_stats = profile_collector.get_stats()
        memory_stats = memory_tracker.get_snapshot()

        # Print results
        click.echo("\nProfile statistics:")
        for stat in profile_stats:
            click.echo(
                f"\n{stat.function_name}:"
                f"\n  Total time: {stat.total_time:.3f}s"
                f"\n  Calls: {stat.calls}"
                f"\n  Time per call: {stat.time_per_call:.3f}s"
                f"\n  Cumulative time: {stat.cumulative_time:.3f}s"
            )

        click.echo("\nMemory statistics:")
        click.echo(f"Current size: {memory_stats.current_size} bytes")
        click.echo(f"Peak size: {memory_stats.peak_size} bytes")

        click.echo("\nTop allocations:")
        for size, trace in memory_stats.allocations:
            click.echo(f"\nSize: {size} bytes")
            click.echo("Traceback:")
            for frame in trace:
                click.echo(f"  {frame}")
    except Exception as e:
        logger.error(f"Failed to profile code: {e}")


@cli.command()
@click.option("--module", help="Module to test")
def generate_tests(module: str):
    """Generate test cases."""
    try:
        # Generate tests
        test_cases = test_generator.generate_tests(module)

        # Create test file
        module_path = Path(module)
        test_path = module_path.parent / f"test_{module_path.name}"

        with open(test_path, "w") as f:
            # Write imports
            f.write("import pytest\n")
            f.write(f"from {module_path.stem} import *\n\n")

            # Write test cases
            for case in test_cases:
                f.write(f"\ndef {case.test_name}():\n")
                f.write(f'    """{case.description}"""\n')

                # Setup
                for line in case.setup:
                    f.write(f"    {line}\n")

                # Assertions
                for line in case.assertions:
                    f.write(f"    {line}\n")

                # Cleanup
                for line in case.cleanup:
                    f.write(f"    {line}\n")

                f.write("\n")

        click.echo(f"Test file generated: {test_path}")

        # Run tests and collect coverage
        coverage_reporter.start_coverage()
        try:
            pytest.main([str(test_path)])
        finally:
            coverage_reporter.stop_coverage()

        # Get coverage report
        report = coverage_reporter.get_report(module)

        click.echo("\nCoverage report:")
        click.echo(f"Line coverage: {report.line_coverage:.1%}")
        click.echo(f"Branch coverage: {report.branch_coverage:.1%}")

        if report.missing_lines:
            click.echo("\nMissing lines:")
            for line in report.missing_lines:
                click.echo(f"- Line {line}")

        if report.branch_misses:
            click.echo("\nMissing branches:")
            for line, branch in report.branch_misses:
                click.echo(f"- Line {line}, Branch {branch}")
    except Exception as e:
        logger.error(f"Failed to generate tests: {e}")


if __name__ == "__main__":
    cli()
