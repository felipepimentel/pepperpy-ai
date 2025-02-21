"""AutoGen adapter implementation.

This module provides the adapter implementation for the Microsoft AutoGen framework.
It allows converting Pepperpy components to their AutoGen equivalents and vice versa.
"""

from typing import Any, Dict, Optional, cast

from pepperpy.adapters.base import AdapterConfig, BaseAdapter
from pepperpy.agents.base import AgentConfig, BaseAgent
from pepperpy.core.logging import get_logger
from pepperpy.workflows.base import BaseWorkflow, WorkflowConfig

# Configure logging
logger = get_logger(__name__)


class AutoGenConfig(AdapterConfig):
    """Configuration for AutoGen adapter.

    Attributes:
        name: Adapter name
        framework_version: AutoGen version
        parameters: Additional adapter parameters
        metadata: Additional metadata
        llm_config: LLM configuration for AutoGen
        agent_config: Agent configuration for AutoGen
    """

    llm_config: Dict[str, Any] = {}
    agent_config: Dict[str, Any] = {}


class AutoGenAdapter(BaseAdapter[AutoGenConfig]):
    """AutoGen framework adapter implementation."""

    def __init__(
        self,
        name: str = "autogen",
        version: str = "0.1.0",
        config: Optional[AutoGenConfig] = None,
    ) -> None:
        """Initialize AutoGen adapter.

        Args:
            name: Adapter name
            version: Adapter version
            config: Optional AutoGen configuration
        """
        if config is None:
            config = AutoGenConfig(
                name=name,
                framework_version=version,
            )
        super().__init__(name, version, config)

    async def adapt_agent(self, agent: BaseAgent) -> Any:
        """Adapt a Pepperpy agent to an AutoGen agent.

        Args:
            agent: Pepperpy agent to adapt

        Returns:
            AutoGen agent
        """
        try:
            # Create AutoGen agent configuration
            agent_config = {
                "name": str(agent.metadata.name),
                "description": str(agent.metadata.description),
                "llm_config": cast(AutoGenConfig, self.config).llm_config,
                **cast(AutoGenConfig, self.config).agent_config,
            }

            # Create AutoGen agent
            # Note: Actual AutoGen agent creation will depend on the specific agent type
            autogen_agent = {
                "config": agent_config,
                "capabilities": await agent.get_capabilities(),
            }

            return autogen_agent

        except Exception as e:
            logger.error(f"Failed to adapt agent {agent.metadata.name}: {e}")
            raise

    async def adapt_workflow(self, workflow: BaseWorkflow) -> Any:
        """Adapt a Pepperpy workflow to an AutoGen workflow.

        Args:
            workflow: Pepperpy workflow to adapt

        Returns:
            AutoGen workflow
        """
        try:
            # Create AutoGen workflow configuration
            workflow_config = {
                "name": str(workflow.metadata.name),
                "description": str(workflow.metadata.description),
                "llm_config": cast(AutoGenConfig, self.config).llm_config,
            }

            # Create AutoGen workflow
            # Note: Actual AutoGen workflow creation will depend on the specific workflow type
            autogen_workflow = {
                "config": workflow_config,
                "capabilities": await workflow.get_capabilities(),
            }

            return autogen_workflow

        except Exception as e:
            logger.error(f"Failed to adapt workflow {workflow.metadata.name}: {e}")
            raise

    async def adapt_tool(self, tool: Any) -> Any:
        """Adapt a Pepperpy tool to an AutoGen tool.

        Args:
            tool: Pepperpy tool to adapt

        Returns:
            AutoGen tool
        """
        try:
            # Create AutoGen tool
            autogen_tool = {
                "name": str(tool.metadata.name),
                "description": str(tool.metadata.description),
                "run": tool.run,
            }

            return autogen_tool

        except Exception as e:
            logger.error(f"Failed to adapt tool {tool.metadata.name}: {e}")
            raise

    async def adapt_from_agent(self, external_agent: Any) -> BaseAgent:
        """Adapt an AutoGen agent to a Pepperpy agent.

        Args:
            external_agent: AutoGen agent to adapt

        Returns:
            Pepperpy agent
        """
        try:
            # Extract agent configuration
            agent_name = str(external_agent.get("config", {}).get("name", "unknown"))
            agent_description = str(
                external_agent.get("config", {}).get("description", "")
            )

            # Create Pepperpy agent configuration
            config = AgentConfig(
                name=agent_name,
                description=agent_description,
            )

            # Create Pepperpy agent
            agent = BaseAgent(
                name=agent_name,
                version="0.1.0",
                config=config,
            )

            return agent

        except Exception as e:
            logger.error(f"Failed to adapt from AutoGen agent: {e}")
            raise

    async def adapt_from_workflow(self, external_workflow: Any) -> BaseWorkflow:
        """Adapt an AutoGen workflow to a Pepperpy workflow.

        Args:
            external_workflow: AutoGen workflow to adapt

        Returns:
            Pepperpy workflow
        """
        try:
            # Extract workflow configuration
            workflow_name = str(
                external_workflow.get("config", {}).get("name", "unknown")
            )
            workflow_description = str(
                external_workflow.get("config", {}).get("description", "")
            )

            # Create Pepperpy workflow configuration
            config = WorkflowConfig(
                name=workflow_name,
                description=workflow_description,
            )

            # Create Pepperpy workflow
            workflow = BaseWorkflow(
                name=workflow_name,
                version="0.1.0",
                config=config,
            )

            return workflow

        except Exception as e:
            logger.error(f"Failed to adapt from AutoGen workflow: {e}")
            raise

    async def adapt_from_tool(self, external_tool: Any) -> Any:
        """Adapt an AutoGen tool to a Pepperpy tool.

        Args:
            external_tool: AutoGen tool to adapt

        Returns:
            Pepperpy tool
        """
        try:
            # Create Pepperpy tool
            tool = {
                "name": str(external_tool.get("name", "unknown")),
                "description": str(external_tool.get("description", "")),
                "run": external_tool.get("run", lambda x: x),
            }

            return tool

        except Exception as e:
            logger.error(f"Failed to adapt from AutoGen tool: {e}")
            raise

    async def _initialize(self) -> None:
        """Initialize adapter resources."""
        pass

    async def _cleanup(self) -> None:
        """Clean up adapter resources."""
        pass
