"""Standard event types for the Pepperpy framework."""

# System Events
SYSTEM_STARTED = "system.started"
SYSTEM_STOPPED = "system.stopped"
SYSTEM_ERROR = "system.error"
SYSTEM_CONFIG_CHANGED = "system.config.changed"

# Agent Events
AGENT_CREATED = "agent.created"
AGENT_UPDATED = "agent.updated"
AGENT_DELETED = "agent.deleted"
AGENT_STARTED = "agent.started"
AGENT_STOPPED = "agent.stopped"
AGENT_ERROR = "agent.error"
AGENT_MESSAGE_RECEIVED = "agent.message.received"
AGENT_MESSAGE_SENT = "agent.message.sent"

# Workflow Events
WORKFLOW_CREATED = "workflow.created"
WORKFLOW_UPDATED = "workflow.updated"
WORKFLOW_DELETED = "workflow.deleted"
WORKFLOW_STARTED = "workflow.started"
WORKFLOW_COMPLETED = "workflow.completed"
WORKFLOW_FAILED = "workflow.failed"
WORKFLOW_STEP_STARTED = "workflow.step.started"
WORKFLOW_STEP_COMPLETED = "workflow.step.completed"
WORKFLOW_STEP_FAILED = "workflow.step.failed"

# Resource Events
RESOURCE_CREATED = "resource.created"
RESOURCE_UPDATED = "resource.updated"
RESOURCE_DELETED = "resource.deleted"
RESOURCE_ACCESSED = "resource.accessed"
RESOURCE_ERROR = "resource.error"

# Security Events
SECURITY_AUTH_SUCCESS = "security.auth.success"
SECURITY_AUTH_FAILED = "security.auth.failed"
SECURITY_ACCESS_DENIED = "security.access.denied"
SECURITY_PERMISSION_CHANGED = "security.permission.changed"
SECURITY_ROLE_CHANGED = "security.role.changed"

# Monitoring Events
MONITORING_METRIC_RECORDED = "monitoring.metric.recorded"
MONITORING_ALERT_TRIGGERED = "monitoring.alert.triggered"
MONITORING_ALERT_RESOLVED = "monitoring.alert.resolved"
MONITORING_THRESHOLD_EXCEEDED = "monitoring.threshold.exceeded"

# Memory Events
MEMORY_ENTRY_CREATED = "memory.entry.created"
MEMORY_ENTRY_UPDATED = "memory.entry.updated"
MEMORY_ENTRY_DELETED = "memory.entry.deleted"
MEMORY_QUERY_EXECUTED = "memory.query.executed"
MEMORY_ERROR = "memory.error"

# Plugin Events
PLUGIN_LOADED = "plugin.loaded"
PLUGIN_UNLOADED = "plugin.unloaded"
PLUGIN_ERROR = "plugin.error"
PLUGIN_CONFIG_CHANGED = "plugin.config.changed"

# User Events
USER_CREATED = "user.created"
USER_UPDATED = "user.updated"
USER_DELETED = "user.deleted"
USER_LOGIN = "user.login"
USER_LOGOUT = "user.logout"
USER_ACTION = "user.action"

# Error Events
ERROR_VALIDATION = "error.validation"
ERROR_PROCESSING = "error.processing"
ERROR_SYSTEM = "error.system"
ERROR_NETWORK = "error.network"
ERROR_DATABASE = "error.database"

# All event types
EVENT_TYPES = [
    # System Events
    SYSTEM_STARTED,
    SYSTEM_STOPPED,
    SYSTEM_ERROR,
    SYSTEM_CONFIG_CHANGED,
    
    # Agent Events
    AGENT_CREATED,
    AGENT_UPDATED,
    AGENT_DELETED,
    AGENT_STARTED,
    AGENT_STOPPED,
    AGENT_ERROR,
    AGENT_MESSAGE_RECEIVED,
    AGENT_MESSAGE_SENT,
    
    # Workflow Events
    WORKFLOW_CREATED,
    WORKFLOW_UPDATED,
    WORKFLOW_DELETED,
    WORKFLOW_STARTED,
    WORKFLOW_COMPLETED,
    WORKFLOW_FAILED,
    WORKFLOW_STEP_STARTED,
    WORKFLOW_STEP_COMPLETED,
    WORKFLOW_STEP_FAILED,
    
    # Resource Events
    RESOURCE_CREATED,
    RESOURCE_UPDATED,
    RESOURCE_DELETED,
    RESOURCE_ACCESSED,
    RESOURCE_ERROR,
    
    # Security Events
    SECURITY_AUTH_SUCCESS,
    SECURITY_AUTH_FAILED,
    SECURITY_ACCESS_DENIED,
    SECURITY_PERMISSION_CHANGED,
    SECURITY_ROLE_CHANGED,
    
    # Monitoring Events
    MONITORING_METRIC_RECORDED,
    MONITORING_ALERT_TRIGGERED,
    MONITORING_ALERT_RESOLVED,
    MONITORING_THRESHOLD_EXCEEDED,
    
    # Memory Events
    MEMORY_ENTRY_CREATED,
    MEMORY_ENTRY_UPDATED,
    MEMORY_ENTRY_DELETED,
    MEMORY_QUERY_EXECUTED,
    MEMORY_ERROR,
    
    # Plugin Events
    PLUGIN_LOADED,
    PLUGIN_UNLOADED,
    PLUGIN_ERROR,
    PLUGIN_CONFIG_CHANGED,
    
    # User Events
    USER_CREATED,
    USER_UPDATED,
    USER_DELETED,
    USER_LOGIN,
    USER_LOGOUT,
    USER_ACTION,
    
    # Error Events
    ERROR_VALIDATION,
    ERROR_PROCESSING,
    ERROR_SYSTEM,
    ERROR_NETWORK,
    ERROR_DATABASE,
] 