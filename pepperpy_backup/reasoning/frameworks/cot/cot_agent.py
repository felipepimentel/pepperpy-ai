"""Chain of Thought agent implementation."""

import logging
from typing import Any, Dict, List, Optional, Tuple

from ...common.errors import AgentError
from ...core.context import Context
from ...models.llm import LLMModel
from ..base.base_agent import BaseAgent
from ..base.interfaces import Tool, Message, AgentMemory, AgentObserver


logger = logging.getLogger(__name__)


class CoTAgent(BaseAgent):
    """Chain of Thought agent implementation."""
    
    def __init__(
        self,
        name: str,
        model: LLMModel,
        tools: Optional[List[Tool]] = None,
        memory: Optional[AgentMemory] = None,
        observers: Optional[List[AgentObserver]] = None,
        context: Optional[Context] = None,
        max_steps: int = 5,
        config: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize CoT agent.
        
        Args:
            name: Agent name
            model: Language model
            tools: Optional list of tools
            memory: Optional agent memory
            observers: Optional list of observers
            context: Optional execution context
            max_steps: Maximum reasoning steps (default: 5)
            config: Optional agent configuration
        """
        super().__init__(name, model, tools, memory, observers, context)
        self._max_steps = max_steps
        self._config = config or {}
        
    async def _process(self, input_data: Any) -> Any:
        """Process input using Chain of Thought pattern.
        
        Args:
            input_data: Input data
            
        Returns:
            Processing result
            
        Raises:
            AgentError: If processing fails
        """
        try:
            # Convert input to message
            if isinstance(input_data, str):
                message = Message(content=input_data, role="user")
            elif isinstance(input_data, Message):
                message = input_data
            else:
                raise AgentError(f"Invalid input type: {type(input_data)}")
                
            # Add input message
            await self.add_message(message)
            
            # Start reasoning loop
            step = 0
            while step < self._max_steps:
                # Get next thought
                thought = await self._get_next_thought()
                
                # Check if done
                if thought.get("type") == "finish":
                    return thought.get("output")
                    
                # Add thought
                await self.add_message(
                    Message(
                        content=thought.get("reasoning", ""),
                        role="thought",
                        metadata={"step": step},
                    )
                )
                
                step += 1
                
            raise AgentError("Maximum steps reached")
            
        except Exception as e:
            raise AgentError(f"Failed to process input: {e}") from e
            
    async def _get_next_thought(self) -> Dict[str, Any]:
        """Get next thought from model.
        
        Returns:
            Thought dictionary with type and content
            
        Raises:
            AgentError: If thought cannot be determined
        """
        try:
            # Build prompt
            prompt = (
                "You are a Chain of Thought agent that solves tasks step by step.\n"
                "Previous messages:\n"
            )
            
            # Add message history
            for message in self._messages[-5:]:  # Last 5 messages
                prompt += f"{message.role}: {message.content}\n"
                
            prompt += (
                "\nWhat is your next step in solving this task?\n"
                "You can:\n"
                "1. Continue reasoning by returning: "
                "{type: 'thought', reasoning: 'Your step-by-step reasoning'}\n"
                "2. Finish task by returning: {type: 'finish', output: 'Your final answer'}\n"
            )
            
            # Get model response
            response = await self._model.generate([Message(content=prompt, role="system")])
            
            # Parse thought
            try:
                import json
                thought = json.loads(response[0].content)
                if not isinstance(thought, dict):
                    raise ValueError("Thought must be a dictionary")
                if "type" not in thought:
                    raise ValueError("Thought must have 'type' field")
                return thought
            except Exception as e:
                raise AgentError(f"Invalid thought format: {e}")
                
        except Exception as e:
            raise AgentError(f"Failed to get next thought: {e}") from e
            
    def validate(self) -> None:
        """Validate agent state."""
        super().validate()
        
        if self._max_steps <= 0:
            raise ValueError("Maximum steps must be positive") 