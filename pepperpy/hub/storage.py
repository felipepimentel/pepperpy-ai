"""Storage module for managing local artifacts.

This module provides functionality for storing and retrieving artifacts locally.
"""

import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import yaml
from structlog import get_logger

logger = get_logger()


class LocalStorage:
    """Local storage implementation for artifacts."""

    def __init__(self, base_dir: Union[str, Path]):
        """Initialize local storage.

        Args:
            base_dir: Base directory for storing artifacts.

        """
        self.base_dir = Path(base_dir)
        self._ensure_directories()

    def _ensure_directories(self) -> None:
        """Ensure required directories exist."""
        for artifact_type in ["agents", "prompts", "workflows"]:
            os.makedirs(self.base_dir / artifact_type, exist_ok=True)

    def save_artifact(
        self,
        artifact_type: str,
        artifact_name: str,
        data: Dict[str, Any],
        version: Optional[str] = None,
    ) -> str:
        """Save an artifact to storage.

        Args:
            artifact_type: Type of artifact (agent, prompt, workflow)
            artifact_name: Name of the artifact
            data: Artifact data to save
            version: Optional version string. If None, auto-generates.

        Returns:
            The version string used for the artifact

        Raises:
            ValueError: If artifact_type is invalid

        """
        if artifact_type not in ["agents", "prompts", "workflows"]:
            raise ValueError(f"Invalid artifact type: {artifact_type}")

        # If no version provided, try to get from data or generate
        if not version:
            version = data.get("version", "1.0.0")

        # Ensure artifact directory exists
        artifact_dir = self.base_dir / artifact_type / artifact_name
        os.makedirs(artifact_dir, exist_ok=True)

        # Save artifact
        file_path = artifact_dir / f"{version}.yaml"
        with open(file_path, "w", encoding="utf-8") as f:
            yaml.safe_dump(data, f, sort_keys=False)

        logger.info(
            "Artifact saved",
            artifact_type=artifact_type,
            artifact_name=artifact_name,
            version=version,
        )
        return version

    def load_artifact(
        self,
        artifact_type: str,
        artifact_name: str,
        version: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Load an artifact from storage.

        Args:
            artifact_type: Type of artifact
            artifact_name: Name of the artifact
            version: Optional version to load. If None, loads latest.

        Returns:
            The artifact data

        Raises:
            FileNotFoundError: If artifact or version not found
            ValueError: If artifact_type is invalid

        """
        if artifact_type not in ["agents", "prompts", "workflows"]:
            raise ValueError(f"Invalid artifact type: {artifact_type}")

        artifact_dir = self.base_dir / artifact_type / artifact_name
        if not artifact_dir.exists():
            raise FileNotFoundError(
                f"Artifact not found: {artifact_type}/{artifact_name}"
            )

        if version:
            file_path = artifact_dir / f"{version}.yaml"
            if not file_path.exists():
                raise FileNotFoundError(
                    f"Version {version} not found for {artifact_type}/{artifact_name}"
                )
        else:
            # Get latest version
            versions = sorted(
                [f.stem for f in artifact_dir.glob("*.yaml")],
                key=lambda x: [int(p) for p in x.split(".")],
            )
            if not versions:
                raise FileNotFoundError(
                    f"No versions found for {artifact_type}/{artifact_name}"
                )
            file_path = artifact_dir / f"{versions[-1]}.yaml"

        with open(file_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)

    def list_artifacts(
        self, artifact_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """List all artifacts of a given type or all types.

        Args:
            artifact_type: Optional type to filter by

        Returns:
            List of artifact metadata

        """
        results = []
        types_to_check = (
            [artifact_type] if artifact_type else ["agents", "prompts", "workflows"]
        )

        for atype in types_to_check:
            type_dir = self.base_dir / atype
            if not type_dir.exists():
                continue

            for artifact_dir in type_dir.iterdir():
                if artifact_dir.is_dir():
                    versions = sorted(
                        [f.stem for f in artifact_dir.glob("*.yaml")],
                        key=lambda x: [int(p) for p in x.split(".")],
                    )
                    if versions:
                        results.append({
                            "name": artifact_dir.name,
                            "type": atype,
                            "latest_version": versions[-1],
                            "versions": versions,
                        })

        return results

    def list_versions(self, artifact_type: str, artifact_name: str) -> List[str]:
        """List all versions of a specific artifact.

        Args:
            artifact_type: Type of artifact
            artifact_name: Name of the artifact

        Returns:
            List of version strings

        Raises:
            FileNotFoundError: If artifact not found

        """
        artifact_dir = self.base_dir / artifact_type / artifact_name
        if not artifact_dir.exists():
            raise FileNotFoundError(
                f"Artifact not found: {artifact_type}/{artifact_name}"
            )

        versions = sorted(
            [f.stem for f in artifact_dir.glob("*.yaml")],
            key=lambda x: [int(p) for p in x.split(".")],
        )
        return versions

    def delete_artifact(
        self,
        artifact_type: str,
        artifact_name: str,
        version: Optional[str] = None,
    ) -> None:
        """Delete an artifact or specific version.

        Args:
            artifact_type: Type of artifact
            artifact_name: Name of the artifact
            version: Optional version to delete. If None, deletes all versions.

        Raises:
            FileNotFoundError: If artifact or version not found

        """
        artifact_dir = self.base_dir / artifact_type / artifact_name
        if not artifact_dir.exists():
            raise FileNotFoundError(
                f"Artifact not found: {artifact_type}/{artifact_name}"
            )

        if version:
            file_path = artifact_dir / f"{version}.yaml"
            if not file_path.exists():
                raise FileNotFoundError(
                    f"Version {version} not found for {artifact_type}/{artifact_name}"
                )
            os.remove(file_path)
            # Remove directory if empty
            if not any(artifact_dir.iterdir()):
                os.rmdir(artifact_dir)
        else:
            # Remove entire artifact directory
            import shutil

            shutil.rmtree(artifact_dir)

        logger.info(
            "Artifact deleted",
            artifact_type=artifact_type,
            artifact_name=artifact_name,
            version=version,
        )
