"""Data validation functionality."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, TypeVar, Generic

from pepperpy.common.errors import PepperpyError
from pepperpy.core.lifecycle import Lifecycle


class ValidationError(PepperpyError):
    """Validation error."""
    pass


T = TypeVar("T")


class DataValidator(Lifecycle, ABC, Generic[T]):
    """Base class for data validators."""
    
    def __init__(self, name: str):
        """Initialize validator.
        
        Args:
            name: Validator name
        """
        super().__init__()
        self.name = name
        
    @abstractmethod
    async def validate_data(self, data: T) -> bool:
        """Validate input data.
        
        Args:
            data: Input data to validate
            
        Returns:
            True if data is valid, False otherwise
            
        Raises:
            ValidationError: If validation fails
        """
        pass
        
    def validate(self) -> None:
        """Validate validator state."""
        super().validate()
        
        if not self.name:
            raise ValueError("Validator name cannot be empty") 