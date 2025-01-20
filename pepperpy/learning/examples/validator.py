"""Example validator implementation."""

import logging
from typing import Any, Dict, List, Optional, Protocol, runtime_checkable

from pepperpy.common.errors import PepperpyError
from pepperpy.core.lifecycle import Lifecycle


logger = logging.getLogger(__name__)


class ExampleValidatorError(PepperpyError):
    """Example validator error."""
    pass


@runtime_checkable
class ExampleValidator(Protocol):
    """Example validator protocol."""
    
    def validate(self, example: Any) -> bool:
        """Validate example.
        
        Args:
            example: Example to validate
            
        Returns:
            True if example is valid, False otherwise
        """
        ...


class SimpleValidator(ExampleValidator):
    """Simple example validator implementation."""
    
    def __init__(
        self,
        required_fields: Optional[List[str]] = None,
        field_types: Optional[Dict[str, type]] = None,
    ) -> None:
        """Initialize simple validator.
        
        Args:
            required_fields: Optional list of required fields
            field_types: Optional mapping of field names to types
        """
        self.required_fields = required_fields or []
        self.field_types = field_types or {}
        
    def validate(self, example: Any) -> bool:
        """Validate example.
        
        Args:
            example: Example to validate
            
        Returns:
            True if example is valid, False otherwise
        """
        try:
            # Validate example type
            if not isinstance(example, dict):
                logger.error("Example must be a dictionary")
                return False
                
            # Validate required fields
            for field in self.required_fields:
                if field not in example:
                    logger.error(f"Missing required field: {field}")
                    return False
                    
            # Validate field types
            for field, field_type in self.field_types.items():
                if field in example and not isinstance(example[field], field_type):
                    logger.error(
                        f"Invalid type for field {field}: "
                        f"expected {field_type}, got {type(example[field])}"
                    )
                    return False
                    
            return True
            
        except Exception as e:
            logger.error(f"Failed to validate example: {e}")
            return False


class ListValidator(ExampleValidator):
    """List example validator implementation."""
    
    def __init__(
        self,
        item_validator: ExampleValidator,
        min_length: Optional[int] = None,
        max_length: Optional[int] = None,
    ) -> None:
        """Initialize list validator.
        
        Args:
            item_validator: Validator for list items
            min_length: Optional minimum list length
            max_length: Optional maximum list length
        """
        self.item_validator = item_validator
        self.min_length = min_length
        self.max_length = max_length
        
    def validate(self, example: Any) -> bool:
        """Validate example.
        
        Args:
            example: Example to validate
            
        Returns:
            True if example is valid, False otherwise
        """
        try:
            # Validate example type
            if not isinstance(example, list):
                logger.error("Example must be a list")
                return False
                
            # Validate list length
            if self.min_length is not None and len(example) < self.min_length:
                logger.error(
                    f"List length {len(example)} is less than "
                    f"minimum length {self.min_length}"
                )
                return False
                
            if self.max_length is not None and len(example) > self.max_length:
                logger.error(
                    f"List length {len(example)} is greater than "
                    f"maximum length {self.max_length}"
                )
                return False
                
            # Validate list items
            for item in example:
                if not self.item_validator.validate(item):
                    return False
                    
            return True
            
        except Exception as e:
            logger.error(f"Failed to validate example: {e}")
            return False


class CompositeValidator(ExampleValidator):
    """Composite example validator implementation."""
    
    def __init__(
        self,
        validators: List[ExampleValidator],
    ) -> None:
        """Initialize composite validator.
        
        Args:
            validators: List of validators to apply
        """
        self.validators = validators
        
    def validate(self, example: Any) -> bool:
        """Validate example.
        
        Args:
            example: Example to validate
            
        Returns:
            True if example is valid, False otherwise
        """
        try:
            # Apply all validators
            for validator in self.validators:
                if not validator.validate(example):
                    return False
                    
            return True
            
        except Exception as e:
            logger.error(f"Failed to validate example: {e}")
            return False 