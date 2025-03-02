"""Schema manager module.

This module provides functionality for managing and validating schemas.
"""

import logging
import time
from typing import Any, Dict, List, Optional

from .base import ValidationError, Validator

logger = logging.getLogger(__name__)


class ValidationManager:
    """Manager for validation.

    This class provides functionality for:
    - Registering validators
    - Validating data against validators
    - Validation metrics tracking
    """

    def __init__(self) -> None:
        """Initialize validation manager."""
        self._validators: Dict[str, Validator] = {}
        self._logger = logging.getLogger(__name__)

    def register_validator(
        self,
        name: str,
        validator: Validator,
    ) -> None:
        """Register a validator.

        Args:
            name: Validator name
            validator: Validator instance

        Raises:
            ValidationError: If validator registration fails
        """
        try:
            if name in self._validators:
                raise ValidationError(f"Validator already registered: {name}")

            self._validators[name] = validator
            self._logger.info(f"Registered validator: {name}")

        except Exception as e:
            self._logger.error(
                f"Validator registration failed: {e}",
                extra={"validator": name},
                exc_info=True,
            )
            raise ValidationError(f"Failed to register validator: {e}") from e

    def validate(
        self,
        name: str,
        data: Any,
    ) -> bool:
        """Validate data using a registered validator.

        Args:
            name: Validator name
            data: Data to validate

        Returns:
            True if validation succeeds, False otherwise

        Raises:
            ValidationError: If validator not found or validation fails
        """
        try:
            validator = self._validators.get(name)
            if not validator:
                raise ValidationError(f"Validator not found: {name}")

            # Record validation start time
            start_time = time.perf_counter()

            # Validate data
            result = validator.validate(data)

            return result

        except Exception as e:
            self._logger.error(
                f"Validation failed: {e}",
                extra={"validator": name, "data": data},
                exc_info=True,
            )
            raise ValidationError(f"Failed to validate data: {e}") from e

    def get_validator(self, name: str) -> Optional[Validator]:
        """Get registered validator.

        Args:
            name: Validator name

        Returns:
            Validator instance or None if not found
        """
        return self._validators.get(name)

    def get_validator_names(self) -> List[str]:
        """Get names of registered validators.

        Returns:
            List of validator names
        """
        return list(self._validators.keys())

    def clear(self) -> None:
        """Clear all registered validators."""
        self._validators.clear()
        self._logger.info("Cleared all validators")
