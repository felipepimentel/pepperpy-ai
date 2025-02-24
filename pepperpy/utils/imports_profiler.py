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

    @property
    def has_error(self) -> bool:
        """Check if import had errors.

        Returns:
            True if import had errors
        """
        return bool(self.errors)

    @property
    def dependency_count(self) -> int:
        """Get number of dependencies.

        Returns:
            Number of dependencies
        """
        return len(self.dependencies)


class ImportProfiler:
    """Import profiler for tracking module import performance."""

    def __init__(self) -> None:
        """Initialize profiler."""
        self._profiles: dict[str, ImportProfile] = {}
        self._start_times: dict[str, float] = {}
        self._memory_before: dict[str, int] = {}
        self._process = psutil.Process()
        self._total_memory_before = self._get_memory_usage()
        self._total_imports = 0
        self._total_errors = 0

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
        self._total_imports += 1

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
            self._total_errors += 1

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

    def get_slow_imports(
        self, threshold: float = 0.1, include_deps: bool = True
    ) -> list[ImportProfile]:
        """Get slow module imports.

        Args:
            threshold: Duration threshold in seconds
            include_deps: Whether to include imports with slow dependencies

        Returns:
            List of slow import profiles
        """
        slow_imports = []
        for profile in self._profiles.values():
            # Check direct import duration
            if profile.duration > threshold:
                slow_imports.append(profile)
                continue

            # Check dependency durations
            if include_deps:
                total_duration = profile.duration
                for dep in profile.dependencies:
                    dep_profile = self._profiles.get(dep)
                    if dep_profile:
                        total_duration += dep_profile.duration
                if total_duration > threshold:
                    slow_imports.append(profile)

        return sorted(slow_imports, key=lambda p: p.duration, reverse=True)

    def get_memory_intensive_imports(
        self, threshold: int = 1024 * 1024, include_deps: bool = True
    ) -> list[ImportProfile]:
        """Get memory intensive imports.

        Args:
            threshold: Memory threshold in bytes
            include_deps: Whether to include imports with memory intensive dependencies

        Returns:
            List of memory intensive import profiles
        """
        memory_imports = []
        for profile in self._profiles.values():
            # Check direct memory impact
            if profile.memory_delta > threshold:
                memory_imports.append(profile)
                continue

            # Check dependency memory impact
            if include_deps:
                total_memory = profile.memory_delta
                for dep in profile.dependencies:
                    dep_profile = self._profiles.get(dep)
                    if dep_profile:
                        total_memory += dep_profile.memory_delta
                if total_memory > threshold:
                    memory_imports.append(profile)

        return sorted(memory_imports, key=lambda p: p.memory_delta, reverse=True)

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
        if not self._profiles:
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
                "memory_intensive_imports": 0,
                "import_chains": 0,
                "max_chain_length": 0,
            }

        # Time analysis
        durations = [p.duration for p in self._profiles.values()]
        total_duration = sum(durations)
        avg_duration = total_duration / len(durations)
        max_duration = max(durations)

        # Dependency analysis
        dep_counts = [len(p.dependencies) for p in self._profiles.values()]
        avg_deps = sum(dep_counts) / len(dep_counts)
        max_deps = max(dep_counts)

        # Memory analysis
        memory_impacts = [p.memory_delta for p in self._profiles.values()]
        total_memory = sum(memory_impacts)
        avg_memory = total_memory / len(memory_impacts)
        max_memory = max(memory_impacts)

        # Chain analysis
        chains = [self.get_import_chain(m) for m in self._profiles]
        max_chain = max(len(c) for c in chains)

        return {
            "total_imports": self._total_imports,
            "total_duration": total_duration,
            "average_duration": avg_duration,
            "max_duration": max_duration,
            "error_count": self._total_errors,
            "average_dependencies": avg_deps,
            "max_dependencies": max_deps,
            "slow_imports": len(self.get_slow_imports()),
            "total_memory_impact": total_memory,
            "average_memory_impact": avg_memory,
            "max_memory_impact": max_memory,
            "memory_intensive_imports": len(self.get_memory_intensive_imports()),
            "import_chains": len(chains),
            "max_chain_length": max_chain,
        }

    def clear(self) -> None:
        """Clear all import profiles."""
        self._profiles.clear()
        self._start_times.clear()
        self._memory_before.clear()
        self._total_memory_before = self._get_memory_usage()
        self._total_imports = 0
        self._total_errors = 0
