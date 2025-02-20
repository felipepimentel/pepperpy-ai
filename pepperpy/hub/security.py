"""Hub security and validation.

This module provides security features for the Hub, including:
- Artifact validation
- Access control
- Signature verification
- Security policy enforcement
"""

import asyncio
import hashlib
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, Set
from uuid import UUID

import jsonschema
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from pydantic import BaseModel, Field

from pepperpy.core.logging import get_logger
from pepperpy.hub.artifacts import (
    agent_schema,
    capability_schema,
    tool_schema,
    workflow_schema,
)
from pepperpy.hub.errors import HubSecurityError, HubValidationError
from pepperpy.monitoring import audit_logger
from pepperpy.security import encryption

logger = get_logger(__name__)


class SecurityConfig(BaseModel):
    """Security configuration."""

    sandbox_enabled: bool = Field(
        default=True,
        description="Whether to enable sandboxing",
    )
    verify_signatures: bool = Field(
        default=True,
        description="Whether to verify signatures",
    )
    allowed_permissions: Set[str] = Field(
        default_factory=lambda: {
            "file_system",
            "network",
            "process",
            "env",
        },
        description="Allowed permissions for artifacts",
    )
    max_artifact_size: int = Field(
        default=10 * 1024 * 1024,  # 10MB
        description="Maximum artifact size in bytes",
    )


class SecurityPolicy:
    """Security policy for Hub artifacts."""

    def __init__(
        self,
        name: str,
        allowed_types: Set[str],
        required_fields: Set[str],
        max_size_bytes: int = 10 * 1024 * 1024,  # 10MB
        require_signature: bool = True,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize security policy.

        Args:
            name: Policy name
            allowed_types: Set of allowed artifact types
            required_fields: Set of required metadata fields
            max_size_bytes: Maximum artifact size in bytes
            require_signature: Whether signatures are required
            metadata: Optional policy metadata
        """
        self._id = uuid.uuid4()
        self.name = name
        self.allowed_types = allowed_types
        self.required_fields = required_fields
        self.max_size_bytes = max_size_bytes
        self.require_signature = require_signature
        self.metadata = metadata or {}
        self.created_at = datetime.utcnow()
        self.updated_at = self.created_at

    @property
    def id(self) -> UUID:
        """Get policy ID.

        Returns:
            UUID: Policy ID
        """
        return self._id


class SecurityManager:
    """Security manager for Hub artifacts."""

    def __init__(self, config: SecurityConfig) -> None:
        """Initialize security manager.

        Args:
            config: Security configuration
        """
        self.config = config
        self.encryption = encryption.AES256GCM()
        self.default_policy = SecurityPolicy(
            name="default",
            allowed_types={"prompt", "agent", "workflow", "model", "tool", "knowledge"},
            required_fields={"name", "version", "description"},
            require_signature=True,
        )
        self._schema_cache: Dict[str, Dict[str, Any]] = {}
        self._schemas = {
            "agent": agent_schema,
            "workflow": workflow_schema,
            "tool": tool_schema,
            "capability": capability_schema,
        }
        self._locks: Dict[str, asyncio.Lock] = {}

    def _load_schema(self, artifact_type: str) -> Dict[str, Any]:
        """Load JSON schema for artifact type.

        Args:
            artifact_type: Type of artifact

        Returns:
            Dict[str, Any]: JSON schema

        Raises:
            HubValidationError: If schema cannot be loaded
        """
        if artifact_type in self._schema_cache:
            return self._schema_cache[artifact_type]

        try:
            schema_path = (
                Path(__file__).parent / "schemas" / f"{artifact_type}_artifact.json"
            )
            if not schema_path.exists():
                raise HubValidationError(
                    f"Schema not found for artifact type: {artifact_type}",
                    details={"schema_path": str(schema_path)},
                )

            with open(schema_path) as f:
                schema = json.load(f)
                self._schema_cache[artifact_type] = schema
                return schema

        except Exception as e:
            raise HubValidationError(
                f"Failed to load schema for {artifact_type}",
                details={"error": str(e)},
            )

    async def validate_artifact(
        self,
        artifact_type: str,
        content: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Validate an artifact.

        Args:
            artifact_type: Type of artifact
            content: Artifact content
            metadata: Optional metadata

        Raises:
            HubValidationError: If validation fails
        """
        try:
            # Get schema
            if artifact_type not in self._schemas:
                raise HubValidationError(
                    f"Unknown artifact type: {artifact_type}",
                    details={"valid_types": list(self._schemas.keys())},
                )
            schema = self._schemas[artifact_type]

            # Validate against schema
            try:
                jsonschema.validate(content, schema)
            except jsonschema.exceptions.ValidationError as e:
                raise HubValidationError(
                    "Artifact content validation failed",
                    details={"error": str(e)},
                )

            # Check size
            content_size = len(json.dumps(content).encode())
            if content_size > self.config.max_artifact_size:
                raise HubValidationError(
                    "Artifact exceeds maximum size",
                    details={
                        "size": content_size,
                        "max_size": self.config.max_artifact_size,
                    },
                )

            # Validate permissions
            if "security" in content:
                permissions = content["security"].get("permissions", [])
                invalid_perms = set(permissions) - self.config.allowed_permissions
                if invalid_perms:
                    raise HubValidationError(
                        "Invalid permissions requested",
                        details={
                            "invalid_permissions": list(invalid_perms),
                            "allowed_permissions": list(
                                self.config.allowed_permissions
                            ),
                        },
                    )

            # Log validation
            await audit_logger.log({
                "event_type": "hub.validate_artifact",
                "artifact_type": artifact_type,
                "content_size": content_size,
                "timestamp": datetime.utcnow(),
            })

        except HubValidationError:
            raise
        except Exception as e:
            raise HubValidationError(f"Artifact validation failed: {e}") from e

    async def verify_signature(
        self,
        content: Dict[str, Any],
        signature: str,
        public_key: str,
    ) -> None:
        """Verify artifact signature.

        Args:
            content: Artifact content
            signature: Cryptographic signature
            public_key: Public key for verification

        Raises:
            HubSecurityError: If verification fails
        """
        if not self.config.verify_signatures:
            return

        try:
            # Compute content hash
            content_bytes = json.dumps(content, sort_keys=True).encode()
            content_hash = hashlib.sha256(content_bytes).hexdigest()

            # Verify signature
            key = serialization.load_pem_public_key(
                public_key.encode(),
                backend=default_backend(),
            )
            try:
                key.verify(
                    bytes.fromhex(signature),
                    content_hash.encode(),
                    padding.PSS(
                        mgf=padding.MGF1(hashes.SHA256()),
                        salt_length=padding.PSS.MAX_LENGTH,
                    ),
                    hashes.SHA256(),
                )
            except InvalidSignature:
                raise HubSecurityError("Invalid artifact signature")

            # Log verification
            await audit_logger.log({
                "event_type": "hub.verify_signature",
                "content_hash": content_hash,
                "timestamp": datetime.utcnow(),
            })

        except HubSecurityError:
            raise
        except Exception as e:
            raise HubSecurityError(f"Signature verification failed: {e}") from e

    async def check_access(
        self,
        user_id: str,
        artifact_id: str,
        operation: str,
    ) -> bool:
        """Check if user has access to perform operation.

        Args:
            user_id: User ID
            artifact_id: Artifact ID
            operation: Operation to check

        Returns:
            bool: Whether access is allowed

        Raises:
            HubSecurityError: If access check fails
        """
        try:
            # Get lock for artifact
            if artifact_id not in self._locks:
                self._locks[artifact_id] = asyncio.Lock()

            async with self._locks[artifact_id]:
                # TODO: Implement proper access control
                # For now, return True for all operations
                return True

        except Exception as e:
            raise HubSecurityError(f"Access check failed: {e}") from e

    async def sandbox_execute(
        self,
        artifact_type: str,
        content: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
    ) -> Any:
        """Execute artifact in sandbox.

        Args:
            artifact_type: Type of artifact
            content: Artifact content
            context: Optional execution context

        Returns:
            Any: Execution result

        Raises:
            HubSecurityError: If execution fails
        """
        if not self.config.sandbox_enabled:
            raise HubSecurityError("Sandbox execution is disabled")

        try:
            # TODO: Implement proper sandboxing
            # For now, just validate and return
            await self.validate_artifact(
                artifact_type=artifact_type,
                content=content,
            )
            return None

        except Exception as e:
            raise HubSecurityError(f"Sandbox execution failed: {e}") from e
