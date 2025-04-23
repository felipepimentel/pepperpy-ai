"""Assistant provider for agent tasks.

This module provides an assistant provider that can engage in conversations,
maintain context, and execute tasks using language models.
"""

from typing import dict, list, Optional, Any

from pepperpy.agents.base import Agent
from pepperpy.llm import Message, MessageRole
from pepperpy.agent import AgentProvider
from pepperpy.plugin import ProviderPlugin
from pepperpy.agent.base import AgentError
from pepperpy.agent.base import AgentError

logger = logger.getLogger(__name__)


class Assistant(class Assistant(Agent, ProviderPlugin):
    """Assistant provider for agent tasks.

    This provider implements an AI assistant that can engage in conversations,
    maintain context, and execute tasks using language models.
    """):
    """
    Agent assistant provider.
    
    This provider implements assistant functionality for the PepperPy agent framework.
    """

    async def initialize(self) -> None:
 """Initialize the provider.

        This method is called automatically when the provider is first used.
 """
        # Skip if already initialized
        if self.initialized:
            return
        
        # Create initial message list with system prompt
        system_prompt = self.config.get(
            "system_prompt", "You are a helpful AI assistant."
        )
        self.messages = [Message(content=system_prompt, role=MessageRole.SYSTEM)]
        self.context = {}

        self.logger.debug(
            f"Initialized with model={self.model}"
        )

    async def cleanup(self) -> None:
 """Clean up provider resources.

        This method is called automatically when the context manager exits.
 """
        # Clean up resources
        self.messages = []
        self.context = {}

        # Call the base class cleanup
        await super().cleanup()

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
            raise AgentError("No task specified")

        try:
            # Handle chat task
            if task_type == "chat":
                message = input_data.get("message")
                context = input_data.get("context")

                if message:
                    response = await self.chat(message, context)
                    return {
                        "status": "success",
                        "response": response,
                        "messages": [m.to_dict() for m in self.messages],
                    }
                else:
                    raise AgentError("No message provided")
            else:
                # Treat task as direct message
                response = await self.chat(task_type)
                return {"status": "success", "response": response}

        except Exception as e:
            self.logger.error(f"Error executing task '{task_type}': {e}")
            return {"status": "error", "message": str(e)}

    async def chat(
        self,
        message: str | Message,
        context: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> str:
        """Send a message to the assistant and get a response.

        Args:
            message: Message to send
            context: Optional context to add to the conversation
            **kwargs: Additional arguments to pass to the LLM

        Returns:
            Assistant's response

        Raises:
            RuntimeError: If provider is not initialized
        """
        if not self.initialized:
            raise RuntimeError("Provider not initialized")

        # Get LLM provider through the framework
        llm_provider = self.llm()
        if not llm_provider:
            raise RuntimeError("LLM provider not available")

        # Convert string to Message
        if isinstance(message, str):
            message = Message(content=message, role=MessageRole.USER)

        # Update context
        if context:
            self.context.update(context)

        # Add message to history
        self.messages.append(message)

        # Get memory size from config
        memory_size = self.memory_size

        # Trim history if needed
        if len(self.messages) > memory_size + 1:  # +1 for system prompt
            self.messages = [self.messages[0]] + self.messages[-memory_size:]

        # Get model parameters from config or kwargs
        model = kwargs.get("model", self.model)
        temperature = kwargs.get("temperature", self.temperature)
        max_tokens = kwargs.get("max_tokens", self.max_tokens)

        # Generate response using LLM
        response = await llm_provider.generate(
            messages=self.messages,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        # Add response to history
        assistant_message = Message(
            content=response.content, role=MessageRole.ASSISTANT
        )
        self.messages.append(assistant_message)

        # Save to memory if available
        memory = self.memory()
        if memory:
            await memory.add_message(assistant_message)

        return response.content

    async def execute_task(self, task: str) -> list[Message]:
        """Execute a task and return the messages.

        Args:
            task: The task to execute.

        Returns:
            list of messages from the execution.
        """
        response = await self.chat(task)
        return [Message(role=MessageRole.ASSISTANT, content=response)]
