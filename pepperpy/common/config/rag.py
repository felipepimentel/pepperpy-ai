"""Configuration for RAG workflows."""

from dataclasses import dataclass
from typing import Optional

from .base import BaseConfig, ConfigError
from .validation import ValidationMixin


@dataclass
class RAGConfig(BaseConfig, ValidationMixin):
    """Configuration for RAG workflows."""
    
    max_context_length: int = 4000
    min_similarity: float = 0.7
    batch_size: int = 5
    enable_metrics: bool = True
    
    def validate(self) -> None:
        """Validate RAG configuration.
        
        Raises:
            ConfigError: If validation fails.
        """
        self.validate_positive("max_context_length", self.max_context_length)
        self.validate_range("min_similarity", self.min_similarity, 0, 1)
        self.validate_positive("batch_size", self.batch_size) 