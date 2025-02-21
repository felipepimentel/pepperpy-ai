"""Security validation utilities."""

import logging
from pathlib import Path
from typing import Any, Dict, Optional

import yaml
from pydantic import BaseModel, ValidationError

from pepperpy.hub.base import HubConfig
from pepperpy.hub.errors import HubValidationError

logger = logging.getLogger(__name__)


class ValidationResult(BaseModel):
    """Result of a validation operation."""

    is_valid: bool
    errors: Optional[Dict[str, str]] = None
    warnings: Optional[Dict[str, str]] = None


async def validate_manifest(config: HubConfig) -> None:
    """Validate hub manifest configuration.

    Args:
        config: Hub configuration to validate

    Raises:
        HubValidationError: If validation fails
    """
    try:
        # Validate required fields
        if not config.name:
            raise HubValidationError("Hub name is required")

        if not config.type:
            raise HubValidationError("Hub type is required")

        # Validate paths
        if config.root_dir and not config.root_dir.exists():
            raise HubValidationError(
                f"Root directory does not exist: {config.root_dir}"
            )

        if config.manifest_path and not config.manifest_path.exists():
            raise HubValidationError(
                f"Manifest file does not exist: {config.manifest_path}"
            )

        # Validate resources and workflows
        if not config.resources and not config.workflows:
            logger.warning(
                "Hub has no resources or workflows defined",
                extra={"hub_name": config.name},
            )

        logger.info(
            "Hub manifest validation successful",
            extra={"hub_name": config.name},
        )

    except ValidationError as e:
        raise HubValidationError(
            "Invalid hub manifest configuration",
            details={"errors": e.errors()},
        )
    except Exception as e:
        raise HubValidationError(
            "Failed to validate hub manifest",
            details={"error": str(e)},
        )


async def validate_artifact(
    artifact_path: Path,
    artifact_type: str,
    schema: Dict[str, Any],
) -> ValidationResult:
    """Validate an artifact against its schema.

    Args:
        artifact_path: Path to artifact file
        artifact_type: Type of artifact
        schema: JSON schema for validation

    Returns:
        ValidationResult: Validation result

    Raises:
        HubValidationError: If validation fails
    """
    try:
        # Load artifact
        with open(artifact_path, "r") as f:
            artifact = yaml.safe_load(f)

        # Basic validation
        if not isinstance(artifact, dict):
            return ValidationResult(
                is_valid=False,
                errors={"format": "Artifact must be a YAML dictionary"},
            )

        # Schema validation
        # TODO: Implement JSON schema validation

        return ValidationResult(is_valid=True)

    except Exception as e:
        raise HubValidationError(
            f"Failed to validate {artifact_type} artifact",
            details={"path": str(artifact_path), "error": str(e)},
        )
