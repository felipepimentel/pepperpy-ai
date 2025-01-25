"""Input sanitization module for Pepperpy.

This module provides functionality for sanitizing input data to prevent
security vulnerabilities like XSS, SQL injection, and command injection.
"""

import re
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Pattern, Union

from pepperpy.core.utils.errors import PepperpyError
from pepperpy.core.lifecycle import Lifecycle


class SanitizationError(PepperpyError):
    """Sanitization error."""
    pass


class Sanitizer(Lifecycle, ABC):
    """Base class for input sanitizers."""
    
    def __init__(
        self,
        name: str,
        patterns: Optional[List[Pattern[str]]] = None,
        replacements: Optional[Dict[str, str]] = None,
    ) -> None:
        """Initialize sanitizer.
        
        Args:
            name: Sanitizer name
            patterns: Optional list of regex patterns to match
            replacements: Optional map of pattern replacements
        """
        super().__init__()
        self.name = name
        self._patterns = patterns or []
        self._replacements = replacements or {}
        
    @property
    def patterns(self) -> List[Pattern[str]]:
        """Get sanitization patterns."""
        return self._patterns
        
    @property
    def replacements(self) -> Dict[str, str]:
        """Get pattern replacements."""
        return self._replacements
        
    @abstractmethod
    async def sanitize(self, data: Any) -> Any:
        """Sanitize input data.
        
        Args:
            data: Input data to sanitize
            
        Returns:
            Sanitized data
            
        Raises:
            SanitizationError: If sanitization fails
        """
        pass
        
    def validate(self) -> None:
        """Validate sanitizer state."""
        super().validate()
        
        if not self.name:
            raise ValueError("Sanitizer name cannot be empty")
            
        if not isinstance(self._patterns, list):
            raise ValueError("Patterns must be a list")
            
        if not isinstance(self._replacements, dict):
            raise ValueError("Replacements must be a dictionary")


class TextSanitizer(Sanitizer):
    """Text input sanitizer."""
    
    def __init__(
        self,
        name: str = "text_sanitizer",
        patterns: Optional[List[Pattern[str]]] = None,
        replacements: Optional[Dict[str, str]] = None,
    ) -> None:
        """Initialize text sanitizer.
        
        Args:
            name: Sanitizer name
            patterns: Optional list of regex patterns to match
            replacements: Optional map of pattern replacements
        """
        default_patterns = [
            re.compile(r"<[^>]*>"),  # HTML tags
            re.compile(r"javascript:", re.IGNORECASE),  # JavaScript
            re.compile(r"on\w+\s*=", re.IGNORECASE),  # Event handlers
            re.compile(r"data:\s*\w+/\w+;base64,", re.IGNORECASE),  # Data URLs
        ]
        
        default_replacements = {
            "<": "&lt;",
            ">": "&gt;",
            '"': "&quot;",
            "'": "&#x27;",
            "&": "&amp;",
        }
        
        super().__init__(
            name=name,
            patterns=patterns or default_patterns,
            replacements=replacements or default_replacements,
        )
        
    async def sanitize(self, data: Union[str, List[str], Dict[str, str]]) -> Any:
        """Sanitize text input.
        
        Args:
            data: Text input to sanitize
            
        Returns:
            Sanitized text
            
        Raises:
            SanitizationError: If sanitization fails
        """
        try:
            if isinstance(data, str):
                return self._sanitize_text(data)
            elif isinstance(data, list):
                return [
                    self._sanitize_text(item) if isinstance(item, str) else item
                    for item in data
                ]
            elif isinstance(data, dict):
                return {
                    key: self._sanitize_text(value) if isinstance(value, str) else value
                    for key, value in data.items()
                }
            return data
        except Exception as e:
            raise SanitizationError(f"Failed to sanitize text: {str(e)}")
            
    def _sanitize_text(self, text: str) -> str:
        """Sanitize single text string.
        
        Args:
            text: Text to sanitize
            
        Returns:
            Sanitized text
        """
        # Apply regex patterns
        for pattern in self._patterns:
            text = pattern.sub("", text)
            
        # Apply character replacements
        for char, replacement in self._replacements.items():
            text = text.replace(char, replacement)
            
        return text


class SQLSanitizer(Sanitizer):
    """SQL input sanitizer."""
    
    def __init__(
        self,
        name: str = "sql_sanitizer",
        patterns: Optional[List[Pattern[str]]] = None,
        replacements: Optional[Dict[str, str]] = None,
    ) -> None:
        """Initialize SQL sanitizer.
        
        Args:
            name: Sanitizer name
            patterns: Optional list of regex patterns to match
            replacements: Optional map of pattern replacements
        """
        default_patterns = [
            re.compile(r";\s*$"),  # Trailing semicolons
            re.compile(r"--"),  # SQL comments
            re.compile(r"/\*.*?\*/", re.DOTALL),  # Multi-line comments
            re.compile(r"(?i)union\s+all\s+select"),  # UNION-based injection
            re.compile(r"(?i)select\s+.*?\s+from"),  # SELECT-based injection
            re.compile(r"(?i)insert\s+into"),  # INSERT-based injection
            re.compile(r"(?i)update\s+.*?\s+set"),  # UPDATE-based injection
            re.compile(r"(?i)delete\s+from"),  # DELETE-based injection
        ]
        
        super().__init__(
            name=name,
            patterns=patterns or default_patterns,
            replacements=replacements,
        )
        
    async def sanitize(self, data: Union[str, List[str], Dict[str, str]]) -> Any:
        """Sanitize SQL input.
        
        Args:
            data: SQL input to sanitize
            
        Returns:
            Sanitized SQL
            
        Raises:
            SanitizationError: If sanitization fails
        """
        try:
            if isinstance(data, str):
                return self._sanitize_sql(data)
            elif isinstance(data, list):
                return [
                    self._sanitize_sql(item) if isinstance(item, str) else item
                    for item in data
                ]
            elif isinstance(data, dict):
                return {
                    key: self._sanitize_sql(value) if isinstance(value, str) else value
                    for key, value in data.items()
                }
            return data
        except Exception as e:
            raise SanitizationError(f"Failed to sanitize SQL: {str(e)}")
            
    def _sanitize_sql(self, sql: str) -> str:
        """Sanitize single SQL string.
        
        Args:
            sql: SQL to sanitize
            
        Returns:
            Sanitized SQL
        """
        # Apply regex patterns
        for pattern in self._patterns:
            sql = pattern.sub("", sql)
            
        # Escape single quotes
        sql = sql.replace("'", "''")
            
        return sql


__all__ = [
    "SanitizationError",
    "Sanitizer",
    "TextSanitizer",
    "SQLSanitizer",
]
