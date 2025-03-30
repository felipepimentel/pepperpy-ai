"""AutoGen provider implementation for the agents module."""

from typing import Dict, List, Optional, Any, cast

from pepperpy.agents.base import Agent, AgentGroup, Memory, Message
from pepperpy.llm.base import LLMProvider


class AutoGenAgent(Agent):
    """AutoGen implementation of an agent."""

    def __init__(self, llm_provider: LLMProvider, memory: Optional[Memory] = None):
        """Initialize the AutoGen agent.
        
        Args:
            llm_provider: The LLM provider to use.
            memory: Optional memory implementation.
        """
        self.llm_provider = llm_provider
        self.memory = memory

    async def initialize(self) -> None:
        """Initialize the agent."""
        # No initialization needed for basic agent
        pass

    async def execute_task(self, task: str) -> List[Message]:
        """Execute a task and return the messages.
        
        Args:
            task: The task to execute.
            
        Returns:
            List of messages from the execution.
        """
        # Basic implementation using single agent
        response = await self.llm_provider.generate(task)
        message = Message(role="assistant", content=str(response))
        
        if self.memory:
            await self.memory.add_message(message)
            
        return [message]


class AutoGenGroup(AgentGroup):
    """AutoGen implementation of an agent group."""

    def __init__(self, 
                 llm_provider: LLMProvider,
                 group_config: Dict[str, Any],
                 memory: Optional[Memory] = None):
        """Initialize the AutoGen agent group.
        
        Args:
            llm_provider: The LLM provider to use.
            group_config: Configuration for the agent group.
            memory: Optional memory implementation.
        """
        self.llm_provider = llm_provider
        self.config = group_config
        self.memory = memory
        self.agents: List[AutoGenAgent] = []

    async def initialize(self) -> None:
        """Initialize the agent group."""
        # Create agents based on config
        for agent_config in self.config.get("agents", []):
            agent = AutoGenAgent(
                llm_provider=self.llm_provider,
                memory=self.memory
            )
            await agent.initialize()
            self.agents.append(agent)

    async def execute_task(self, task: str) -> List[Message]:
        """Execute a task using the agent group.
        
        Args:
            task: The task to execute.
            
        Returns:
            List of messages from the execution.
        """
        messages: List[Message] = []
        
        # Basic round-robin execution
        for agent in self.agents:
            agent_messages = await agent.execute_task(task)
            messages.extend(agent_messages)
            
            if self.memory:
                for message in agent_messages:
                    await self.memory.add_message(message)
        
        return messages
