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
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set, Tuple

from ..errors import VersionDependencyError
from ..types import Version, VersionDependency


class VersionHistory:
    """Tracks the history of version changes for components."""

    def __init__(self):
        """Initialize version history tracker."""
        self._history: Dict[str, List[Tuple[Version, datetime]]] = defaultdict(list)
        self._current_versions: Dict[str, Version] = {}
        self._metadata: Dict[str, Dict[str, Any]] = defaultdict(dict)

    def record_version(
        self,
        component: str,
        version: Version,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Record a new version for a component.

        Args:
            component: Component name
            version: Version to record
            metadata: Optional metadata about the version
        """
        timestamp = datetime.now(timezone.utc)
        self._history[component].append((version, timestamp))
        self._current_versions[component] = version

        if metadata:
            self._metadata[component][str(version)] = metadata

    def get_version_history(self, component: str) -> List[Tuple[Version, datetime]]:
        """Get the version history for a component.

        Args:
            component: Component name

        Returns:
            List of (version, timestamp) tuples
        """
        return self._history.get(component, [])

    def get_current_version(self, component: str) -> Optional[Version]:
        """Get the current version of a component.

        Args:
            component: Component name

        Returns:
            Current version or None if not found
        """
        return self._current_versions.get(component)

    def get_version_metadata(self, component: str, version: Version) -> Dict[str, Any]:
        """Get metadata for a specific version of a component.

        Args:
            component: Component name
            version: Version to get metadata for

        Returns:
            Metadata dictionary
        """
        return self._metadata.get(component, {}).get(str(version), {})

    def has_component(self, component: str) -> bool:
        """Check if a component exists in the history.

        Args:
            component: Component name

        Returns:
            True if component exists, False otherwise
        """
        return component in self._history

    def get_components(self) -> List[str]:
        """Get all components in the history.

        Returns:
            List of component names
        """
        return list(self._history.keys())

    def get_version_count(self, component: str) -> int:
        """Get the number of versions recorded for a component.

        Args:
            component: Component name

        Returns:
            Number of versions
        """
        return len(self._history.get(component, []))

    def clear_history(self, component: Optional[str] = None) -> None:
        """Clear version history.

        Args:
            component: Component to clear history for, or None for all components
        """
        if component:
            if component in self._history:
                self._history[component] = []
                self._metadata[component] = {}
                if component in self._current_versions:
                    del self._current_versions[component]
        else:
            self._history.clear()
            self._metadata.clear()
            self._current_versions.clear()

    def to_dict(self) -> Dict[str, Any]:
        """Convert version history to dictionary.

        Returns:
            Dictionary representation
        """
        return {
            "history": {
                component: [
                    {"version": str(version), "timestamp": timestamp.isoformat()}
                    for version, timestamp in versions
                ]
                for component, versions in self._history.items()
            },
            "current_versions": {
                component: str(version)
                for component, version in self._current_versions.items()
            },
            "metadata": self._metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "VersionHistory":
        """Create version history from dictionary.

        Args:
            data: Dictionary representation

        Returns:
            VersionHistory instance
        """
        history = cls()

        # Restore history
        for component, versions in data.get("history", {}).items():
            for entry in versions:
                version = Version.parse(entry["version"])
                timestamp = datetime.fromisoformat(entry["timestamp"])
                history._history[component].append((version, timestamp))

        # Restore current versions
        for component, version_str in data.get("current_versions", {}).items():
            history._current_versions[component] = Version.parse(version_str)

        # Restore metadata
        history._metadata = data.get("metadata", {})

        return history


class VersionTracker:
    """Tracks and manages component versions and their dependencies."""

    def __init__(self):
        """Initialize version tracker."""
        self._history = VersionHistory()
        self._dependency_tracker = DependencyTracker()

    def register_version(
        self,
        component: str,
        version: Version,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Register a version for a component.

        Args:
            component: Component name
            version: Version to record
            metadata: Optional metadata about the version
        """
        self._history.record_version(component, version, metadata)
        self._dependency_tracker.register_version(component, version)

    def register_dependency(
        self, component: str, dependency: VersionDependency
    ) -> None:
        """Register a dependency for a component.

        Args:
            component: Component name
            dependency: Dependency to register
        """
        self._dependency_tracker.register_dependency(component, dependency)

    def get_version(self, component: str) -> Optional[Version]:
        """Get the current version of a component.

        Args:
            component: Component name

        Returns:
            Current version or None if not found
        """
        return self._history.get_current_version(component)

    def get_version_history(self, component: str) -> List[Tuple[Version, datetime]]:
        """Get the version history for a component.

        Args:
            component: Component name

        Returns:
            List of (version, timestamp) tuples
        """
        return self._history.get_version_history(component)

    def get_dependencies(self, component: str) -> List[VersionDependency]:
        """Get all dependencies for a component.

        Args:
            component: Component name

        Returns:
            List of dependencies
        """
        return self._dependency_tracker.get_dependencies(component)

    def check_dependencies(self, component: str) -> bool:
        """Check if all dependencies for a component are satisfied.

        Args:
            component: Component name

        Returns:
            True if all dependencies are satisfied
        """
        return self._dependency_tracker.check_dependencies(component)

    def get_dependency_graph(self) -> Dict[str, Set[str]]:
        """Get the dependency graph.

        Returns:
            Dependency graph as a dictionary
        """
        return self._dependency_tracker.get_dependency_graph()

    def get_dependent_components(self, component: str) -> Set[str]:
        """Get components that depend on a given component.

        Args:
            component: Component name

        Returns:
            Set of component names
        """
        return self._dependency_tracker.get_dependent_components(component)

    def check_circular_dependencies(self) -> List[List[str]]:
        """Check for circular dependencies in the graph.

        Returns:
            List of circular dependency chains
        """
        return self._dependency_tracker.check_circular_dependencies()

    def get_update_order(self) -> List[str]:
        """Get the order in which components should be updated.

        Returns:
            List of component names in update order
        """
        return self._dependency_tracker.get_update_order()

    def to_dict(self) -> Dict[str, Any]:
        """Convert version tracker to dictionary.

        Returns:
            Dictionary representation
        """
        return {
            "history": self._history.to_dict(),
            "dependencies": self._dependency_tracker.to_dict(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "VersionTracker":
        """Create version tracker from dictionary.

        Args:
            data: Dictionary representation

        Returns:
            VersionTracker instance
        """
        tracker = cls()

        # Restore history
        if "history" in data:
            tracker._history = VersionHistory.from_dict(data["history"])

        # Restore dependencies
        if "dependencies" in data:
            tracker._dependency_tracker = DependencyTracker.from_dict(
                data["dependencies"]
            )

        return tracker


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
        self, component: str, dependency: VersionDependency
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
        self, version: Version, dependency: VersionDependency
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
