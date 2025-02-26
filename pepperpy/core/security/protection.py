"""Data protection system.

This module provides data protection functionality using encryption
and key management for secure data handling.
"""

from typing import Any, Dict, TypeVar
from uuid import UUID

from pepperpy.core.errors import ValidationError
from pepperpy.core.metrics import MetricsCollector
from pepperpy.security.key_management import KeyManager
from pepperpy.security.types import ProtectionPolicy, SecurityContext

T = TypeVar("T")


class DataProtector:
    """Data protection system."""

    def __init__(
        self,
        key_manager: KeyManager,
        metrics: MetricsCollector,
    ) -> None:
        """Initialize data protector.

        Args:
            key_manager: Key management system
            metrics: Metrics collector
        """
        self.key_manager = key_manager
        self.metrics = metrics
        self.protection_policies: Dict[str, ProtectionPolicy] = {}

        # Initialize metrics
        self.protected_items_counter = self.metrics.counter(
            "security_protected_items",
            "Number of items protected",
        )
        self.protection_errors_counter = self.metrics.counter(
            "security_protection_errors",
            "Number of protection errors",
        )

    async def register_policy(self, policy: ProtectionPolicy) -> None:
        """Register a protection policy.

        Args:
            policy: Protection policy to register
        """
        self.protection_policies[policy.field_name] = policy

    async def protect_data(
        self,
        data: Dict[str, Any],
        context: SecurityContext,
    ) -> Dict[str, Any]:
        """Protect data according to policies.

        Args:
            data: Data to protect
            context: Security context

        Returns:
            Dict[str, Any]: Protected data

        Raises:
            ValidationError: If protection fails
        """
        try:
            protected_data = data.copy()

            for field_name, value in data.items():
                policy = self.protection_policies.get(field_name)
                if not policy:
                    continue

                # Check required scopes
                if not policy.required_scopes.issubset(context.active_scopes):
                    raise ValidationError(
                        f"Missing required scopes for field {field_name}"
                    )

                # Apply protection
                if policy.protection_type == "encryption":
                    if not policy.encryption_key_id:
                        key = await self.key_manager.get_active_key()
                    else:
                        key = await self.key_manager.get_key_by_id(
                            UUID(policy.encryption_key_id)
                        )

                    encrypted = await key.cipher.encrypt(
                        {"value": value},
                        {"field": field_name, "context": context.user_id},
                    )
                    protected_data[field_name] = {
                        "type": "encrypted",
                        "key_id": str(key.key_id),
                        **encrypted,
                    }

                elif policy.protection_type == "masking":
                    if not policy.masking_pattern:
                        raise ValidationError(
                            f"Missing masking pattern for field {field_name}"
                        )
                    protected_data[field_name] = self._apply_masking(
                        str(value), policy.masking_pattern
                    )

            self.protected_items_counter.inc()
            return protected_data

        except Exception as e:
            self.protection_errors_counter.inc()
            raise ValidationError(f"Data protection failed: {e}") from e

    async def unprotect_data(
        self,
        protected_data: Dict[str, Any],
        context: SecurityContext,
    ) -> Dict[str, Any]:
        """Unprotect data according to policies.

        Args:
            protected_data: Protected data
            context: Security context

        Returns:
            Dict[str, Any]: Unprotected data

        Raises:
            ValidationError: If unprotection fails
        """
        try:
            data = protected_data.copy()

            for field_name, value in protected_data.items():
                policy = self.protection_policies.get(field_name)
                if not policy:
                    continue

                # Check required scopes
                if not policy.required_scopes.issubset(context.active_scopes):
                    raise ValidationError(
                        f"Missing required scopes for field {field_name}"
                    )

                # Handle encrypted data
                if isinstance(value, dict) and value.get("type") == "encrypted":
                    key = await self.key_manager.get_key_by_id(
                        UUID(value["key_id"])
                    )
                    decrypted = await key.cipher.decrypt(value)
                    data[field_name] = decrypted["value"]

                # Handle masked data
                elif policy.protection_type == "masking":
                    # Masked data cannot be unmasked
                    continue

            return data

        except Exception as e:
            self.protection_errors_counter.inc()
            raise ValidationError(f"Data unprotection failed: {e}") from e

    def _apply_masking(self, value: str, pattern: str) -> str:
        """Apply masking pattern to value.

        Args:
            value: Value to mask
            pattern: Masking pattern (e.g. "XXX-XX-####")

        Returns:
            str: Masked value
        """
        if len(value) != len(pattern):
            raise ValidationError(
                f"Value length {len(value)} does not match pattern length {len(pattern)}"
            )

        masked = ""
        for v, p in zip(value, pattern):
            if p == "X":
                masked += "*"
            elif p == "#":
                masked += v
            else:
                masked += p

        return masked 