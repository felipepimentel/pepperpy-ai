"""LangChain adapter implementation.

This module provides the adapter implementation for the LangChain framework.
It allows converting Pepperpy components to their LangChain equivalents and vice versa.
"""

from typing import Any, Dict, Optional, cast

from langchain.agents import AgentExecutor, Tool
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate

from pepperpy.adapters.base import AdapterConfig, BaseAdapter
from pepperpy.agents.base import AgentConfig, BaseAgent
from pepperpy.core.logging import get_logger
from pepperpy.workflows.base import BaseWorkflow, WorkflowConfig

# Configure logging
logger = get_logger(__name__)


class LangChainConfig(AdapterConfig):
    """Configuration for LangChain adapter.

    Attributes:
        name: Adapter name
        framework_version: LangChain version
        parameters: Additional adapter parameters
        metadata: Additional metadata
        llm_config: LLM configuration for LangChain
        agent_config: Agent configuration for LangChain
    """

    llm_config: Dict[str, Any] = {}
    agent_config: Dict[str, Any] = {}


class LangChainAdapter(BaseAdapter[LangChainConfig]):
    """LangChain framework adapter implementation."""

    def __init__(
        self,
        name: str = "langchain",
        version: str = "0.1.0",
        config: Optional[LangChainConfig] = None,
    ) -> None:
        """Initialize LangChain adapter.

        Args:
            name: Adapter name
            version: Adapter version
            config: Optional LangChain configuration
        """
        if config is None:
            config = LangChainConfig(
                name=name,
                framework_version=version,
            )
        super().__init__(name, version, config)

    async def adapt_agent(self, agent: BaseAgent) -> AgentExecutor:
        """Adapt a Pepperpy agent to a LangChain agent.

        Args:
            agent: Pepperpy agent to adapt

        Returns:
            LangChain AgentExecutor
        """
        try:
            # Create LangChain tools from agent capabilities
            tools = []
            for capability in await agent.get_capabilities():
                tool = Tool(
                    name=capability,
                    func=lambda x: x,  # Placeholder
                    description=f"Tool for {capability}",
                )
                tools.append(tool)

            # Create LangChain agent
            llm_chain = LLMChain(
                llm=cast(LangChainConfig, self.config).llm_config.get("llm"),
                prompt=PromptTemplate(
                    template=str(agent.metadata.description),
                    input_variables=["input"],
                ),
            )

            # Create agent executor
            agent_executor = AgentExecutor.from_agent_and_tools(
                agent=llm_chain,
                tools=tools,
                **cast(LangChainConfig, self.config).agent_config,
            )

            return agent_executor

        except Exception as e:
            logger.error(f"Failed to adapt agent {agent.metadata.name}: {e}")
            raise

    async def adapt_workflow(self, workflow: BaseWorkflow) -> LLMChain:
        """Adapt a Pepperpy workflow to a LangChain chain.

        Args:
            workflow: Pepperpy workflow to adapt

        Returns:
            LangChain LLMChain
        """
        try:
            # Create LangChain chain from workflow
            chain = LLMChain(
                llm=cast(LangChainConfig, self.config).llm_config.get("llm"),
                prompt=PromptTemplate(
                    template=str(workflow.metadata.description),
                    input_variables=["input"],
                ),
            )

            return chain

        except Exception as e:
            logger.error(f"Failed to adapt workflow {workflow.metadata.name}: {e}")
            raise

    async def adapt_tool(self, tool: Any) -> Tool:
        """Adapt a Pepperpy tool to a LangChain tool.

        Args:
            tool: Pepperpy tool to adapt

        Returns:
            LangChain Tool
        """
        try:
            # Create LangChain tool
            langchain_tool = Tool(
                name=str(tool.metadata.name),
                func=tool.run,
                description=str(tool.metadata.description),
            )

            return langchain_tool

        except Exception as e:
            logger.error(f"Failed to adapt tool {tool.metadata.name}: {e}")
            raise

    async def adapt_from_agent(self, external_agent: AgentExecutor) -> BaseAgent:
        """Adapt a LangChain agent to a Pepperpy agent.

        Args:
            external_agent: LangChain agent to adapt

        Returns:
            Pepperpy agent
        """
        try:
            # Create Pepperpy agent from LangChain agent
            agent_name = getattr(external_agent.agent, "name", "unknown")
            config = AgentConfig(name=str(agent_name))

            agent = BaseAgent(
                name=str(agent_name),
                version="0.1.0",
                config=config,
            )

            return agent

        except Exception as e:
            logger.error(f"Failed to adapt from LangChain agent: {e}")
            raise

    async def adapt_from_workflow(self, external_workflow: LLMChain) -> BaseWorkflow:
        """Adapt a LangChain chain to a Pepperpy workflow.

        Args:
            external_workflow: LangChain chain to adapt

        Returns:
            Pepperpy workflow
        """
        try:
            # Create Pepperpy workflow from LangChain chain
            workflow_name = getattr(external_workflow, "name", "unknown")
            config = WorkflowConfig(name=str(workflow_name))

            workflow = BaseWorkflow(
                name=str(workflow_name),
                version="0.1.0",
                config=config,
            )

            return workflow

        except Exception as e:
            logger.error(f"Failed to adapt from LangChain workflow: {e}")
            raise

    async def adapt_from_tool(self, external_tool: Tool) -> Any:
        """Adapt a LangChain tool to a Pepperpy tool.

        Args:
            external_tool: LangChain tool to adapt

        Returns:
            Pepperpy tool
        """
        try:
            # Create Pepperpy tool from LangChain tool
            tool = {
                "name": str(external_tool.name),
                "description": str(external_tool.description),
                "run": external_tool.func,
            }

            return tool

        except Exception as e:
            logger.error(f"Failed to adapt from LangChain tool: {e}")
            raise
