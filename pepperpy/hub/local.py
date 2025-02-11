"""Local hub integration for loading artifacts.

This module provides functions for loading artifacts from the local Pepper Hub.
"""

import os
from pathlib import Path
from typing import Any, Dict, Optional

import yaml

from pepperpy.core.errors import ValidationError
from pepperpy.monitoring import bind_logger

# Configure logger
logger = bind_logger(module="hub.local")

# Default hub directory in user's home
HUB_DIR = Path.home() / ".pepper_hub"


def load_artifact(artifact_type: str, name: str, version: Optional[str] = None) -> Dict[str, Any]:
    """Load an artifact from the local hub.

    Args:
        artifact_type: Type of artifact (prompt, agent, workflow)
        name: Name of the artifact
        version: Optional version to load (defaults to latest)

    Returns:
        The artifact data as a dictionary

    Raises:
        ValidationError: If the artifact or version is not found
    """
    try:
        base_dir = HUB_DIR / f"{artifact_type}s" / name
        if not base_dir.exists():
            raise ValidationError(f"Artifact '{name}' of type '{artifact_type}' not found in local hub.")

        versions = sorted([v for v in os.listdir(base_dir) if v.endswith(".yaml")])
        if not versions:
            raise ValidationError(f"No versions available for artifact '{name}'.")

        if version:
            filename = f"{version}.yaml"
            if filename not in versions:
                raise ValidationError(f"Version '{version}' not found for artifact '{name}'.")
        else:
            filename = versions[-1]  # latest

        with open(base_dir / filename, "r", encoding="utf-8") as f:
            content = yaml.safe_load(f)

        logger.info(
            "Artifact loaded successfully",
            type=artifact_type,
            name=name,
            version=version or filename.replace(".yaml", ""),
        )
        return content

    except Exception as e:
        logger.error(
            "Failed to load artifact",
            error=str(e),
            type=artifact_type,
            name=name,
            version=version,
        )
        raise ValidationError(f"Failed to load artifact: {str(e)}") from e