"""Audit analysis functionality for PepperPy security.

This module provides functionality for analyzing audit events, detecting patterns,
and identifying potential security issues.
"""

from typing import Any, Dict, List

from .events import AuditEvent


class AuditAnalyzer:
    """Analyzes audit events for patterns and anomalies."""

    def analyze_user_activity(
        self, events: List[AuditEvent], window_size: int = 3600
    ) -> Dict[str, Any]:
        """Analyze user activity patterns.

        Args:
            events: List of audit events to analyze
            window_size: Time window in seconds for analysis

        Returns:
            Dictionary containing user activity statistics
        """
        user_stats = {}

        for event in events:
            if not event.user_id:
                continue

            if event.user_id not in user_stats:
                user_stats[event.user_id] = {
                    "total_events": 0,
                    "event_types": {},
                    "severity_counts": {},
                    "resources_accessed": set(),
                }

            stats = user_stats[event.user_id]
            stats["total_events"] += 1
            stats["event_types"][event.event_type.value] = (
                stats["event_types"].get(event.event_type.value, 0) + 1
            )
            stats["severity_counts"][event.severity.value] = (
                stats["severity_counts"].get(event.severity.value, 0) + 1
            )
            if event.resource_id:
                stats["resources_accessed"].add(event.resource_id)

        # Convert sets to lists for JSON serialization
        for stats in user_stats.values():
            stats["resources_accessed"] = list(stats["resources_accessed"])

        return user_stats

    def detect_anomalies(
        self, events: List[AuditEvent], thresholds: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Detect anomalous patterns in audit events.

        Args:
            events: List of audit events to analyze
            thresholds: Dictionary of threshold values for anomaly detection

        Returns:
            List of detected anomalies
        """
        anomalies = []

        # Group events by user
        user_events = {}
        for event in events:
            if not event.user_id:
                continue
            if event.user_id not in user_events:
                user_events[event.user_id] = []
            user_events[event.user_id].append(event)

        # Check for anomalies
        for user_id, user_events_list in user_events.items():
            # Check event frequency
            event_count = len(user_events_list)
            if event_count > thresholds.get("max_events_per_user", 1000):
                anomalies.append({
                    "type": "high_event_frequency",
                    "user_id": user_id,
                    "count": event_count,
                    "threshold": thresholds["max_events_per_user"],
                })

            # Check severity patterns
            critical_events = [
                e for e in user_events_list if e.severity.value == "critical"
            ]
            if len(critical_events) > thresholds.get("max_critical_events", 5):
                anomalies.append({
                    "type": "high_severity_pattern",
                    "user_id": user_id,
                    "count": len(critical_events),
                    "threshold": thresholds["max_critical_events"],
                })

            # Check for rapid resource access
            if len(user_events_list) >= 2:
                sorted_events = sorted(user_events_list, key=lambda e: e.timestamp)
                for i in range(len(sorted_events) - 1):
                    time_diff = (
                        sorted_events[i + 1].timestamp - sorted_events[i].timestamp
                    ).total_seconds()
                    if time_diff < thresholds.get("min_event_interval", 1.0):
                        anomalies.append({
                            "type": "rapid_events",
                            "user_id": user_id,
                            "interval": time_diff,
                            "threshold": thresholds["min_event_interval"],
                            "events": [
                                sorted_events[i].event_type.value,
                                sorted_events[i + 1].event_type.value,
                            ],
                        })

        return anomalies
