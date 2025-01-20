"""Chain of thought reasoner implementation."""

import logging
from typing import Any, Dict, List, Optional

from ..common.errors import PepperpyError
from ..models.llm import LLMModel
from ..models.types import Message
from .base import Reasoner, ReasoningError


logger = logging.getLogger(__name__)


class ChainOfThoughtReasoner(Reasoner):
    """Chain of thought reasoner implementation."""
    
    def __init__(
        self,
        name: str,
        model: LLMModel,
        max_steps: int = 5,
        config: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize chain of thought reasoner.
        
        Args:
            name: Reasoner name
            model: Language model
            max_steps: Maximum number of reasoning steps
            config: Optional reasoner configuration
        """
        super().__init__(name, config)
        self._model = model
        self._max_steps = max_steps
        
    @property
    def model(self) -> LLMModel:
        """Return language model."""
        return self._model
        
    @property
    def max_steps(self) -> int:
        """Return maximum number of reasoning steps."""
        return self._max_steps
        
    async def _initialize(self) -> None:
        """Initialize reasoner."""
        await super()._initialize()
        await self._model.initialize()
        
    async def _cleanup(self) -> None:
        """Clean up reasoner."""
        await super()._cleanup()
        await self._model.cleanup()
        
    async def reason(
        self,
        input_data: Any,
        context: Optional[Dict[str, Any]] = None,
    ) -> Any:
        """Reason about input data using chain of thought.
        
        Args:
            input_data: Input data
            context: Optional reasoning context
            
        Returns:
            Reasoning result
            
        Raises:
            ReasoningError: If reasoning fails
        """
        context = context or {}
        thoughts: List[str] = []
        
        try:
            # Initial thought
            thought = await self._get_next_thought(input_data, thoughts, context)
            thoughts.append(thought)
            
            # Continue reasoning until conclusion or max steps reached
            while len(thoughts) < self._max_steps:
                thought = await self._get_next_thought(input_data, thoughts, context)
                
                if not thought or thought.lower().startswith("conclusion:"):
                    break
                    
                thoughts.append(thought)
                
            # Extract conclusion
            conclusion = thoughts[-1]
            if not conclusion.lower().startswith("conclusion:"):
                conclusion = await self._get_conclusion(input_data, thoughts, context)
                
            return {
                "thoughts": thoughts,
                "conclusion": conclusion,
            }
            
        except Exception as e:
            raise ReasoningError(f"Chain of thought reasoning failed: {e}")
            
    async def _get_next_thought(
        self,
        input_data: Any,
        thoughts: List[str],
        context: Dict[str, Any],
    ) -> str:
        """Get next thought.
        
        Args:
            input_data: Input data
            thoughts: Previous thoughts
            context: Reasoning context
            
        Returns:
            Next thought
        """
        prompt = self._build_thought_prompt(input_data, thoughts, context)
        message = Message(role="user", content=prompt)
        response = await self._model.generate([message])
        return response.content
        
    async def _get_conclusion(
        self,
        input_data: Any,
        thoughts: List[str],
        context: Dict[str, Any],
    ) -> str:
        """Get conclusion.
        
        Args:
            input_data: Input data
            thoughts: Previous thoughts
            context: Reasoning context
            
        Returns:
            Conclusion
        """
        prompt = self._build_conclusion_prompt(input_data, thoughts, context)
        message = Message(role="user", content=prompt)
        response = await self._model.generate([message])
        return response.content
        
    def _build_thought_prompt(
        self,
        input_data: Any,
        thoughts: List[str],
        context: Dict[str, Any],
    ) -> str:
        """Build thought prompt.
        
        Args:
            input_data: Input data
            thoughts: Previous thoughts
            context: Reasoning context
            
        Returns:
            Thought prompt
        """
        prompt = f"Input: {input_data}\n\n"
        
        if thoughts:
            prompt += "Previous thoughts:\n"
            for i, thought in enumerate(thoughts, 1):
                prompt += f"{i}. {thought}\n"
            prompt += "\n"
            
        prompt += "Next thought:"
        return prompt
        
    def _build_conclusion_prompt(
        self,
        input_data: Any,
        thoughts: List[str],
        context: Dict[str, Any],
    ) -> str:
        """Build conclusion prompt.
        
        Args:
            input_data: Input data
            thoughts: Previous thoughts
            context: Reasoning context
            
        Returns:
            Conclusion prompt
        """
        prompt = f"Input: {input_data}\n\n"
        
        if thoughts:
            prompt += "Thoughts:\n"
            for i, thought in enumerate(thoughts, 1):
                prompt += f"{i}. {thought}\n"
            prompt += "\n"
            
        prompt += "Conclusion:"
        return prompt
        
    def validate(self) -> None:
        """Validate reasoner state."""
        super().validate()
        
        if not self._model:
            raise ValueError("Language model not provided")
            
        if self._max_steps < 1:
            raise ValueError("Maximum steps must be greater than 0") 