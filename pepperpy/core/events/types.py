"""Event types for the Pepperpy framework.

This module defines the event types used throughout the framework.
"""

from enum import Enum, auto


class EventType(Enum):
    """Event types for the framework."""

    # System events
    SYSTEM_STARTED = auto()
    SYSTEM_STOPPED = auto()

    # Provider events
    PROVIDER_REGISTERED = auto()
    PROVIDER_UNREGISTERED = auto()
    PROVIDER_UPDATED = auto()

    # Agent events
    AGENT_STARTED = auto()
    AGENT_STOPPED = auto()
    AGENT_ERROR = auto()

    # Capability events
    CAPABILITY_ADDED = auto()
    CAPABILITY_REMOVED = auto()
    CAPABILITY_UPDATED = auto()

    # Resource events
    RESOURCE_CREATED = auto()
    RESOURCE_DELETED = auto()
    RESOURCE_UPDATED = auto()

    # Security events
    SECURITY_VIOLATION = auto()
    AUTHENTICATION_FAILED = auto()
    AUTHORIZATION_FAILED = auto()

    # Monitoring events
    METRIC_RECORDED = auto()
    LOG_EMITTED = auto()
    TRACE_RECORDED = auto()


__all__ = ["EventType"]
