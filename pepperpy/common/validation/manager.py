"""Schema manager module.

This module provides functionality for managing and validating schemas.
"""

import logging
import time
from typing import Any

from pepperpy.common.errors import ValidationError
from pepperpy.monitoring.metrics import Counter, Histogram, MetricsManager
from pepperpy.validation.base import BaseSchema

logger = logging.getLogger(__name__)


class SchemaManager:
    """Manager for schema validation.

    This class provides functionality for:
    - Registering schemas
    - Validating data against schemas
    - Schema version management
    - Validation metrics tracking
    """

    def __init__(self) -> None:
        """Initialize schema manager."""
        self._schemas: dict[str, type[BaseSchema]] = {}
        self._metrics = MetricsManager.get_instance()
        self._logger = logging.getLogger(__name__)
        self._validation_counter: Counter | None = None
        self._validation_time: Histogram | None = None

    async def initialize(self) -> None:
        """Initialize schema manager."""
        try:
            # Create metrics
            self._validation_counter = await self._metrics.create_counter(
                name="schema_validations_total",
                description="Total number of schema validations",
                labels={"status": "success"},
            )
            self._validation_time = await self._metrics.create_histogram(
                name="schema_validation_seconds",
                description="Schema validation time in seconds",
                labels={"status": "success"},
                buckets=[0.001, 0.01, 0.1, 1.0],
            )
            self._logger.info("Schema manager initialized")
        except Exception as e:
            self._logger.error(f"Failed to initialize schema manager: {e}")
            raise

    def register_schema(
        self,
        name: str,
        schema: type[BaseSchema],
    ) -> None:
        """Register a schema.

        Args:
            name: Schema name
            schema: Schema class

        Raises:
            ValidationError: If schema registration fails
        """
        try:
            if name in self._schemas:
                raise ValidationError(f"Schema already registered: {name}")

            if not issubclass(schema, BaseSchema):
                raise ValidationError(
                    f"Schema must inherit from BaseSchema: {schema.__name__}"
                )

            self._schemas[name] = schema
            self._logger.info(f"Registered schema: {name}")

        except Exception as e:
            self._logger.error(
                f"Schema registration failed: {e}",
                extra={"schema": name},
                exc_info=True,
            )
            raise ValidationError(f"Failed to register schema: {e}") from e

    async def validate(
        self,
        name: str,
        data: dict[str, Any],
        version: str | None = None,
    ) -> BaseSchema:
        """Validate data against schema.

        Args:
            name: Schema name
            data: Data to validate
            version: Optional schema version

        Returns:
            Validated schema instance

        Raises:
            ValidationError: If validation fails
        """
        try:
            schema = self._schemas.get(name)
            if not schema:
                raise ValidationError(f"Schema not found: {name}")

            # Version check if specified
            if version and "version" not in data:
                data["version"] = version

            # Record validation start time
            start_time = time.perf_counter()

            # Validate data
            instance = schema.validate_json(data)

            # Record metrics
            if self._validation_counter:
                await self._validation_counter.inc()
            if self._validation_time:
                duration = time.perf_counter() - start_time
                await self._validation_time.observe(duration)

            return instance

        except Exception as e:
            # Record error metrics
            if self._validation_counter:
                await self._validation_counter.inc()

            self._logger.error(
                f"Schema validation failed: {e}",
                extra={"schema": name, "data": data},
                exc_info=True,
            )
            raise ValidationError(f"Failed to validate data: {e}") from e

    def get_schema(self, name: str) -> type[BaseSchema] | None:
        """Get registered schema.

        Args:
            name: Schema name

        Returns:
            Schema class or None if not found
        """
        return self._schemas.get(name)

    def get_schema_names(self) -> list[str]:
        """Get names of registered schemas.

        Returns:
            List of schema names
        """
        return list(self._schemas.keys())

    def get_json_schema(self, name: str) -> dict[str, Any] | None:
        """Get JSON schema for registered schema.

        Args:
            name: Schema name

        Returns:
            JSON schema or None if not found
        """
        schema = self.get_schema(name)
        return schema.get_json_schema() if schema else None

    def clear(self) -> None:
        """Clear all registered schemas."""
        self._schemas.clear()
        self._logger.info("Cleared all schemas")
