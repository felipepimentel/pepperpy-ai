"""Pepper Hub - A centralized hub for managing AI artifacts.

This package provides a simple and consistent way to manage AI artifacts like agents,
prompts, and workflows in a local directory structure (.pepper_hub).
"""

from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from structlog import get_logger

from pepperpy.core.errors import ConfigurationError
from pepperpy.hub.agents import Agent, AgentConfig, AgentRegistry
from pepperpy.hub.prompts import PromptRegistry
from pepperpy.hub.storage import LocalStorage
from pepperpy.hub.workflow import WorkflowEngine
from pepperpy.hub.workflows import Workflow, WorkflowConfig, WorkflowRegistry
from pepperpy.monitoring import logger

# Configure logger
logger = get_logger()

__all__ = [
    "Agent",
    "AgentConfig",
    "AgentRegistry",
    "PromptRegistry",
    "Workflow",
    "WorkflowConfig",
    "WorkflowRegistry",
]


class Hub:
    """Central hub for managing Pepperpy artifacts and workflows."""

    def __init__(self, storage_dir: Union[str, Path]) -> None:
        """Initialize the hub.

        Args:
        ----
            storage_dir: Directory for storing artifacts.

        """
        self.storage_dir = Path(storage_dir)
        self.storage = LocalStorage(self.storage_dir)
        self.workflow_engine = WorkflowEngine(self.storage_dir / "workflows")
        self.log = logger.bind(component="hub")

        # Ensure directories exist
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        (self.storage_dir / "workflows").mkdir(exist_ok=True)
        (self.storage_dir / "agents").mkdir(exist_ok=True)

    def save_artifact(
        self,
        artifact_type: str,
        artifact_id: str,
        data: Dict[str, Any],
        version: Optional[str] = None,
    ) -> None:
        """Save an artifact to the hub.

        Args:
        ----
            artifact_type: Type of artifact (e.g., "agents", "workflows").
            artifact_id: ID of the artifact.
            data: Artifact data to save.
            version: Optional version string.

        """
        self.storage.save_artifact(artifact_type, artifact_id, data, version)

    def load_artifact(
        self,
        artifact_type: str,
        artifact_id: str,
        version: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Load an artifact from the hub.

        Args:
        ----
            artifact_type: Type of artifact (e.g., "agents", "workflows").
            artifact_id: ID of the artifact.
            version: Optional version string.

        Returns:
        -------
            Dict[str, Any]: Loaded artifact data.

        Raises:
        ------
            ConfigurationError: If artifact cannot be loaded.

        """
        try:
            return self.storage.load_artifact(artifact_type, artifact_id, version)
        except Exception as e:
            raise ConfigurationError(f"Failed to load artifact {artifact_id}: {str(e)}")

    def list_artifacts(
        self,
        artifact_type: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """List available artifacts of a given type.

        Args:
        ----
            artifact_type: Type of artifacts to list (optional).

        Returns:
        -------
            List[Dict[str, Any]]: List of artifact metadata including name,
            type, latest version, and all available versions.

        """
        return self.storage.list_artifacts(artifact_type)

    def delete_artifact(
        self,
        artifact_type: str,
        artifact_id: str,
        version: Optional[str] = None,
    ) -> None:
        """Delete an artifact from the hub.

        Args:
        ----
            artifact_type: Type of artifact to delete.
            artifact_id: ID of the artifact.
            version: Optional version to delete.

        """
        self.storage.delete_artifact(artifact_type, artifact_id, version)
