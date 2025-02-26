"""Base interfaces for the Pepperpy Hub system."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class HubInterface(ABC):
    """Base interface for the Pepperpy Hub system."""

    @abstractmethod
    def get_artifact(self, artifact_id: str) -> Any:
        """Retrieve an artifact from the hub."""
        pass

    @abstractmethod
    def store_artifact(
        self, artifact: Any, metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Store an artifact in the hub."""
        pass

    @abstractmethod
    def list_artifacts(
        self, filter_criteria: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """List artifacts matching the given criteria."""
        pass

    @abstractmethod
    def delete_artifact(self, artifact_id: str) -> bool:
        """Delete an artifact from the hub."""
        pass


class HubArtifact(ABC):
    """Base class for hub artifacts."""

    def __init__(self, artifact_id: str, metadata: Optional[Dict[str, Any]] = None):
        self.artifact_id = artifact_id
        self.metadata = metadata or {}

    @abstractmethod
    def validate(self) -> bool:
        """Validate the artifact."""
        pass

    @abstractmethod
    def serialize(self) -> Dict[str, Any]:
        """Serialize the artifact for storage."""
        pass

    @classmethod
    @abstractmethod
    def deserialize(cls, data: Dict[str, Any]) -> "HubArtifact":
        """Deserialize the artifact from storage."""
        pass
