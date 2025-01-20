"""Text cleaning algorithm implementation."""

import logging
import re
from typing import Any, Dict, List, Optional, Pattern

from ....common.errors import PepperpyError
from .base_algorithm import BaseAlgorithm, AlgorithmError


logger = logging.getLogger(__name__)


class CleaningError(PepperpyError):
    """Cleaning error."""
    pass


class TextCleaningAlgorithm(BaseAlgorithm):
    """Text cleaning algorithm implementation."""
    
    # Regular expressions for text cleaning
    URL_PATTERN: Pattern[str] = re.compile(
        r"http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|"
        r"(?:%[0-9a-fA-F][0-9a-fA-F]))+"
    )
    EMAIL_PATTERN: Pattern[str] = re.compile(
        r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
    )
    NUMBER_PATTERN: Pattern[str] = re.compile(r"\d+")
    PUNCTUATION_PATTERN: Pattern[str] = re.compile(r"[^\w\s]")
    
    def __init__(
        self,
        name: str,
        remove_urls: bool = True,
        remove_emails: bool = True,
        remove_numbers: bool = False,
        remove_punctuation: bool = False,
        config: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize algorithm.
        
        Args:
            name: Algorithm name
            remove_urls: Whether to remove URLs (default: True)
            remove_emails: Whether to remove email addresses (default: True)
            remove_numbers: Whether to remove numbers (default: False)
            remove_punctuation: Whether to remove punctuation (default: False)
            config: Optional algorithm configuration
        """
        super().__init__(name, config)
        self._remove_urls = remove_urls
        self._remove_emails = remove_emails
        self._remove_numbers = remove_numbers
        self._remove_punctuation = remove_punctuation
        
    def _validate_input(self, data: Any) -> None:
        """Validate input data.
        
        Args:
            data: Data to validate
            
        Raises:
            AlgorithmError: If data is invalid
        """
        if not isinstance(data, str):
            raise AlgorithmError(f"Expected string input, got {type(data)}")
            
    def _validate_output(self, data: Any) -> None:
        """Validate output data.
        
        Args:
            data: Data to validate
            
        Raises:
            AlgorithmError: If data is invalid
        """
        if not isinstance(data, str):
            raise AlgorithmError(f"Expected string output, got {type(data)}")
            
    async def _process_data(
        self,
        data: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Process text by cleaning.
        
        Args:
            data: Text to process
            context: Optional processing context
            
        Returns:
            Cleaned text
            
        Raises:
            AlgorithmError: If text cannot be processed
        """
        try:
            # Clean text
            result = data
            
            if self._remove_urls:
                result = self.URL_PATTERN.sub(" ", result)
                
            if self._remove_emails:
                result = self.EMAIL_PATTERN.sub(" ", result)
                
            if self._remove_numbers:
                result = self.NUMBER_PATTERN.sub(" ", result)
                
            if self._remove_punctuation:
                result = self.PUNCTUATION_PATTERN.sub(" ", result)
                
            # Normalize whitespace
            result = " ".join(result.split())
            
            return result
            
        except Exception as e:
            raise CleaningError(f"Failed to clean text: {e}") from e
            
    def validate(self) -> None:
        """Validate algorithm state."""
        super().validate()
        
        if not any([
            self._remove_urls,
            self._remove_emails,
            self._remove_numbers,
            self._remove_punctuation,
        ]):
            raise ValueError("At least one cleaning option must be enabled")
