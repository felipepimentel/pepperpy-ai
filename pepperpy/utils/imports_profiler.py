"""Import profiling utilities.

This module provides utilities for profiling and analyzing module imports.
"""

import time
from dataclasses import dataclass, field
from typing import Any

import psutil


@dataclass
class ImportProfile:
    """Import profile information."""

    module: str
    duration: float
    memory_before: int
    memory_after: int
    dependencies: set[str] = field(default_factory=set)
    errors: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def memory_delta(self) -> int:
        """Get memory usage delta.

        Returns:
            Memory usage delta in bytes
        """
        return self.memory_after - self.memory_before


class ImportProfiler:
    """Import profiler for tracking module import performance."""

    def __init__(self) -> None:
        """Initialize profiler."""
        self._profiles: dict[str, ImportProfile] = {}
        self._start_times: dict[str, float] = {}
        self._memory_before: dict[str, int] = {}
        self._process = psutil.Process()

    def _get_memory_usage(self) -> int:
        """Get current memory usage.

        Returns:
            Memory usage in bytes
        """
        return self._process.memory_info().rss

    def start_import(self, module: str) -> None:
        """Start profiling module import.

        Args:
            module: Module name
        """
        self._start_times[module] = time.perf_counter()
        self._memory_before[module] = self._get_memory_usage()

    def finish_import(
        self,
        module: str,
        dependencies: set[str] | None = None,
        error: str | None = None,
    ) -> ImportProfile:
        """Finish profiling module import.

        Args:
            module: Module name
            dependencies: Optional module dependencies
            error: Optional import error

        Returns:
            Import profile
        """
        start_time = self._start_times.pop(module, time.perf_counter())
        memory_before = self._memory_before.pop(module, 0)
        memory_after = self._get_memory_usage()
        duration = time.perf_counter() - start_time

        profile = ImportProfile(
            module=module,
            duration=duration,
            memory_before=memory_before,
            memory_after=memory_after,
            dependencies=dependencies or set(),
        )

        if error:
            profile.errors.append(error)

        self._profiles[module] = profile
        return profile

    def get_profile(self, module: str) -> ImportProfile | None:
        """Get module import profile.

        Args:
            module: Module name

        Returns:
            Import profile or None if not found
        """
        return self._profiles.get(module)

    def get_all_profiles(self) -> dict[str, ImportProfile]:
        """Get all import profiles.

        Returns:
            Dictionary of module import profiles
        """
        return self._profiles.copy()

    def get_slow_imports(self, threshold: float = 0.1) -> list[ImportProfile]:
        """Get slow module imports.

        Args:
            threshold: Duration threshold in seconds

        Returns:
            List of slow import profiles
        """
        return [
            profile
            for profile in self._profiles.values()
            if profile.duration > threshold
        ]

    def get_import_chain(self, module: str) -> list[str]:
        """Get module import chain.

        Args:
            module: Module name

        Returns:
            List of modules in import chain
        """
        chain = []
        visited = set()

        def visit(mod: str) -> None:
            """Visit module and its dependencies.

            Args:
                mod: Module name
            """
            if mod in visited:
                return

            visited.add(mod)
            chain.append(mod)

            profile = self._profiles.get(mod)
            if profile:
                for dep in profile.dependencies:
                    visit(dep)

        visit(module)
        return chain

    def analyze_imports(self) -> dict[str, Any]:
        """Analyze import profiles.

        Returns:
            Dictionary containing import analysis results
        """
        total_imports = len(self._profiles)
        if not total_imports:
            return {
                "total_imports": 0,
                "total_duration": 0.0,
                "average_duration": 0.0,
                "max_duration": 0.0,
                "error_count": 0,
                "average_dependencies": 0.0,
                "max_dependencies": 0,
                "slow_imports": 0,
                "total_memory_impact": 0,
                "average_memory_impact": 0,
                "max_memory_impact": 0,
            }

        # Time analysis
        total_duration = sum(p.duration for p in self._profiles.values())
        avg_duration = total_duration / total_imports
        max_duration = max(p.duration for p in self._profiles.values())
        error_count = sum(len(p.errors) for p in self._profiles.values())

        # Dependency analysis
        dep_counts = [len(p.dependencies) for p in self._profiles.values()]
        avg_deps = sum(dep_counts) / len(dep_counts)
        max_deps = max(dep_counts)

        # Memory analysis
        memory_impacts = [p.memory_delta for p in self._profiles.values()]
        total_memory = sum(memory_impacts)
        avg_memory = total_memory / total_imports
        max_memory = max(memory_impacts)

        return {
            "total_imports": total_imports,
            "total_duration": total_duration,
            "average_duration": avg_duration,
            "max_duration": max_duration,
            "error_count": error_count,
            "average_dependencies": avg_deps,
            "max_dependencies": max_deps,
            "slow_imports": len(self.get_slow_imports()),
            "total_memory_impact": total_memory,
            "average_memory_impact": avg_memory,
            "max_memory_impact": max_memory,
        }

    def clear(self) -> None:
        """Clear all import profiles."""
        self._profiles.clear()
        self._start_times.clear()
        self._memory_before.clear()
