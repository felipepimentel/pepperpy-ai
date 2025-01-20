"""Fine-tuning learning strategy implementation."""

import logging
from typing import Any, Dict, List, Optional

from ...common.errors import PepperpyError
from ..models.llm import LLMModel
from ..models.types import Message
from .base import LearningStrategy, LearningError


logger = logging.getLogger(__name__)


class FineTuningStrategy(LearningStrategy):
    """Fine-tuning learning strategy implementation."""
    
    def __init__(
        self,
        name: str,
        model: LLMModel,
        epochs: int = 3,
        batch_size: int = 32,
        learning_rate: float = 1e-5,
        config: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize fine-tuning strategy.
        
        Args:
            name: Strategy name
            model: Language model
            epochs: Number of training epochs
            batch_size: Training batch size
            learning_rate: Training learning rate
            config: Optional strategy configuration
        """
        super().__init__(name, config)
        self._model = model
        self._epochs = epochs
        self._batch_size = batch_size
        self._learning_rate = learning_rate
        
    @property
    def model(self) -> LLMModel:
        """Return language model."""
        return self._model
        
    @property
    def epochs(self) -> int:
        """Return number of training epochs."""
        return self._epochs
        
    @property
    def batch_size(self) -> int:
        """Return training batch size."""
        return self._batch_size
        
    @property
    def learning_rate(self) -> float:
        """Return training learning rate."""
        return self._learning_rate
        
    async def _initialize(self) -> None:
        """Initialize fine-tuning strategy."""
        await super()._initialize()
        await self._model.initialize()
        
    async def _cleanup(self) -> None:
        """Clean up fine-tuning strategy."""
        await super()._cleanup()
        await self._model.cleanup()
        
    async def train(
        self,
        input_data: Any,
        context: Optional[Dict[str, Any]] = None,
    ) -> Any:
        """Train on input data.
        
        Args:
            input_data: Input data
            context: Optional training context
            
        Returns:
            Training result
            
        Raises:
            LearningError: If training fails
        """
        try:
            # Convert input to training examples
            if isinstance(input_data, (list, tuple)):
                examples = input_data
            else:
                raise LearningError(f"Invalid input type: {type(input_data)}")
                
            # Validate training examples
            for example in examples:
                if not isinstance(example, dict):
                    raise LearningError("Examples must be dictionaries")
                if "input" not in example or "output" not in example:
                    raise LearningError("Examples must have 'input' and 'output' fields")
                    
            # Fine-tune model
            training_config = {
                "epochs": self._epochs,
                "batch_size": self._batch_size,
                "learning_rate": self._learning_rate,
                **(context or {}),
            }
            
            result = await self._model.fine_tune(examples, training_config)
            return result
            
        except Exception as e:
            raise LearningError(f"Fine-tuning failed: {e}") from e
            
    async def evaluate(
        self,
        input_data: Any,
        context: Optional[Dict[str, Any]] = None,
    ) -> Any:
        """Evaluate on input data.
        
        Args:
            input_data: Input data
            context: Optional evaluation context
            
        Returns:
            Evaluation result
            
        Raises:
            LearningError: If evaluation fails
        """
        try:
            # Convert input to evaluation examples
            if isinstance(input_data, (list, tuple)):
                examples = input_data
            else:
                raise LearningError(f"Invalid input type: {type(input_data)}")
                
            # Validate evaluation examples
            for example in examples:
                if not isinstance(example, dict):
                    raise LearningError("Examples must be dictionaries")
                if "input" not in example or "output" not in example:
                    raise LearningError("Examples must have 'input' and 'output' fields")
                    
            # Evaluate model
            results = []
            for example in examples:
                # Generate response
                message = Message(role="user", content=example["input"])
                response = await self._model.generate([message])
                
                # Compare with expected output
                results.append({
                    "input": example["input"],
                    "expected": example["output"],
                    "actual": response.content,
                })
                
            return {
                "examples": len(examples),
                "results": results,
            }
            
        except Exception as e:
            raise LearningError(f"Fine-tuning evaluation failed: {e}") from e
            
    def validate(self) -> None:
        """Validate fine-tuning strategy state."""
        super().validate()
        
        if not self._model:
            raise ValueError("Language model not provided")
            
        if self._epochs < 1:
            raise ValueError("Number of epochs must be greater than 0")
            
        if self._batch_size < 1:
            raise ValueError("Batch size must be greater than 0")
            
        if self._learning_rate <= 0:
            raise ValueError("Learning rate must be positive") 