"""Security management for the Pepperpy Hub.

This module provides security features including:
- Artifact validation
- Access control
- Rate limiting
- Audit logging
- Code scanning
- Sandbox execution
"""

import asyncio
import hashlib
import hmac
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, Set

from jsonschema import validate as validate_schema
from pydantic import BaseModel, Field, validator

from pepperpy.core.base import Lifecycle
from pepperpy.core.types import ComponentState
from pepperpy.hub.artifacts import (
    agent_schema,
    capability_schema,
    tool_schema,
    workflow_schema,
)
from pepperpy.hub.errors import HubSecurityError, HubValidationError
from pepperpy.monitoring import audit_logger
from pepperpy.security.rate_limiter import RateLimiter
from pepperpy.security.sandbox import Sandbox
from pepperpy.security.scanner import CodeScanner
from pepperpy.security.types import ValidationResult

logger = logging.getLogger(__name__)


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
    secret_key: str = Field(
        default="",
        description="Secret key for cryptographic operations",
    )
    rate_limit_rpm: int = Field(
        default=60,
        description="Rate limit requests per minute",
    )
    rate_limit_burst: int = Field(
        default=10,
        description="Rate limit burst size",
    )
    require_signature: bool = Field(
        default=False,
        description="Whether signatures are required",
    )
    scan_code: bool = Field(
        default=True,
        description="Whether to perform code scanning",
    )

    @validator("secret_key")
    def validate_secret_key(cls, v: str) -> str:
        """Validate secret key."""
        if not v and cls.verify_signatures:
            raise ValueError(
                "Secret key required when signature verification is enabled"
            )
        return v


class SecurityManager(Lifecycle):
    """Manages security features for the Hub."""

    def __init__(self, config: Optional[SecurityConfig] = None) -> None:
        """Initialize security manager.

        Args:
            config: Optional security configuration
        """
        super().__init__()
        self.config = config or SecurityConfig()
        self._schemas: Dict[str, Dict[str, Any]] = {}
        self._locks: Dict[str, asyncio.Lock] = {}
        self._rate_limiter = RateLimiter(
            requests_per_minute=self.config.rate_limit_rpm,
            burst_size=self.config.rate_limit_burst,
        )
        self._sandbox = Sandbox() if self.config.sandbox_enabled else None
        self._scanner = CodeScanner() if self.config.scan_code else None
        self._state = ComponentState.UNREGISTERED

    async def initialize(self) -> None:
        """Initialize security manager.

        This loads security schemas and sets up rate limiting.

        Raises:
            HubSecurityError: If initialization fails
        """
        try:
            self._state = ComponentState.INITIALIZED

            # Load artifact schemas
            await self._load_schemas()

            # Initialize rate limiter
            self._rate_limiter = RateLimiter(
                requests_per_minute=self.config.rate_limit_rpm,
                burst_size=self.config.rate_limit_burst,
            )

            # Initialize sandbox if enabled
            if self.config.sandbox_enabled:
                self._sandbox = Sandbox()
                await self._sandbox.initialize()

            # Initialize code scanner if enabled
            if self.config.scan_code:
                self._scanner = CodeScanner()
                await self._scanner.initialize()

            # Update state
            self._state = ComponentState.RUNNING
            logger.info("Security manager initialized")

        except Exception as e:
            self._state = ComponentState.ERROR
            logger.error(f"Failed to initialize security manager: {e}")
            raise HubSecurityError(
                "Failed to initialize security manager", details={"error": str(e)}
            )

    async def cleanup(self) -> None:
        """Clean up security manager resources.

        Raises:
            HubSecurityError: If cleanup fails
        """
        try:
            self._schemas.clear()
            self._locks.clear()
            if self._sandbox:
                await self._sandbox.cleanup()
            if self._scanner:
                await self._scanner.cleanup()

            # Update state
            self._state = ComponentState.UNREGISTERED
            logger.info("Security manager cleaned up")

        except Exception as e:
            self._state = ComponentState.ERROR
            logger.error(f"Failed to cleanup security manager: {e}")
            raise HubSecurityError(
                "Failed to cleanup security manager", details={"error": str(e)}
            )

    async def _load_schemas(self) -> None:
        """Load artifact validation schemas."""
        try:
            # Load built-in schemas
            self._schemas = {
                "agent": agent_schema,
                "workflow": workflow_schema,
                "tool": tool_schema,
                "capability": capability_schema,
            }

            # Validate schemas
            for name, schema in self._schemas.items():
                try:
                    validate_schema(instance=schema, schema=schema)
        except Exception as e:
            raise HubValidationError(
                        f"Invalid schema for {name}",
                details={"error": str(e)},
            )

            logger.debug(f"Loaded {len(self._schemas)} validation schemas")

        except Exception as e:
            raise HubSecurityError(f"Failed to load schemas: {e}")

    async def validate_artifact(
        self,
        artifact_type: str,
        content: Dict[str, Any],
        metadata: Dict[str, Any],
    ) -> ValidationResult:
        """Validate an artifact.

        Args:
            artifact_type: Type of artifact
            content: Artifact content
            metadata: Artifact metadata

        Returns:
            ValidationResult: Result of validation

        Raises:
            HubValidationError: If validation fails
        """
        result = ValidationResult()
        try:
            # Get schema
            schema = self._schemas.get(artifact_type)
            if not schema:
                result.errors.append(f"Unknown artifact type: {artifact_type}")
                return result

            # Validate content
            try:
                validate_schema(instance=content, schema=schema)
            except Exception as e:
                result.errors.append(f"Content validation failed: {str(e)}")

            # Validate metadata
            required_fields = ["name", "version", "description", "author"]
            for field in required_fields:
                if not metadata.get(field):
                    result.errors.append(f"Missing required field: {field}")

            # Validate permissions
            if "security" in content:
                permissions = content["security"].get("permissions", [])
                invalid_perms = set(permissions) - self.config.allowed_permissions
                if invalid_perms:
                    result.errors.append(
                        f"Invalid permissions requested: {list(invalid_perms)}"
                    )

            # Validate signature if required
            if self.config.require_signature:
                if not metadata.get("signature"):
                    result.errors.append("Missing required signature")
                else:
                    try:
                        await self.validate_signature(
                            path=Path(f"/tmp/{artifact_type}_content"),
                            signature=metadata["signature"],
                        )
                    except Exception as e:
                        result.errors.append(f"Signature validation failed: {str(e)}")

            # Scan code if enabled
            if self.config.scan_code and self._scanner:
                scan_results = await self._scanner.scan(content)
                result.warnings.extend(scan_results.warnings)
                result.errors.extend(scan_results.errors)

            # Set validation result
            result.is_valid = len(result.errors) == 0

            # Log validation result
            await audit_logger.log({
                "event_type": "security.artifact_validation",
                "artifact_type": artifact_type,
                "is_valid": result.is_valid,
                "errors": result.errors,
                "warnings": result.warnings,
                "timestamp": datetime.utcnow().isoformat(),
            })

            return result

        except Exception as e:
            raise HubValidationError(
                "Artifact validation failed",
                details={"error": str(e)},
            )

    async def check_access(
        self,
        user_id: str,
        artifact_id: str,
        operation: str,
    ) -> bool:
        """Check if a user has access to perform an operation.

        Args:
            user_id: ID of the user
            artifact_id: ID of the artifact
            operation: Operation to check (read, write, delete)

        Returns:
            bool: True if access is allowed

        Raises:
            HubSecurityError: If access check fails
        """
        try:
            # Get lock for artifact
            if artifact_id not in self._locks:
                self._locks[artifact_id] = asyncio.Lock()

            async with self._locks[artifact_id]:
                # Check rate limits
                if not await self._rate_limiter.check_rate(user_id):
            await audit_logger.log({
                        "event_type": "security.rate_limit",
                "user_id": user_id,
                "artifact_id": artifact_id,
                "operation": operation,
                        "timestamp": datetime.utcnow().isoformat(),
            })
                return False

                # TODO: Implement proper access control
                # For now, return True for all operations
                await audit_logger.log({
                    "event_type": "security.access_check",
                    "user_id": user_id,
                    "artifact_id": artifact_id,
                    "operation": operation,
                    "timestamp": datetime.utcnow().isoformat(),
                    "granted": True,
                })
                return True

        except Exception as e:
            raise HubSecurityError(
                "Access check failed",
                details={
                    "user_id": user_id,
                    "artifact_id": artifact_id,
                    "operation": operation,
                    "error": str(e),
                },
            )

    async def validate_signature(
        self,
        path: Path,
        signature: Optional[bytes] = None,
    ) -> None:
        """Validate file signature.

        Args:
            path: Path to file to validate
            signature: Optional signature bytes. If not provided,
                     looks for .sig file

        Raises:
            HubSecurityError: If signature validation fails
        """
        if not self.config.verify_signatures:
            return

        try:
            # Read file content
            with open(path, "rb") as f:
                content = f.read()

            # Get signature
            if signature is None:
                sig_path = path.with_suffix(path.suffix + ".sig")
                if not sig_path.exists():
                    raise HubSecurityError(f"Signature file not found: {sig_path}")
                with open(sig_path, "r") as f:
                    signature = bytes.fromhex(f.read().strip())

            # Verify signature
            if not self.config.secret_key:
                raise HubSecurityError("No secret key configured")

            key = self.config.secret_key.encode()
            mac = hmac.new(key, content, hashlib.sha256)
            computed_sig = mac.digest()

            if not hmac.compare_digest(signature, computed_sig):
                raise HubSecurityError("Invalid signature")

            await audit_logger.log({
                "event_type": "security.signature_verified",
                "file": str(path),
                "timestamp": datetime.utcnow().isoformat(),
                "success": True,
            })

        except HubSecurityError:
            raise
        except Exception as e:
            raise HubSecurityError(
                "Failed to verify signature", details={"error": str(e)}
            )

    async def generate_signature(self, path: Path) -> bytes:
        """Generate signature for a file.

        Args:
            path: Path to file to sign

        Returns:
            bytes: Generated signature

        Raises:
            HubSecurityError: If signature generation fails
        """
        try:
            # Read file content
            with open(path, "rb") as f:
                content = f.read()

            # Generate signature
            if not self.config.secret_key:
                raise HubSecurityError("No secret key configured")

            key = self.config.secret_key.encode()
            mac = hmac.new(key, content, hashlib.sha256)
            signature = mac.digest()

            # Save signature
            sig_path = path.with_suffix(path.suffix + ".sig")
            with open(sig_path, "w") as f:
                f.write(signature.hex())

            await audit_logger.log({
                "event_type": "security.signature_generated",
                "file": str(path),
                "timestamp": datetime.utcnow().isoformat(),
                "success": True,
            })

            return signature

        except Exception as e:
            raise HubSecurityError(
                "Failed to generate signature", details={"error": str(e)}
            )

    async def sandbox_execute(
        self,
        artifact_id: str,
        code: str,
        timeout: int = 30,
    ) -> Dict[str, Any]:
        """Execute code in a sandbox environment.

        Args:
            artifact_id: ID of the artifact
            code: Code to execute
            timeout: Execution timeout in seconds

        Returns:
            Dict[str, Any]: Execution results

        Raises:
            HubSecurityError: If sandbox execution fails
        """
        if not self.config.sandbox_enabled or not self._sandbox:
            raise HubSecurityError("Sandbox execution not enabled")

        try:
            # Execute in sandbox
            result = await self._sandbox.execute(
                code=code,
                timeout=timeout,
                artifact_id=artifact_id,
            )

            await audit_logger.log({
                "event_type": "security.sandbox_execution",
                "artifact_id": artifact_id,
                "success": True,
                "timestamp": datetime.utcnow().isoformat(),
            })

            return result

        except Exception as e:
            raise HubSecurityError(
                "Sandbox execution failed",
                details={
                    "artifact_id": artifact_id,
                    "error": str(e),
                },
            )

    async def scan_code(
        self,
        artifact_id: str,
        code: str,
    ) -> ValidationResult:
        """Scan code for security issues.

        Args:
            artifact_id: ID of the artifact
            code: Code to scan

        Returns:
            ValidationResult: Scan results

        Raises:
            HubSecurityError: If code scanning fails
        """
        if not self.config.scan_code or not self._scanner:
            raise HubSecurityError("Code scanning not enabled")

        try:
            # Scan code
            result = await self._scanner.scan(code)

            await audit_logger.log({
                "event_type": "security.code_scan",
                "artifact_id": artifact_id,
                "success": True,
                "warnings": result.warnings,
                "errors": result.errors,
                "timestamp": datetime.utcnow().isoformat(),
            })

            return result

        except Exception as e:
            raise HubSecurityError(
                "Code scanning failed",
                details={
                    "artifact_id": artifact_id,
                    "error": str(e),
                },
            )
