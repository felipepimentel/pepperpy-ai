"""Data transformation functionality."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, TypeVar, Generic

from pepperpy.common.errors import PepperpyError
from pepperpy.core.lifecycle import Lifecycle


class TransformationError(PepperpyError):
    """Transformation error."""
    pass


T = TypeVar("T")
U = TypeVar("U")


class DataTransformer(Lifecycle, ABC, Generic[T, U]):
    """Base class for data transformers."""
    
    def __init__(self, name: str):
        """Initialize transformer.
        
        Args:
            name: Transformer name
        """
        super().__init__()
        self.name = name
        
    @abstractmethod
    async def transform(self, data: T) -> U:
        """Transform input data.
        
        Args:
            data: Input data to transform
            
        Returns:
            Transformed data
            
        Raises:
            TransformationError: If transformation fails
        """
        pass
        
    def validate(self) -> None:
        """Validate transformer state."""
        super().validate()
        
        if not self.name:
            raise ValueError("Transformer name cannot be empty") 