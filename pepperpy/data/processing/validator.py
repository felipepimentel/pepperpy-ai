"""Data validator implementation."""

import logging
from typing import Any, Dict, List, Optional, Protocol, TypeVar

from ...common.errors import PepperpyError
from ...core.lifecycle import Lifecycle


logger = logging.getLogger(__name__)


class ValidationError(PepperpyError):
    """Validation error."""
    pass


class Validator(Protocol):
    """Data validator protocol."""
    
    async def validate(
        self,
        data: Any,
        context: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Validate data.
        
        Args:
            data: Data to validate
            context: Optional validation context
            
        Returns:
            True if data is valid, False otherwise
            
        Raises:
            ValidationError: If data cannot be validated
        """
        ...


V = TypeVar("V", bound=Validator)


class ValidationManager(Lifecycle):
    """Data validation manager implementation."""
    
    def __init__(
        self,
        name: str,
        validators: List[Validator],
        config: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize validation manager.
        
        Args:
            name: Manager name
            validators: Data validators
            config: Optional manager configuration
        """
        super().__init__(name)
        self._validators = validators
        self._config = config or {}
        
    @property
    def config(self) -> Dict[str, Any]:
        """Return manager configuration."""
        return self._config
        
    async def _initialize(self) -> None:
        """Initialize manager."""
        pass
        
    async def _cleanup(self) -> None:
        """Clean up manager."""
        pass
        
    async def validate_data(
        self,
        data: Any,
        context: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Validate data using all validators.
        
        Args:
            data: Data to validate
            context: Optional validation context
            
        Returns:
            True if data is valid, False otherwise
            
        Raises:
            ValidationError: If data cannot be validated
        """
        try:
            # Apply validators in sequence
            for validator in self._validators:
                if not await validator.validate(data, context):
                    return False
                    
            return True
            
        except Exception as e:
            raise ValidationError(f"Failed to validate data: {e}") from e
            
    def validate(self) -> None:
        """Validate manager state."""
        super().validate()
        
        if not self.name:
            raise ValueError("Manager name cannot be empty")
            
        if not self._validators:
            raise ValueError("No validators provided")


class TextLengthValidator(Validator):
    """Text length validator."""
    
    def __init__(
        self,
        min_length: Optional[int] = None,
        max_length: Optional[int] = None,
        config: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize validator.
        
        Args:
            min_length: Optional minimum length
            max_length: Optional maximum length
            config: Optional validator configuration
        """
        self._min_length = min_length
        self._max_length = max_length
        self._config = config or {}
        
    async def validate(
        self,
        data: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Validate text length.
        
        Args:
            data: Text to validate
            context: Optional validation context
            
        Returns:
            True if text length is valid, False otherwise
            
        Raises:
            ValidationError: If text cannot be validated
        """
        try:
            # Validate input
            if not isinstance(data, str):
                raise ValidationError(f"Expected string input, got {type(data)}")
                
            # Check length
            length = len(data)
            
            if self._min_length is not None and length < self._min_length:
                return False
                
            if self._max_length is not None and length > self._max_length:
                return False
                
            return True
            
        except Exception as e:
            raise ValidationError(f"Failed to validate text: {e}") from e


class TextContentValidator(Validator):
    """Text content validator."""
    
    def __init__(
        self,
        required_words: Optional[List[str]] = None,
        blocked_words: Optional[List[str]] = None,
        min_words: Optional[int] = None,
        max_words: Optional[int] = None,
        config: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize validator.
        
        Args:
            required_words: Optional list of required words
            blocked_words: Optional list of blocked words
            min_words: Optional minimum word count
            max_words: Optional maximum word count
            config: Optional validator configuration
        """
        self._required_words = required_words
        self._blocked_words = blocked_words or []
        self._min_words = min_words
        self._max_words = max_words
        self._config = config or {}
        
    async def validate(
        self,
        data: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Validate text content.
        
        Args:
            data: Text to validate
            context: Optional validation context
            
        Returns:
            True if text content is valid, False otherwise
            
        Raises:
            ValidationError: If text cannot be validated
        """
        try:
            # Validate input
            if not isinstance(data, str):
                raise ValidationError(f"Expected string input, got {type(data)}")
                
            # Split into words
            words = data.split()
            
            # Check word count
            if self._min_words is not None and len(words) < self._min_words:
                return False
                
            if self._max_words is not None and len(words) > self._max_words:
                return False
                
            # Check blocked words
            if any(word in words for word in self._blocked_words):
                return False
                
            # Check required words
            if self._required_words is not None:
                if not all(word in words for word in self._required_words):
                    return False
                    
            return True
            
        except Exception as e:
            raise ValidationError(f"Failed to validate text: {e}") from e


class TextFormatValidator(Validator):
    """Text format validator."""
    
    def __init__(
        self,
        allow_urls: bool = True,
        allow_emails: bool = True,
        allow_numbers: bool = True,
        allow_punctuation: bool = True,
        config: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize validator.
        
        Args:
            allow_urls: Whether to allow URLs (default: True)
            allow_emails: Whether to allow email addresses (default: True)
            allow_numbers: Whether to allow numbers (default: True)
            allow_punctuation: Whether to allow punctuation (default: True)
            config: Optional validator configuration
        """
        self._allow_urls = allow_urls
        self._allow_emails = allow_emails
        self._allow_numbers = allow_numbers
        self._allow_punctuation = allow_punctuation
        self._config = config or {}
        
    async def validate(
        self,
        data: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Validate text format.
        
        Args:
            data: Text to validate
            context: Optional validation context
            
        Returns:
            True if text format is valid, False otherwise
            
        Raises:
            ValidationError: If text cannot be validated
        """
        try:
            # Validate input
            if not isinstance(data, str):
                raise ValidationError(f"Expected string input, got {type(data)}")
                
            # TODO: Implement format validation
            return True
            
        except Exception as e:
            raise ValidationError(f"Failed to validate text: {e}") from e
