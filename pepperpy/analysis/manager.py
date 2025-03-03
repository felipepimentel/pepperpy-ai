"""Code analysis manager module.

This module provides the main manager for code analysis operations,
coordinating multiple analyzers and aggregating their results.
"""

from pepperpy.core.common.analysis.analyzers import ComplexityAnalyzer, SecurityAnalyzer
from pepperpy.core.common.analysis.types import (
    AnalysisLevel,
    AnalysisResult,
    CodeAnalyzer,
)
from pepperpy.observability import MetricsManager


class CodeAnalysisManager:
    """Manager for code analysis operations.

    Coordinates multiple code analyzers and aggregates their results.
    Provides metrics tracking for analysis operations.

    Example:
        >>> manager = CodeAnalysisManager()
        >>> manager.register_analyzer("security", SecurityAnalyzer())
        >>> results = await manager.analyze_code("eval('1 + 1')")
        >>> assert results["SecurityAnalyzer"][0].level == AnalysisLevel.ERROR

    """

    def __init__(self) -> None:
        """Initialize manager.

        Registers default analyzers and sets up metrics tracking.
        """
        self._analyzers: dict[str, CodeAnalyzer] = {}
        self._metrics = MetricsManager.get_instance()

        # Register default analyzers
        self.register_analyzer("security", SecurityAnalyzer())
        self.register_analyzer("complexity", ComplexityAnalyzer())

    def register_analyzer(
        self, name: str, analyzer: CodeAnalyzer, replace: bool = False,
    ) -> None:
        """Register a code analyzer.

        Args:
            name: Name to register analyzer under
            analyzer: Analyzer instance to register
            replace: Whether to replace existing analyzer

        Raises:
            ValueError: If analyzer exists and replace is False

        """
        if name in self._analyzers and not replace:
            raise ValueError(f"Analyzer {name} already registered")
        self._analyzers[name] = analyzer

    def unregister_analyzer(self, name: str) -> None:
        """Unregister a code analyzer.

        Args:
            name: Name of analyzer to unregister

        Raises:
            KeyError: If analyzer doesn't exist

        """
        if name not in self._analyzers:
            raise KeyError(f"Analyzer {name} not registered")
        del self._analyzers[name]

    def get_analyzer(self, name: str) -> CodeAnalyzer:
        """Get a registered analyzer.

        Args:
            name: Name of analyzer to get

        Returns:
            The registered analyzer

        Raises:
            KeyError: If analyzer doesn't exist

        """
        if name not in self._analyzers:
            raise KeyError(f"Analyzer {name} not registered")
        return self._analyzers[name]

    async def analyze_code(
        self, code: str, analyzers: list[str] | None = None,
    ) -> dict[str, list[AnalysisResult]]:
        """Analyze code with selected analyzers.

        Args:
            code: Code to analyze
            analyzers: Optional list of analyzer names to use.
                If None, all registered analyzers are used.

        Returns:
            Dictionary mapping analyzer names to their results

        Raises:
            KeyError: If any requested analyzer doesn't exist

        """
        results = {}
        selected_analyzers = (
            [self.get_analyzer(name) for name in analyzers]
            if analyzers
            else self._analyzers.values()
        )

        for analyzer in selected_analyzers:
            try:
                self._metrics.increment("pepperpy_code_analysis_runs")
                results[analyzer.__class__.__name__] = analyzer.analyze(code)
            except Exception as e:
                self._metrics.increment("pepperpy_code_analysis_errors")
                results[analyzer.__class__.__name__] = [
                    AnalysisResult(
                        level=AnalysisLevel.ERROR,
                        message=f"Analysis failed: {e}",
                        details={"error": str(e)},
                    ),
                ]

        return results

    async def analyze_file(
        self, path: str, analyzers: list[str] | None = None,
    ) -> dict[str, list[AnalysisResult]]:
        """Analyze a file with selected analyzers.

        Args:
            path: Path to file to analyze
            analyzers: Optional list of analyzer names to use.
                If None, all registered analyzers are used.

        Returns:
            Dictionary mapping analyzer names to their results

        Raises:
            FileNotFoundError: If file doesn't exist
            PermissionError: If file can't be read
            KeyError: If any requested analyzer doesn't exist

        """
        results = {}
        selected_analyzers = (
            [self.get_analyzer(name) for name in analyzers]
            if analyzers
            else self._analyzers.values()
        )

        for analyzer in selected_analyzers:
            try:
                self._metrics.increment("pepperpy_code_analysis_runs")
                results[analyzer.__class__.__name__] = analyzer.analyze_file(path)
            except Exception as e:
                self._metrics.increment("pepperpy_code_analysis_errors")
                results[analyzer.__class__.__name__] = [
                    AnalysisResult(
                        level=AnalysisLevel.ERROR,
                        message=f"Analysis failed: {e}",
                        details={"error": str(e)},
                    ),
                ]

        return results

    async def analyze_module(
        self, module: str, analyzers: list[str] | None = None,
    ) -> dict[str, list[AnalysisResult]]:
        """Analyze a module with selected analyzers.

        Args:
            module: Module name to analyze
            analyzers: Optional list of analyzer names to use.
                If None, all registered analyzers are used.

        Returns:
            Dictionary mapping analyzer names to their results

        Raises:
            ImportError: If module can't be imported
            KeyError: If any requested analyzer doesn't exist

        """
        results = {}
        selected_analyzers = (
            [self.get_analyzer(name) for name in analyzers]
            if analyzers
            else self._analyzers.values()
        )

        for analyzer in selected_analyzers:
            try:
                self._metrics.increment("pepperpy_code_analysis_runs")
                results[analyzer.__class__.__name__] = analyzer.analyze_module(module)
            except Exception as e:
                self._metrics.increment("pepperpy_code_analysis_errors")
                results[analyzer.__class__.__name__] = [
                    AnalysisResult(
                        level=AnalysisLevel.ERROR,
                        message=f"Analysis failed: {e}",
                        details={"error": str(e)},
                    ),
                ]

        return results
