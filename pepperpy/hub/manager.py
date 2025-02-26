"""Hub manager implementation for artifact management."""

from typing import Any, Dict, List, Optional, Type

from .base import HubArtifact, HubInterface


class HubManager(HubInterface):
    """Manager class for the Pepperpy Hub system."""

    def __init__(self):
        self._storage: Dict[str, Dict[str, Any]] = {}
        self._artifact_types: Dict[str, Type[HubArtifact]] = {}

    def register_artifact_type(
        self, type_name: str, artifact_class: Type[HubArtifact]
    ) -> None:
        """Register a new artifact type."""
        self._artifact_types[type_name] = artifact_class

    def get_artifact(self, artifact_id: str) -> HubArtifact:
        """Retrieve an artifact from the hub."""
        if artifact_id not in self._storage:
            raise KeyError(f"Artifact {artifact_id} not found")

        data = self._storage[artifact_id]
        artifact_type = self._artifact_types[data["type"]]
        return artifact_type.deserialize(data)

    def store_artifact(
        self, artifact: HubArtifact, metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Store an artifact in the hub."""
        if not artifact.validate():
            raise ValueError("Invalid artifact")

        artifact_data = artifact.serialize()
        if metadata:
            artifact_data["metadata"] = {**artifact.metadata, **metadata}

        self._storage[artifact.artifact_id] = artifact_data
        return artifact.artifact_id

    def list_artifacts(
        self, filter_criteria: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """List artifacts matching the given criteria."""
        artifacts = list(self._storage.values())

        if filter_criteria:
            return [
                artifact
                for artifact in artifacts
                if all(
                    artifact.get(key) == value for key, value in filter_criteria.items()
                )
            ]

        return artifacts

    def delete_artifact(self, artifact_id: str) -> bool:
        """Delete an artifact from the hub."""
        if artifact_id in self._storage:
            del self._storage[artifact_id]
            return True
        return False
