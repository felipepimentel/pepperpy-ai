"""Monitoring types module for the Pepperpy framework.

This module defines core monitoring types used throughout the framework.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum, auto
from typing import Any, Dict, List, Optional

from pepperpy.core.models import BaseModel, ConfigDict, Field


class MonitoringLevel(str, Enum):
    """Monitoring severity levels."""

    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AlertState(str, Enum):
    """Alert states."""

    PENDING = "pending"
    FIRING = "firing"
    RESOLVED = "resolved"
    SILENCED = "silenced"
    ACKNOWLEDGED = "acknowledged"


class AlertSeverity(str, Enum):
    """Alert severity levels."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class MonitoringEvent(BaseModel):
    """Monitoring event.

    Attributes:
        id: Event ID
        timestamp: Event timestamp
        level: Event level
        source: Event source
        message: Event message
        data: Event data
        metadata: Additional metadata
    """

    model_config = ConfigDict(
        frozen=True,
        arbitrary_types_allowed=True,
        validate_assignment=True,
        populate_by_name=True,
        str_strip_whitespace=True,
        validate_default=True,
    )

    id: str = Field(description="Event ID")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Event timestamp",
    )
    level: MonitoringLevel = Field(description="Event level")
    source: str = Field(description="Event source")
    message: str = Field(description="Event message")
    data: dict[str, Any] = Field(
        default_factory=dict,
        description="Event data",
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata",
    )


class Alert(BaseModel):
    """Alert definition.

    Attributes:
        id: Alert ID
        name: Alert name
        description: Alert description
        severity: Alert severity
        state: Alert state
        source: Alert source
        condition: Alert condition
        labels: Alert labels
        annotations: Alert annotations
        created_at: Creation timestamp
        updated_at: Last update timestamp
        resolved_at: Resolution timestamp
    """

    model_config = ConfigDict(
        frozen=True,
        arbitrary_types_allowed=True,
        validate_assignment=True,
        populate_by_name=True,
        str_strip_whitespace=True,
        validate_default=True,
    )

    id: str = Field(description="Alert ID")
    name: str = Field(description="Alert name")
    description: str = Field(description="Alert description")
    severity: AlertSeverity = Field(description="Alert severity")
    state: AlertState = Field(description="Alert state")
    source: str = Field(description="Alert source")
    condition: str = Field(description="Alert condition")
    labels: dict[str, str] = Field(
        default_factory=dict,
        description="Alert labels",
    )
    annotations: dict[str, str] = Field(
        default_factory=dict,
        description="Alert annotations",
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Creation timestamp",
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Last update timestamp",
    )
    resolved_at: datetime | None = Field(
        default=None,
        description="Resolution timestamp",
    )


class MonitoringRule(BaseModel):
    """Monitoring rule.

    Attributes:
        id: Rule ID
        name: Rule name
        description: Rule description
        condition: Rule condition
        severity: Rule severity
        labels: Rule labels
        annotations: Rule annotations
        enabled: Whether rule is enabled
    """

    model_config = ConfigDict(
        frozen=True,
        arbitrary_types_allowed=True,
        validate_assignment=True,
        populate_by_name=True,
        str_strip_whitespace=True,
        validate_default=True,
    )

    id: str = Field(description="Rule ID")
    name: str = Field(description="Rule name")
    description: str = Field(description="Rule description")
    condition: str = Field(description="Rule condition")
    severity: AlertSeverity = Field(description="Rule severity")
    labels: dict[str, str] = Field(
        default_factory=dict,
        description="Rule labels",
    )
    annotations: dict[str, str] = Field(
        default_factory=dict,
        description="Rule annotations",
    )
    enabled: bool = Field(
        default=True,
        description="Whether rule is enabled",
    )


class MonitoringMetric(BaseModel):
    """Monitoring metric.

    Attributes:
        name: Metric name
        value: Metric value
        timestamp: Metric timestamp
        labels: Metric labels
        metadata: Additional metadata
    """

    model_config = ConfigDict(
        frozen=True,
        arbitrary_types_allowed=True,
        validate_assignment=True,
        populate_by_name=True,
        str_strip_whitespace=True,
        validate_default=True,
    )

    name: str = Field(description="Metric name")
    value: float = Field(description="Metric value")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Metric timestamp",
    )
    labels: dict[str, str] = Field(
        default_factory=dict,
        description="Metric labels",
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata",
    )


# Export public API
__all__ = [
    "Alert",
    "AlertSeverity",
    "AlertState",
    "MonitoringEvent",
    "MonitoringLevel",
    "MonitoringMetric",
    "MonitoringRule",
] 