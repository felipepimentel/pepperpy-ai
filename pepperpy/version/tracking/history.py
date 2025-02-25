"""
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

        return history 