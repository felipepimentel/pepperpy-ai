"""Agent factory implementation."""

from typing import ClassVar, TypedDict

from ..base.message import MessageHandler
from .analysis import AnalysisAgent
from .architect import ArchitectAgent
from .development import DevelopmentAgent
from .project_manager import ProjectManagerAgent
from .quality import QualityEngineerAgent
from .research import ResearchAgent
from .specialized import SpecializedAgent
from .team import TeamAgent
from .types import AgentRole


class AgentKwargs(TypedDict, total=False):
    """Type hints for agent kwargs."""
    temperature: float
    max_tokens: int
    model: str


class AgentFactory:
    """Factory for creating agents."""

    _agent_types: ClassVar[dict[AgentRole, type[MessageHandler]]] = {
        AgentRole.ARCHITECT: ArchitectAgent,
        AgentRole.DEVELOPMENT: DevelopmentAgent,
        AgentRole.ANALYSIS: AnalysisAgent,
        AgentRole.PROJECT_MANAGER: ProjectManagerAgent,
        AgentRole.QA: QualityEngineerAgent,
        AgentRole.TEAM: TeamAgent,
        AgentRole.SPECIALIZED: SpecializedAgent,
        AgentRole.RESEARCH: ResearchAgent,
    }

    @classmethod
    def create_agent(cls, role: AgentRole, **kwargs: AgentKwargs) -> MessageHandler:
        """Create an agent instance.

        Args:
            role: The role of the agent to create
            **kwargs: Additional arguments to pass to the agent constructor

        Returns:
            An initialized agent instance

        Raises:
            ValueError: If the role is not supported
        """
        if role not in cls._agent_types:
            raise ValueError(f"Unsupported agent role: {role}")

        agent_class = cls._agent_types[role]
        return agent_class(**kwargs)
