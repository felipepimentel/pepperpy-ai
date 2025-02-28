"""Hub security module.

This module provides security functionality specific to the Hub system.
"""

import hashlib
import json
from pathlib import Path

from pepperpy.common.errors import SecurityError
from pepperpy.monitoring import logger
from pepperpy.security.base import SecurityManager as BaseSecurityManager
from pepperpy.security.types import SecurityContext

# Configure logging
logger = logger.getChild(__name__)


class HubSecurityManager(BaseSecurityManager):
    """Security manager for Hub operations.

    This class handles:
    - Authentication for Hub operations
    - Authorization for artifact access
    - Signature validation for manifests
    - Encryption of sensitive data
    """

    def __init__(self, root_dir: Path) -> None:
        """Initialize hub security manager.

        Args:
            root_dir: Root directory for security data
        """
        super().__init__()
        self.root_dir = root_dir
        self.keys_dir = root_dir / "keys"
        self.tokens_dir = root_dir / "tokens"
        self._active = False

    async def initialize(self) -> None:
        """Initialize security manager.

        Creates required directories and loads security data.
        """
        try:
            # Create directories
            self.keys_dir.mkdir(parents=True, exist_ok=True)
            self.tokens_dir.mkdir(parents=True, exist_ok=True)

            # Load security data
            await self._load_security_data()

            self._active = True
            logger.info(
                "Hub security manager initialized", extra={"path": str(self.root_dir)}
            )

        except Exception as e:
            raise SecurityError(f"Failed to initialize hub security: {e}")

    async def cleanup(self) -> None:
        """Clean up security manager.

        Saves security data and cleans up resources.
        """
        try:
            if self._active:
                # Save security data
                await self._save_security_data()

                self._active = False
                logger.info("Hub security manager cleaned up")

        except Exception as e:
            raise SecurityError(f"Failed to clean up hub security: {e}")

    async def validate_signature(self, manifest_path: Path) -> None:
        """Validate the signature of a manifest file.

        Args:
            manifest_path: Path to manifest file

        Raises:
            SecurityError: If validation fails
        """
        try:
            # Load manifest and signature
            with open(manifest_path) as f:
                manifest = json.load(f)

            signature_path = manifest_path.with_suffix(".sig")
            if not signature_path.exists():
                raise SecurityError(f"Signature not found for {manifest_path}")

            with open(signature_path) as f:
                signature = f.read().strip()

            # Validate signature
            content = json.dumps(manifest, sort_keys=True)
            computed_hash = hashlib.sha256(content.encode()).hexdigest()

            if computed_hash != signature:
                raise SecurityError(f"Invalid signature for {manifest_path}")

            logger.info(
                "Validated manifest signature", extra={"manifest": str(manifest_path)}
            )

        except SecurityError:
            raise
        except Exception as e:
            raise SecurityError(f"Failed to validate manifest signature: {e}")

    async def check_artifact_access(
        self,
        artifact_id: str,
        context: SecurityContext,
    ) -> bool:
        """Check if an artifact can be accessed.

        Args:
            artifact_id: ID of artifact to check
            context: Security context for the request

        Returns:
            bool: Whether access is allowed

        Raises:
            SecurityError: If check fails
        """
        try:
            # Get artifact metadata
            metadata_path = self.root_dir / "artifacts" / f"{artifact_id}.json"
            if not metadata_path.exists():
                return False

            with open(metadata_path) as f:
                metadata = json.load(f)

            # Check visibility
            visibility = metadata.get("visibility", "public")
            if visibility == "public":
                return True

            # Check ownership
            owner = metadata.get("owner")
            if owner and owner == context.user_id:
                return True

            # Check shared access
            shared_with = metadata.get("shared_with", [])
            if context.user_id in shared_with:
                return True

            return False

        except Exception as e:
            raise SecurityError(f"Failed to check artifact access: {e}")

    async def _load_security_data(self) -> None:
        """Load security data from disk."""
        try:
            # Load keys
            for key_file in self.keys_dir.glob("*.key"):
                with open(key_file) as f:
                    key_data = json.load(f)
                    # Process key data...

            # Load tokens
            for token_file in self.tokens_dir.glob("*.token"):
                with open(token_file) as f:
                    token_data = json.load(f)
                    # Process token data...

        except Exception as e:
            raise SecurityError(f"Failed to load security data: {e}")

    async def _save_security_data(self) -> None:
        """Save security data to disk."""
        try:
            # Save keys
            for key_id, key_data in self._keys.items():
                key_file = self.keys_dir / f"{key_id}.key"
                with open(key_file, "w") as f:
                    json.dump(key_data, f, indent=2)

            # Save tokens
            for token_id, token_data in self._tokens.items():
                token_file = self.tokens_dir / f"{token_id}.token"
                with open(token_file, "w") as f:
                    json.dump(token_data, f, indent=2)

        except Exception as e:
            raise SecurityError(f"Failed to save security data: {e}")
