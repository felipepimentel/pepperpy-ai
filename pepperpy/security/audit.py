"""Module for auditing LLM interactions and security events."""
from typing import List, Optional, Dict, Any, Union
from dataclasses import dataclass
from enum import Enum
from datetime import datetime
import json
import asyncio


class AuditEventType(Enum):
    """Types of audit events."""
    PROMPT_SUBMISSION = "prompt_submission"
    MODEL_RESPONSE = "model_response"
    CONTENT_FILTER = "content_filter"
    INJECTION_ATTEMPT = "injection_attempt"
    POLICY_VIOLATION = "policy_violation"
    ACCESS_CONTROL = "access_control"
    ERROR = "error"


@dataclass
class AuditEvent:
    """Represents an auditable event."""
    id: str
    type: AuditEventType
    timestamp: datetime
    user_id: str
    details: Dict[str, Any]
    severity: int  # 1-10
    metadata: Optional[dict] = None


class AuditLogger:
    """Logs audit events."""
    
    def __init__(self):
        self.events: List[AuditEvent] = []
        self._lock = asyncio.Lock()

    async def log_event(self, event: AuditEvent):
        """Log an audit event."""
        async with self._lock:
            self.events.append(event)

    def get_events(self,
                  event_type: Optional[AuditEventType] = None,
                  start_time: Optional[datetime] = None,
                  end_time: Optional[datetime] = None,
                  min_severity: Optional[int] = None) -> List[AuditEvent]:
        """Get filtered audit events."""
        filtered = self.events
        
        if event_type:
            filtered = [e for e in filtered if e.type == event_type]
        
        if start_time:
            filtered = [e for e in filtered if e.timestamp >= start_time]
        
        if end_time:
            filtered = [e for e in filtered if e.timestamp <= end_time]
        
        if min_severity is not None:
            filtered = [e for e in filtered if e.severity >= min_severity]
        
        return filtered


class AuditAnalyzer:
    """Analyzes audit events for patterns and anomalies."""
    
    def analyze_user_activity(self,
                            events: List[AuditEvent],
                            window_size: int = 3600) -> Dict[str, Any]:
        """Analyze user activity patterns."""
        user_stats = {}
        
        for event in events:
            if event.user_id not in user_stats:
                user_stats[event.user_id] = {
                    'total_events': 0,
                    'event_types': {},
                    'avg_severity': 0,
                    'high_severity_count': 0
                }
            
            stats = user_stats[event.user_id]
            stats['total_events'] += 1
            stats['event_types'][event.type.value] = stats['event_types'].get(event.type.value, 0) + 1
            stats['avg_severity'] = (
                (stats['avg_severity'] * (stats['total_events'] - 1) + event.severity)
                / stats['total_events']
            )
            if event.severity >= 8:
                stats['high_severity_count'] += 1
        
        return user_stats

    def detect_anomalies(self,
                        events: List[AuditEvent],
                        thresholds: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Detect anomalous patterns in audit events."""
        anomalies = []
        
        # Group events by user
        user_events = {}
        for event in events:
            if event.user_id not in user_events:
                user_events[event.user_id] = []
            user_events[event.user_id].append(event)
        
        # Check for anomalies
        for user_id, user_events_list in user_events.items():
            # Check event frequency
            event_count = len(user_events_list)
            if event_count > thresholds.get('max_events_per_user', 1000):
                anomalies.append({
                    'type': 'high_event_frequency',
                    'user_id': user_id,
                    'count': event_count,
                    'threshold': thresholds['max_events_per_user']
                })
            
            # Check severity patterns
            high_severity = [e for e in user_events_list if e.severity >= 8]
            if len(high_severity) > thresholds.get('max_high_severity_events', 10):
                anomalies.append({
                    'type': 'high_severity_pattern',
                    'user_id': user_id,
                    'count': len(high_severity),
                    'threshold': thresholds['max_high_severity_events']
                })
        
        return anomalies


class AuditReport:
    """Generates audit reports."""
    
    @staticmethod
    def generate_summary(events: List[AuditEvent]) -> Dict[str, Any]:
        """Generate a summary report of audit events."""
        if not events:
            return {}
        
        summary = {
            'total_events': len(events),
            'time_range': {
                'start': min(e.timestamp for e in events).isoformat(),
                'end': max(e.timestamp for e in events).isoformat()
            },
            'event_types': {},
            'severity_distribution': {
                'low': 0,    # 1-3
                'medium': 0, # 4-7
                'high': 0    # 8-10
            },
            'users': set(),
            'high_severity_events': []
        }
        
        for event in events:
            # Count event types
            event_type = event.type.value
            summary['event_types'][event_type] = summary['event_types'].get(event_type, 0) + 1
            
            # Track severity distribution
            if event.severity <= 3:
                summary['severity_distribution']['low'] += 1
            elif event.severity <= 7:
                summary['severity_distribution']['medium'] += 1
            else:
                summary['severity_distribution']['high'] += 1
                summary['high_severity_events'].append({
                    'id': event.id,
                    'type': event_type,
                    'timestamp': event.timestamp.isoformat(),
                    'user_id': event.user_id,
                    'severity': event.severity,
                    'details': event.details
                })
            
            # Track unique users
            summary['users'].add(event.user_id)
        
        summary['unique_users'] = len(summary['users'])
        summary['users'] = list(summary['users'])  # Convert set to list for JSON serialization
        
        return summary

    @staticmethod
    def generate_compliance_report(events: List[AuditEvent]) -> Dict[str, Any]:
        """Generate a compliance-focused report."""
        report = {
            'policy_violations': [],
            'injection_attempts': [],
            'content_filter_triggers': [],
            'access_control_events': []
        }
        
        for event in events:
            event_data = {
                'id': event.id,
                'timestamp': event.timestamp.isoformat(),
                'user_id': event.user_id,
                'severity': event.severity,
                'details': event.details
            }
            
            if event.type == AuditEventType.POLICY_VIOLATION:
                report['policy_violations'].append(event_data)
            elif event.type == AuditEventType.INJECTION_ATTEMPT:
                report['injection_attempts'].append(event_data)
            elif event.type == AuditEventType.CONTENT_FILTER:
                report['content_filter_triggers'].append(event_data)
            elif event.type == AuditEventType.ACCESS_CONTROL:
                report['access_control_events'].append(event_data)
        
        return report


class AuditManager:
    """High-level interface for audit management."""
    
    def __init__(self):
        self.logger = AuditLogger()
        self.analyzer = AuditAnalyzer()

    async def log_prompt_submission(self,
                                  user_id: str,
                                  prompt: str,
                                  metadata: Optional[dict] = None):
        """Log a prompt submission event."""
        event = AuditEvent(
            id=f"prompt_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            type=AuditEventType.PROMPT_SUBMISSION,
            timestamp=datetime.now(),
            user_id=user_id,
            details={'prompt': prompt},
            severity=3,  # Default severity for prompt submissions
            metadata=metadata
        )
        await self.logger.log_event(event)

    async def log_model_response(self,
                               user_id: str,
                               prompt_id: str,
                               response: str,
                               metadata: Optional[dict] = None):
        """Log a model response event."""
        event = AuditEvent(
            id=f"resp_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            type=AuditEventType.MODEL_RESPONSE,
            timestamp=datetime.now(),
            user_id=user_id,
            details={
                'prompt_id': prompt_id,
                'response': response
            },
            severity=3,  # Default severity for model responses
            metadata=metadata
        )
        await self.logger.log_event(event)

    async def log_security_event(self,
                               event_type: AuditEventType,
                               user_id: str,
                               details: Dict[str, Any],
                               severity: int,
                               metadata: Optional[dict] = None):
        """Log a security-related event."""
        event = AuditEvent(
            id=f"sec_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            type=event_type,
            timestamp=datetime.now(),
            user_id=user_id,
            details=details,
            severity=severity,
            metadata=metadata
        )
        await self.logger.log_event(event)

    def generate_report(self,
                       start_time: Optional[datetime] = None,
                       end_time: Optional[datetime] = None,
                       report_type: str = 'summary') -> Dict[str, Any]:
        """Generate an audit report."""
        events = self.logger.get_events(start_time=start_time, end_time=end_time)
        
        if report_type == 'summary':
            return AuditReport.generate_summary(events)
        elif report_type == 'compliance':
            return AuditReport.generate_compliance_report(events)
        else:
            raise ValueError(f"Unsupported report type: {report_type}")

    def analyze_activity(self,
                        start_time: Optional[datetime] = None,
                        end_time: Optional[datetime] = None) -> Dict[str, Any]:
        """Analyze audit activity for patterns and anomalies."""
        events = self.logger.get_events(start_time=start_time, end_time=end_time)
        
        user_activity = self.analyzer.analyze_user_activity(events)
        anomalies = self.analyzer.detect_anomalies(events, {
            'max_events_per_user': 1000,
            'max_high_severity_events': 10
        })
        
        return {
            'user_activity': user_activity,
            'anomalies': anomalies
        } 