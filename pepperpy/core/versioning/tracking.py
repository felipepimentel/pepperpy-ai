"""
Version dependency tracking functionality.
"""

from typing import Dict, List, Optional, Set, Any
from collections import defaultdict

from ..types import Version, VersionDependency
from ..errors import VersionDependencyError


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
            "dependency_graph": {
                k: list(v) for k, v in self._dependency_graph.items()
            },
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

        return tracker """
Version history tracking functionality.
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime

from ..types import Version, VersionChange


@dataclass
class VersionHistoryEntry:
    """Represents a version history entry."""

    component: str
    version: Version
    timestamp: datetime
    changes: List[VersionChange] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class VersionHistory:
    """Tracker for version history."""

    def __init__(self):
        """Initialize version history."""
        self._history: Dict[str, List[VersionHistoryEntry]] = {}

    def add_entry(
        self,
        component: str,
        version: Version,
        changes: Optional[List[VersionChange]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Add a version history entry."""
        if component not in self._history:
            self._history[component] = []

        entry = VersionHistoryEntry(
            component=component,
            version=version,
            timestamp=datetime.now(),
            changes=changes or [],
            metadata=metadata or {},
        )
        self._history[component].append(entry)

    def get_history(
        self, component: str, limit: Optional[int] = None
    ) -> List[VersionHistoryEntry]:
        """Get version history for a component."""
        history = self._history.get(component, [])
        if limit:
            return history[-limit:]
        return history

    def get_latest_version(self, component: str) -> Optional[Version]:
        """Get the latest version for a component."""
        history = self._history.get(component, [])
        if not history:
            return None
        return history[-1].version

    def get_changes_between(
        self, component: str, from_version: Version, to_version: Version
    ) -> List[VersionChange]:
        """Get changes between two versions of a component."""
        changes = []
        history = self._history.get(component, [])
        collecting = False

        for entry in history:
            if entry.version == from_version:
                collecting = True
                continue
            if collecting:
                changes.extend(entry.changes)
                if entry.version == to_version:
                    break

        return changes

    def get_components_updated_since(
        self, timestamp: datetime
    ) -> Dict[str, List[Version]]:
        """Get components that have been updated since a given timestamp."""
        updates = {}
        for component, history in self._history.items():
            versions = [
                entry.version
                for entry in history
                if entry.timestamp >= timestamp
            ]
            if versions:
                updates[component] = versions
        return updates

    def search_history(
        self,
        component: Optional[str] = None,
        version: Optional[Version] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        metadata_filter: Optional[Dict[str, Any]] = None,
    ) -> List[VersionHistoryEntry]:
        """Search version history with filters."""
        results = []

        # Get the history to search through
        if component:
            histories = {component: self._history.get(component, [])}
        else:
            histories = self._history

        # Apply filters
        for comp, history in histories.items():
            for entry in history:
                if version and entry.version != version:
                    continue
                if start_time and entry.timestamp < start_time:
                    continue
                if end_time and entry.timestamp > end_time:
                    continue
                if metadata_filter:
                    matches = True
                    for key, value in metadata_filter.items():
                        if entry.metadata.get(key) != value:
                            matches = False
                            break
                    if not matches:
                        continue
                results.append(entry)

        return sorted(results, key=lambda x: x.timestamp)

    def to_dict(self) -> Dict[str, Any]:
        """Convert version history state to dictionary."""
        return {
            component: [
                {
                    "component": entry.component,
                    "version": str(entry.version),
                    "timestamp": entry.timestamp.isoformat(),
                    "changes": [
                        {
                            "type": c.type.name,
                            "description": c.description,
                            "breaking": c.breaking,
                            "affected_components": c.affected_components,
                        }
                        for c in entry.changes
                    ],
                    "metadata": entry.metadata,
                }
                for entry in history
            ]
            for component, history in self._history.items()
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "VersionHistory":
        """Create version history from dictionary."""
        history = cls()

        for component, entries in data.items():
            history._history[component] = []
            for entry_data in entries:
                version = Version.parse(entry_data["version"])  # type: ignore
                changes = [
                    VersionChange(
                        type=c["type"],
                        description=c["description"],
                        breaking=c["breaking"],
                        affected_components=c["affected_components"],
                    )
                    for c in entry_data["changes"]
                ]
                entry = VersionHistoryEntry(
                    component=entry_data["component"],
                    version=version,
                    timestamp=datetime.fromisoformat(entry_data["timestamp"]),
                    changes=changes,
                    metadata=entry_data["metadata"],
                )
                history._history[component].append(entry)

        return history """
Version tracking support.
"""

from .dependencies import DependencyTracker
from .history import VersionHistory, VersionHistoryEntry

__all__ = ["DependencyTracker", "VersionHistory", "VersionHistoryEntry"]
