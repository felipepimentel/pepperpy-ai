"""Agent implementation module for the Pepperpy framework."""
from .autonomous import AutonomousAgent, AutonomousAgentConfig
from .interactive import InteractiveAgent, InteractiveAgentConfig
from .task_assistant import TaskAssistantAgent, TaskAssistantAgentConfig
from .workflow_agent import WorkflowAgent, WorkflowAgentConfig
__all__ = ["AutonomousAgent", "AutonomousAgentConfig", "InteractiveAgent", "InteractiveAgentConfig", "TaskAssistantAgent", "TaskAssistantAgentConfig", "WorkflowAgent", "WorkflowAgentConfig"]
