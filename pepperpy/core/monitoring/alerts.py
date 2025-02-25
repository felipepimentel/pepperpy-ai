"""Alert management functionality for monitoring.

This module provides alert management functionality.
"""

from datetime import datetime

from pepperpy.core.lifecycle import LifecycleComponent
from pepperpy.core.monitoring.errors import AlertError
from pepperpy.core.monitoring.types import (
    Alert,
    AlertSeverity,
    AlertState,
    MonitoringRule,
)


class AlertManager(LifecycleComponent):
    """Manager for handling alerts."""

    def __init__(self, name: str = "alert_manager") -> None:
        """Initialize alert manager.

        Args:
            name: Manager name
        """
        super().__init__(name)
        self._alerts: dict[str, Alert] = {}
        self._rules: dict[str, MonitoringRule] = {}

    async def initialize(self) -> None:
        """Initialize alert manager.

        Raises:
            AlertError: If initialization fails
        """
        try:
            await self._initialize()
        except Exception as e:
            raise AlertError(f"Failed to initialize alert manager: {e}")

    async def cleanup(self) -> None:
        """Clean up alert manager.

        Raises:
            AlertError: If cleanup fails
        """
        try:
            await self._cleanup()
        except Exception as e:
            raise AlertError(f"Failed to clean up alert manager: {e}")

    async def _initialize(self) -> None:
        """Initialize alert manager implementation."""
        pass

    async def _cleanup(self) -> None:
        """Clean up alert manager implementation."""
        pass

    async def add_rule(self, rule: MonitoringRule) -> None:
        """Add monitoring rule.

        Args:
            rule: Rule to add

        Raises:
            AlertError: If rule already exists
        """
        if rule.id in self._rules:
            raise AlertError(f"Rule already exists: {rule.id}")
        self._rules[rule.id] = rule

    async def remove_rule(self, rule_id: str) -> None:
        """Remove monitoring rule.

        Args:
            rule_id: ID of rule to remove

        Raises:
            AlertError: If rule not found
        """
        if rule_id not in self._rules:
            raise AlertError(f"Rule not found: {rule_id}")
        del self._rules[rule_id]

    async def get_alerts(
        self,
        severity: AlertSeverity | None = None,
        state: AlertState | None = None,
        source: str | None = None,
    ) -> list[Alert]:
        """Get alerts matching criteria.

        Args:
            severity: Optional severity filter
            state: Optional state filter
            source: Optional source filter

        Returns:
            list[Alert]: Matching alerts
        """
        alerts = list(self._alerts.values())

        if severity:
            alerts = [a for a in alerts if a.severity == severity]
        if state:
            alerts = [a for a in alerts if a.state == state]
        if source:
            alerts = [a for a in alerts if a.source == source]

        return alerts

    async def update_alert(
        self,
        alert_id: str,
        state: AlertState | None = None,
        annotations: dict[str, str] | None = None,
    ) -> None:
        """Update alert.

        Args:
            alert_id: Alert ID
            state: Optional new state
            annotations: Optional annotations to update

        Raises:
            AlertError: If alert not found
        """
        if alert_id not in self._alerts:
            raise AlertError(f"Alert not found: {alert_id}")

        alert = self._alerts[alert_id]
        if state:
            alert.state = state
        if annotations:
            alert.annotations.update(annotations)
        alert.updated_at = datetime.utcnow()


__all__ = ["AlertManager"]
