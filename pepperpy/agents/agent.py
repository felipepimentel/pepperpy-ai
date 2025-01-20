"""Base agent implementation for Pepperpy."""

import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Set, Type

from ...core.lifecycle import Lifecycle
from ...core.context import Context
from ...models.llm import LLMModel
from ...common.errors import AgentError
from ...profile import Profile
from .interfaces import (
    Tool,
    Message,
    AgentState,
    AgentMemory,
    AgentObserver,
)

logger = logging.getLogger(__name__)

class BaseAgent(Lifecycle, ABC):
    """Base agent class."""
    
    def __init__(
        self,
        name: str,
        model: LLMModel,
        tools: Optional[List[Tool]] = None,
        memory: Optional[AgentMemory] = None,
        observers: Optional[List[AgentObserver]] = None,
        context: Optional[Context] = None,
        profile: Optional[Profile] = None,
    ) -> None:
        """Initialize agent.
        
        Args:
            name: Agent name
            model: Language model
            tools: Optional list of tools
            memory: Optional agent memory
            observers: Optional list of observers
            context: Optional execution context
            profile: Optional agent profile
        """
        super().__init__(name, context)
        self._model = model
        self._tools = tools or []
        self._memory = memory
        self._observers = observers or []
        self._profile = profile
        self._state = AgentState.IDLE
        self._messages: List[Message] = []
        
    @property
    def model(self) -> LLMModel:
        """Return language model."""
        return self._model
        
    @property
    def tools(self) -> List[Tool]:
        """Return available tools."""
        return self._tools
        
    @property
    def memory(self) -> Optional[AgentMemory]:
        """Return agent memory."""
        return self._memory
        
    @property
    def profile(self) -> Optional[Profile]:
        """Return agent profile."""
        return self._profile
        
    @property
    def state(self) -> AgentState:
        """Return agent state."""
        return self._state
        
    @property
    def messages(self) -> List[Message]:
        """Return message history."""
        return self._messages
        
    async def _initialize(self) -> None:
        """Initialize agent."""
        # Initialize model
        await self._model.initialize()
        
        # Initialize memory
        if self._memory:
            await self._memory.initialize()
            
        # Initialize tools
        for tool in self._tools:
            await tool.initialize()
            
        # Initialize observers
        for observer in self._observers:
            await observer.initialize()
            
        self._state = AgentState.READY
        
    async def _cleanup(self) -> None:
        """Clean up agent."""
        # Clean up model
        await self._model.cleanup()
        
        # Clean up memory
        if self._memory:
            await self._memory.cleanup()
            
        # Clean up tools
        for tool in self._tools:
            await tool.cleanup()
            
        # Clean up observers
        for observer in self._observers:
            await observer.cleanup()
            
        self._state = AgentState.IDLE
        
    async def add_message(self, message: Message) -> None:
        """Add message to history.
        
        Args:
            message: Message to add
        """
        self._messages.append(message)
        
        # Notify observers
        for observer in self._observers:
            await observer.on_message(message)
            
        # Update memory
        if self._memory:
            await self._memory.add_message(message)
            
    async def process(self, input_data: Any) -> Any:
        """Process input data.
        
        Args:
            input_data: Input data
            
        Returns:
            Processing result
            
        Raises:
            AgentError: If agent is not ready
        """
        if self._state != AgentState.READY:
            raise AgentError("Agent not ready")
            
        try:
            self._state = AgentState.PROCESSING
            
            # Notify observers
            for observer in self._observers:
                await observer.on_process_start(input_data)
                
            # Process input
            result = await self._process(input_data)
            
            # Notify observers
            for observer in self._observers:
                await observer.on_process_end(result)
                
            return result
            
        except Exception as e:
            # Notify observers
            for observer in self._observers:
                await observer.on_error(e)
                
            raise
            
        finally:
            self._state = AgentState.READY
            
    @abstractmethod
    async def _process(self, input_data: Any) -> Any:
        """Process input data implementation.
        
        Args:
            input_data: Input data
            
        Returns:
            Processing result
        """
        pass
        
    def validate(self) -> None:
        """Validate agent state."""
        super().validate()
        
        if not self.name:
            raise ValueError("Agent name cannot be empty")
            
        if not self._model:
            raise ValueError("Language model not provided")
            
        if self._context is not None:
            self._context.validate()
