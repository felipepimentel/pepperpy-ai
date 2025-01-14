"""Crew team provider module."""

from collections.abc import Sequence
from typing import Any, cast

from langchain.agents import AgentExecutor
from langchain.agents.agent_toolkits import create_conversational_retrieval_agent
from langchain.agents.openai_functions_agent.base import OpenAIFunctionsAgent
from langchain.chat_models import ChatOpenAI
from langchain.memory import ConversationBufferMemory
from langchain.schema.language_model import BaseLanguageModel
from langchain.schema.messages import SystemMessage
from langchain.schema.retriever import BaseRetriever
from langchain.tools.base import BaseTool

from pepperpy.responses import ResponseData, ResponseMetadata
from pepperpy.teams.config import TeamConfig
from pepperpy.teams.providers.base import BaseTeamProvider
from pepperpy.types.params import ToolParams


class CrewTeamProvider(BaseTeamProvider):
    """Crew team provider."""

    def __init__(
        self,
        config: TeamConfig,
        llm: BaseLanguageModel | None = None,
        tools: Sequence[BaseTool] | None = None,
        retriever: BaseRetriever | None = None,
        memory: ConversationBufferMemory | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize crew team provider.

        Args:
            config: Team configuration.
            llm: Language model.
            tools: List of tools.
            retriever: Retriever.
            memory: Memory.
            **kwargs: Additional arguments.
        """
        super().__init__()
        self._config = config
        self._llm = llm or ChatOpenAI(temperature=0)
        self._tools = tools or []
        self._retriever = retriever
        self._memory = memory or ConversationBufferMemory(
            memory_key="chat_history", return_messages=True
        )
        self._kwargs = kwargs
        self._agent: AgentExecutor | None = None

    @property
    def config(self) -> TeamConfig:
        """Get provider configuration.

        Returns:
            TeamConfig: Provider configuration.
        """
        return self._config

    async def execute_task(self, task: str, **kwargs: ToolParams) -> ResponseData:
        """Execute team task.

        Args:
            task: Task to execute.
            **kwargs: Additional arguments.

        Returns:
            ResponseData: Task execution result.

        Raises:
            RuntimeError: If agent initialization fails.
        """
        if not self._agent:
            if self._retriever:
                self._agent = create_conversational_retrieval_agent(
                    llm=self._llm,
                    tools=self._tools,
                    retriever=self._retriever,
                    memory=self._memory,
                    **self._kwargs,
                )
            else:
                self._agent = AgentExecutor.from_agent_and_tools(
                    agent=cast(OpenAIFunctionsAgent, self._llm),
                    tools=self._tools,
                    memory=self._memory,
                    **self._kwargs,
                )

        if not self._agent:
            raise RuntimeError("Failed to initialize agent")

        result = await self._agent.arun(task)
        return ResponseData(
            content=str(result),
            metadata=ResponseMetadata(provider=self.config.provider),
        )
