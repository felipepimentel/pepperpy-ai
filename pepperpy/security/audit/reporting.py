"""Audit reporting functionality for PepperPy security.

This module provides functionality for generating various types of audit reports
and summaries from audit events.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from .events import AuditEvent, AuditEventSeverity, AuditEventType


class AuditReport:
    """Generates audit reports."""

    @staticmethod
    def generate_summary(events: List[AuditEvent]) -> Dict[str, Any]:
        """Generate a summary report of audit events.

        Args:
            events: List of audit events to summarize

        Returns:
            Dictionary containing the summary report
        """
        if not events:
            return {}

        summary = {
            "total_events": len(events),
            "time_range": {
                "start": min(e.timestamp for e in events).isoformat(),
                "end": max(e.timestamp for e in events).isoformat(),
            },
            "event_types": {},
            "severity_distribution": {
                "info": 0,
                "warning": 0,
                "error": 0,
                "critical": 0,
            },
            "users": set(),
            "resources": set(),
            "critical_events": [],
        }

        for event in events:
            # Count event types
            event_type = event.event_type.value
            summary["event_types"][event_type] = (
                summary["event_types"].get(event_type, 0) + 1
            )

            # Track severity distribution
            summary["severity_distribution"][event.severity.value] += 1

            # Track critical events
            if event.severity == AuditEventSeverity.CRITICAL:
                summary["critical_events"].append({
                    "event_type": event_type,
                    "timestamp": event.timestamp.isoformat(),
                    "user_id": event.user_id,
                    "resource_id": event.resource_id,
                    "action": event.action,
                    "status": event.status,
                    "details": event.details,
                })

            # Track unique users and resources
            if event.user_id:
                summary["users"].add(event.user_id)
            if event.resource_id:
                summary["resources"].add(event.resource_id)

        # Convert sets to lists for JSON serialization
        summary["users"] = list(summary["users"])
        summary["resources"] = list(summary["resources"])

        return summary

    @staticmethod
    def generate_compliance_report(events: List[AuditEvent]) -> Dict[str, Any]:
        """Generate a compliance-focused report.

        Args:
            events: List of audit events to analyze

        Returns:
            Dictionary containing the compliance report
        """
        report = {
            "authentication_events": [],
            "authorization_events": [],
            "data_access_events": [],
            "system_changes": [],
            "security_alerts": [],
        }

        for event in events:
            event_data = {
                "timestamp": event.timestamp.isoformat(),
                "user_id": event.user_id,
                "resource_id": event.resource_id,
                "action": event.action,
                "status": event.status,
                "severity": event.severity.value,
                "details": event.details,
            }

            if event.event_type == AuditEventType.AUTHENTICATION:
                report["authentication_events"].append(event_data)
            elif event.event_type == AuditEventType.AUTHORIZATION:
                report["authorization_events"].append(event_data)
            elif event.event_type == AuditEventType.DATA_ACCESS:
                report["data_access_events"].append(event_data)
            elif event.event_type == AuditEventType.SYSTEM_CHANGE:
                report["system_changes"].append(event_data)
            elif event.event_type == AuditEventType.SECURITY_ALERT:
                report["security_alerts"].append(event_data)

        return report

    @staticmethod
    def generate_user_report(
        events: List[AuditEvent], user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate a user activity report.

        Args:
            events: List of audit events to analyze
            user_id: Optional user ID to filter events

        Returns:
            Dictionary containing the user activity report
        """
        if user_id:
            events = [e for e in events if e.user_id == user_id]

        report = {
            "total_events": len(events),
            "users": {},
        }

        for event in events:
            if not event.user_id:
                continue

            if event.user_id not in report["users"]:
                report["users"][event.user_id] = {
                    "event_count": 0,
                    "event_types": {},
                    "severity_counts": {},
                    "resources_accessed": set(),
                    "latest_activity": None,
                }

            user_stats = report["users"][event.user_id]
            user_stats["event_count"] += 1
            user_stats["event_types"][event.event_type.value] = (
                user_stats["event_types"].get(event.event_type.value, 0) + 1
            )
            user_stats["severity_counts"][event.severity.value] = (
                user_stats["severity_counts"].get(event.severity.value, 0) + 1
            )
            if event.resource_id:
                user_stats["resources_accessed"].add(event.resource_id)
            if not user_stats[
                "latest_activity"
            ] or event.timestamp > datetime.fromisoformat(
                user_stats["latest_activity"]
            ):
                user_stats["latest_activity"] = event.timestamp.isoformat()

        # Convert sets to lists for JSON serialization
        for user_stats in report["users"].values():
            user_stats["resources_accessed"] = list(user_stats["resources_accessed"])

        return report
