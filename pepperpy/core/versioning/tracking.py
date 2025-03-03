"""Version tracking and dependency management system.

This module provides tools for tracking version dependencies and history:

- VersionTracker: Core class for tracking component versions
- VersionHistory: Record of version changes over time
- DependencyTracker: Track dependencies between versioned components
- Version conflict detection and resolution
- Dependency graph analysis and validation

The version tracking system enables applications to maintain a consistent
version state across components and detect potential compatibility issues.
"""

from collections import defaultdict
from typing import Any, Dict, List, Optional, Set

from ..errors import VersionDependencyError
from ..types import Version, VersionDependency


class DependencyTracker:
    """Tracker for version dependencies."""

    def __init__(self):
        """Initialize dependency tracker."""
        self._dependencies: Dict[str, List[VersionDependency]] = defaultdict(list)
        self._versions: Dict[str, Version] = {}
        self._dependency_graph: Dict[str, Set[str]] = defaultdict(set)

    def register_version(self, component: str, version: Version) -> None:
        """Register a version for a component."""
        self._versions[component] = version

    def register_dependency(
        self, component: str, dependency: VersionDependency,
    ) -> None:
        """Register a dependency for a component."""
        self._dependencies[component].append(dependency)
        self._dependency_graph[component].add(dependency.component)

    def get_dependencies(self, component: str) -> List[VersionDependency]:
        """Get all dependencies for a component."""
        return self._dependencies.get(component, [])

    def get_version(self, component: str) -> Optional[Version]:
        """Get the current version of a component."""
        return self._versions.get(component)

    def check_dependencies(self, component: str) -> bool:
        """Check if all dependencies for a component are satisfied."""
        if component not in self._dependencies:
            return True

        for dep in self._dependencies[component]:
            dep_version = self.get_version(dep.component)
            if dep_version is None:
                if dep.required:
                    raise VersionDependencyError(
                        dep.component,
                        dep.version,
                        "Required dependency not found",
                    )
                continue

            if not self._check_version_compatibility(dep_version, dep):
                raise VersionDependencyError(
                    dep.component,
                    dep.version,
                    f"Incompatible version {dep_version}",
                )

        return True

    def get_dependency_graph(self) -> Dict[str, Set[str]]:
        """Get the dependency graph."""
        return dict(self._dependency_graph)

    def get_dependent_components(self, component: str) -> Set[str]:
        """Get components that depend on a given component."""
        dependents = set()
        for comp, deps in self._dependency_graph.items():
            if component in deps:
                dependents.add(comp)
        return dependents

    def check_circular_dependencies(self) -> List[List[str]]:
        """Check for circular dependencies in the graph."""
        cycles = []
        visited = set()
        path = []

        def dfs(node: str) -> None:
            if node in path:
                cycle = path[path.index(node) :]
                cycle.append(node)
                cycles.append(cycle)
                return

            if node in visited:
                return

            visited.add(node)
            path.append(node)

            for neighbor in self._dependency_graph[node]:
                dfs(neighbor)

            path.pop()

        for component in self._dependency_graph:
            if component not in visited:
                dfs(component)

        return cycles

    def get_update_order(self) -> List[str]:
        """Get the order in which components should be updated."""
        visited = set()
        order = []

        def dfs(node: str) -> None:
            if node in visited:
                return

            visited.add(node)

            for dep in self._dependencies[node]:
                dfs(dep.component)

            order.append(node)

        for component in self._dependency_graph:
            if component not in visited:
                dfs(component)

        return order

    def _check_version_compatibility(
        self, version: Version, dependency: VersionDependency,
    ) -> bool:
        """Check if a version satisfies a dependency."""
        if dependency.compatibility_range:
            min_version, max_version = dependency.compatibility_range
            return min_version <= version <= max_version

        # If no range is specified, versions must match exactly
        return version == dependency.version

    def to_dict(self) -> Dict[str, Any]:
        """Convert dependency tracker state to dictionary."""
        return {
            "dependencies": {
                component: [
                    {
                        "component": d.component,
                        "version": str(d.version),
                        "required": d.required,
                        "compatibility_range": (
                            (
                                str(d.compatibility_range[0]),
                                str(d.compatibility_range[1]),
                            )
                            if d.compatibility_range
                            else None
                        ),
                    }
                    for d in deps
                ]
                for component, deps in self._dependencies.items()
            },
            "versions": {k: str(v) for k, v in self._versions.items()},
            "dependency_graph": {k: list(v) for k, v in self._dependency_graph.items()},
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DependencyTracker":
        """Create dependency tracker from dictionary."""
        tracker = cls()

        # Restore versions
        for component, version_str in data.get("versions", {}).items():
            version = Version.parse(version_str)  # type: ignore
            tracker.register_version(component, version)

        # Restore dependencies
        for component, deps in data.get("dependencies", {}).items():
            for dep in deps:
                version = Version.parse(dep["version"])  # type: ignore
                compatibility_range = None
                if dep.get("compatibility_range"):
                    compatibility_range = (
                        Version.parse(dep["compatibility_range"][0]),  # type: ignore
                        Version.parse(dep["compatibility_range"][1]),  # type: ignore
                    )
                dependency = VersionDependency(
                    component=dep["component"],
                    version=version,
                    required=dep["required"],
                    compatibility_range=compatibility_range,
                )
                tracker.register_dependency(component, dependency)

        return tracker
