"""Agent role definitions."""

from enum import Enum


class AgentRole(str, Enum):
    """Agent role types."""

    ANALYST = "analyst"
    DEVELOPER = "developer"
    TESTER = "tester"
    RESEARCHER = "researcher"
    REVIEWER = "reviewer"
    ARCHITECT = "architect"
    MANAGER = "manager"
    QA = "qa"
    DEVOPS = "devops"
    QUALITY_ENGINEER = "quality_engineer"
