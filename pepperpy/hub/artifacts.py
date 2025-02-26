"""Hub artifacts module defining standard artifact types."""

from typing import Any, Dict, Optional

from ..base import HubArtifact


class ModelArtifact(HubArtifact):
    """Artifact representing a machine learning model."""

    def __init__(
        self,
        artifact_id: str,
        model_type: str,
        model_data: Any,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(artifact_id, metadata)
        self.model_type = model_type
        self.model_data = model_data

    def validate(self) -> bool:
        """Validate the model artifact."""
        return bool(self.model_type and self.model_data)

    def serialize(self) -> Dict[str, Any]:
        """Serialize the model artifact."""
        return {
            "type": "model",
            "model_type": self.model_type,
            "model_data": self.model_data,
            "metadata": self.metadata,
        }

    @classmethod
    def deserialize(cls, data: Dict[str, Any]) -> "ModelArtifact":
        """Deserialize a model artifact."""
        return cls(
            artifact_id=data["artifact_id"],
            model_type=data["model_type"],
            model_data=data["model_data"],
            metadata=data.get("metadata", {}),
        )


class DatasetArtifact(HubArtifact):
    """Artifact representing a dataset."""

    def __init__(
        self,
        artifact_id: str,
        data: Any,
        format: str,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(artifact_id, metadata)
        self.data = data
        self.format = format

    def validate(self) -> bool:
        """Validate the dataset artifact."""
        return bool(self.data and self.format)

    def serialize(self) -> Dict[str, Any]:
        """Serialize the dataset artifact."""
        return {
            "type": "dataset",
            "data": self.data,
            "format": self.format,
            "metadata": self.metadata,
        }

    @classmethod
    def deserialize(cls, data: Dict[str, Any]) -> "DatasetArtifact":
        """Deserialize a dataset artifact."""
        return cls(
            artifact_id=data["artifact_id"],
            data=data["data"],
            format=data["format"],
            metadata=data.get("metadata", {}),
        )
