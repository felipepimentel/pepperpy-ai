"""Pepper Hub - A centralized hub for managing AI artifacts.

This package provides a simple and consistent way to manage AI artifacts like agents,
prompts, and workflows in a local directory structure (.pepper_hub).
"""

from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from structlog import get_logger

from pepperpy.hub.agents import Agent, AgentConfig, AgentRegistry
from pepperpy.hub.prompts import PromptRegistry
from pepperpy.hub.storage import LocalStorage
from pepperpy.hub.workflows import Workflow, WorkflowConfig, WorkflowRegistry

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
    """Central hub for managing and loading AI artifacts."""

    def __init__(self, storage_dir: Optional[Union[str, Path]] = None):
        """Initialize the hub with local storage.

        Args:
        ----
            storage_dir: Optional directory for storing artifacts locally.
                If None, uses default (~/.pepper_hub).

        """
        self.storage = LocalStorage(storage_dir or Path.home() / ".pepper_hub")

    def save_artifact(
        self,
        artifact_type: str,
        artifact_id: str,
        data: Dict[str, Any],
        version: Optional[str] = None,
    ) -> str:
        """Save an artifact.

        Args:
        ----
            artifact_type: Type of artifact (agent, prompt, workflow)
            artifact_id: ID of the artifact
            data: Artifact data/configuration
            version: Optional version string. If None, auto-generates.

        Returns:
        -------
            The version string used

        """
        return self.storage.save_artifact(artifact_type, artifact_id, data, version)

    def load_artifact(
        self,
        artifact_type: str,
        artifact_id: str,
        version: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Load an artifact.

        Args:
        ----
            artifact_type: Type of artifact (agent, prompt, workflow)
            artifact_id: ID of the artifact
            version: Optional version to load. If None, loads latest.

        Returns:
        -------
            The artifact data

        """
        return self.storage.load_artifact(artifact_type, artifact_id, version)

    def list_artifacts(
        self, artifact_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """List all artifacts of a given type or all types.

        Args:
        ----
            artifact_type: Optional type to filter by (agent, prompt, workflow)

        Returns:
        -------
            List of artifact metadata

        """
        return self.storage.list_artifacts(artifact_type)

    def list_versions(self, artifact_type: str, artifact_name: str) -> List[str]:
        """List all versions of a specific artifact.

        Args:
        ----
            artifact_type: Type of artifact
            artifact_name: Name of the artifact

        Returns:
        -------
            List of version strings

        """
        return self.storage.list_versions(artifact_type, artifact_name)

    def delete_artifact(
        self,
        artifact_type: str,
        artifact_name: str,
        version: Optional[str] = None,
    ) -> None:
        """Delete an artifact or specific version.

        Args:
        ----
            artifact_type: Type of artifact
            artifact_name: Name of the artifact
            version: Optional version to delete. If None, deletes all versions.

        """
        self.storage.delete_artifact(artifact_type, artifact_name, version)
