"""Configuration for learning strategies."""

from dataclasses import dataclass
from typing import Optional

from .base import BaseConfig, ConfigError
from .validation import ValidationMixin


@dataclass
class InContextConfig(ValidationMixin):
    """Configuration for in-context learning."""
    
    max_examples: int = 5
    similarity_threshold: float = 0.8
    
    def validate(self) -> None:
        """Validate in-context learning configuration.
        
        Raises:
            ConfigError: If validation fails.
        """
        self.validate_positive("max_examples", self.max_examples)
        self.validate_range("similarity_threshold", self.similarity_threshold, 0, 1)


@dataclass
class RetrievalConfig(ValidationMixin):
    """Configuration for retrieval-based learning."""
    
    max_context_length: int = 2000
    min_similarity: float = 0.7
    
    def validate(self) -> None:
        """Validate retrieval-based learning configuration.
        
        Raises:
            ConfigError: If validation fails.
        """
        self.validate_positive("max_context_length", self.max_context_length)
        self.validate_range("min_similarity", self.min_similarity, 0, 1)


@dataclass
class FineTuningConfig(ValidationMixin):
    """Configuration for fine-tuning."""
    
    num_epochs: int = 3
    batch_size: int = 4
    learning_rate: float = 2e-5
    validation_split: float = 0.2
    
    def validate(self) -> None:
        """Validate fine-tuning configuration.
        
        Raises:
            ConfigError: If validation fails.
        """
        self.validate_positive("num_epochs", self.num_epochs)
        self.validate_positive("batch_size", self.batch_size)
        self.validate_positive("learning_rate", self.learning_rate)
        self.validate_range("validation_split", self.validation_split, 0, 1)


@dataclass
class LearningConfig(BaseConfig, ValidationMixin):
    """Configuration for learning strategies."""
    
    in_context: InContextConfig = InContextConfig()
    retrieval: RetrievalConfig = RetrievalConfig()
    fine_tuning: FineTuningConfig = FineTuningConfig()
    
    def validate(self) -> None:
        """Validate learning strategies configuration.
        
        Raises:
            ConfigError: If validation fails.
        """
        self.in_context.validate()
        self.retrieval.validate()
        self.fine_tuning.validate() 