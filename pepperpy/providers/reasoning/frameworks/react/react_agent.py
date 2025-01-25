"""ReAct agent implementation."""

import logging
from typing import Any, Dict, List, Optional, Tuple

from ...common.errors import AgentError
from ...core.context import Context
from ...models.llm import LLMModel
from ..base.base_agent import BaseAgent
from ..base.interfaces import Tool, Message, AgentMemory, AgentObserver


logger = logging.getLogger(__name__)


class ReActAgent(BaseAgent):
    """ReAct (Reasoning + Acting) agent implementation."""
    
    def __init__(
        self,
        name: str,
        model: LLMModel,
        tools: Optional[List[Tool]] = None,
        memory: Optional[AgentMemory] = None,
        observers: Optional[List[AgentObserver]] = None,
        context: Optional[Context] = None,
        max_iterations: int = 10,
        config: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize ReAct agent.
        
        Args:
            name: Agent name
            model: Language model
            tools: Optional list of tools
            memory: Optional agent memory
            observers: Optional list of observers
            context: Optional execution context
            max_iterations: Maximum reasoning iterations (default: 10)
            config: Optional agent configuration
        """
        super().__init__(name, model, tools, memory, observers, context)
        self._max_iterations = max_iterations
        self._config = config or {}
        
    async def _process(self, input_data: Any) -> Any:
        """Process input using ReAct pattern.
        
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
            iteration = 0
            while iteration < self._max_iterations:
                # Get next action
                action = await self._get_next_action()
                
                # Check if done
                if action.get("type") == "finish":
                    return action.get("output")
                    
                # Execute tool
                if action.get("type") == "tool":
                    tool_name = action.get("tool")
                    tool_input = action.get("input")
                    
                    # Find tool
                    tool = next(
                        (t for t in self._tools if t.__class__.__name__ == tool_name),
                        None,
                    )
                    if not tool:
                        raise AgentError(f"Tool not found: {tool_name}")
                        
                    # Execute tool
                    try:
                        result = await tool.execute(tool_input)
                    except Exception as e:
                        result = f"Error: {str(e)}"
                        
                    # Add observation
                    await self.add_message(
                        Message(
                            content=str(result),
                            role="observation",
                            metadata={"tool": tool_name},
                        )
                    )
                    
                iteration += 1
                
            raise AgentError("Maximum iterations reached")
            
        except Exception as e:
            raise AgentError(f"Failed to process input: {e}") from e
            
    async def _get_next_action(self) -> Dict[str, Any]:
        """Get next action from model.
        
        Returns:
            Action dictionary with type and parameters
            
        Raises:
            AgentError: If action cannot be determined
        """
        try:
            # Get available tools
            tool_descriptions = []
            for tool in self._tools:
                tool_descriptions.append(
                    f"- {tool.__class__.__name__}: {tool.__doc__ or 'No description'}"
                )
                
            # Build prompt
            prompt = (
                "You are a ReAct agent that can use tools to solve tasks.\n"
                "Available tools:\n"
                f"{chr(10).join(tool_descriptions)}\n\n"
                "Previous messages:\n"
            )
            
            # Add message history
            for message in self._messages[-5:]:  # Last 5 messages
                prompt += f"{message.role}: {message.content}\n"
                
            prompt += (
                "\nDecide what to do next. You can:\n"
                "1. Use a tool by returning: {type: 'tool', tool: 'ToolName', input: ...}\n"
                "2. Finish task by returning: {type: 'finish', output: ...}\n"
                "\nWhat is your next action?"
            )
            
            # Get model response
            response = await self._model.generate(prompt)
            
            # Parse action
            try:
                import json
                action = json.loads(response)
                if not isinstance(action, dict):
                    raise ValueError("Action must be a dictionary")
                if "type" not in action:
                    raise ValueError("Action must have 'type' field")
                return action
            except Exception as e:
                raise AgentError(f"Invalid action format: {e}")
                
        except Exception as e:
            raise AgentError(f"Failed to get next action: {e}") from e
            
    def validate(self) -> None:
        """Validate agent state."""
        super().validate()
        
        if self._max_iterations <= 0:
            raise ValueError("Maximum iterations must be positive") 