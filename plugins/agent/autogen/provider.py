"""AutoGen provider implementation for the agents module."""

from typing import Any

from pepperpy.agents.base import Agent, AgentGroup, Message
from pepperpy.plugin.provider import BasePluginProvider


class AutoGenAgent(Agent, BasePluginProvider):
    """AutoGen implementation of an agent."""

    async def initialize(self) -> None:
        """Initialize the agent."""
        # Call the base class implementation first
        await super().initialize()

        # Additional initialization can be added here if needed
        self.logger.debug(
            f"Initialized with model={self.config.get('model', 'default')}"
        )

    async def execute(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """Execute a task based on input data.

        Args:
            input_data: Input data containing task and parameters

        Returns:
            Task execution result
        """
        # Get task type from input
        task_type = input_data.get("task")

        if not task_type:
            return {"status": "error", "error": "No task specified"}

        try:
            # Handle different task types
            if task_type == "chat":
                # Handle chat task with message history
                messages = input_data.get("messages", [])
                if not messages:
                    # Add system message if not present
                    system_prompt = self.config.get(
                        "system_prompt", "You are a helpful assistant."
                    )
                    messages.append({"role": "system", "content": system_prompt})

                    # Add user message from task if available
                    if "content" in input_data:
                        messages.append(
                            {"role": "user", "content": input_data["content"]}
                        )

                # Get the last user message to process
                last_user_message = None
                for msg in reversed(messages):
                    if msg.get("role") == "user":
                        last_user_message = msg.get("content")
                        break

                if not last_user_message:
                    return {"status": "error", "error": "No user message found"}

                # Process the message
                result = await self.execute_task(last_user_message)
                response = result[0].content if result else "No response generated"

                return {
                    "status": "success",
                    "response": response,
                    "messages": messages + [{"role": "assistant", "content": response}],
                }
            else:
                # Treat task as a direct query/prompt
                result = await self.execute_task(task_type)
                response = result[0].content if result else "No response generated"

                return {"status": "success", "content": response}

        except Exception as e:
            self.logger.error(f"Error executing task '{task_type}': {e}")
            return {"status": "error", "error": str(e)}

    async def execute_task(self, task: str) -> list[Message]:
        """Execute a task and return the messages.

        Args:
            task: The task to execute.

        Returns:
            List of messages from the execution.
        """
        # Get LLM provider through the framework
        llm_provider = self.llm()

        # Basic implementation using single agent
        response = await llm_provider.completion(task)
        message = Message(role="assistant", content=str(response))

        # Get memory through the framework if available
        memory = self.memory()
        if memory:
            await memory.add_message(message)

        return [message]


class AutoGenGroup(AgentGroup, BasePluginProvider):
    """AutoGen implementation of an agent group."""

    def __init__(self, **kwargs: Any):
        """Initialize the AutoGen agent group.

        Args:
            **kwargs: Configuration for the agent group.
        """
        super().__init__(**kwargs)
        self.agents: list[AutoGenAgent] = []

    async def initialize(self) -> None:
        """Initialize the agent group."""
        # Call the base class implementation first
        await super().initialize()

        # Create agents based on config
        for agent_config in self.config.get("agents", []):
            # Create agent using plugin registry
            agent = AutoGenAgent(**agent_config)
            await agent.initialize()
            self.agents.append(agent)

    async def cleanup(self) -> None:
        """Clean up resources used by the agent group."""
        # Clean up all agent resources
        for agent in self.agents:
            await agent.cleanup()

        self.agents = []

        # Call the base class cleanup
        await super().cleanup()

    async def execute(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """Execute a task using the agent group.

        Args:
            input_data: Input data containing task and parameters

        Returns:
            Task execution result
        """
        # Get task type from input
        task_type = input_data.get("task")

        if not task_type:
            return {"status": "error", "error": "No task specified"}

        try:
            # Run the task with all agents
            results = []
            for agent in self.agents:
                agent_result = await agent.execute(input_data)
                results.append(agent_result)

            # Combine results
            return {"status": "success", "results": results}

        except Exception as e:
            self.logger.error(f"Error executing task '{task_type}': {e}")
            return {"status": "error", "error": str(e)}

    async def execute_task(self, task: str) -> list[Message]:
        """Execute a task using the agent group.

        Args:
            task: The task to execute.

        Returns:
            List of messages from the execution.
        """
        messages: list[Message] = []

        # Get memory through the framework if available
        memory = self.memory()

        # Basic round-robin execution
        for agent in self.agents:
            agent_messages = await agent.execute_task(task)
            messages.extend(agent_messages)

            if memory:
                for message in agent_messages:
                    await memory.add_message(message)

        return messages
