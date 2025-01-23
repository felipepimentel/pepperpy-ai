"""Example template implementations."""

import logging
from typing import Any, Dict, List, Optional

from .generator import ExampleTemplate


logger = logging.getLogger(__name__)


class SimpleTemplate(ExampleTemplate):
    """Simple example template implementation."""
    
    def __init__(
        self,
        template: str,
        required_params: Optional[List[str]] = None,
    ) -> None:
        """Initialize simple template.
        
        Args:
            template: Template string with placeholders
            required_params: Optional list of required parameters
        """
        self.template = template
        self.required_params = required_params or []
        
    def generate(self, **kwargs: Any) -> str:
        """Generate example from template.
        
        Args:
            **kwargs: Template parameters
            
        Returns:
            Generated example
            
        Raises:
            ValueError: If required parameters are missing
        """
        # Validate required parameters
        missing_params = [
            param for param in self.required_params
            if param not in kwargs
        ]
        if missing_params:
            raise ValueError(
                f"Missing required parameters: {', '.join(missing_params)}"
            )
            
        # Format template with parameters
        try:
            return self.template.format(**kwargs)
            
        except KeyError as e:
            raise ValueError(f"Missing template parameter: {e}")
        except Exception as e:
            raise ValueError(f"Failed to format template: {e}")


class DictTemplate(ExampleTemplate):
    """Dictionary example template implementation."""
    
    def __init__(
        self,
        template: Dict[str, Any],
        required_params: Optional[List[str]] = None,
    ) -> None:
        """Initialize dictionary template.
        
        Args:
            template: Template dictionary with placeholders
            required_params: Optional list of required parameters
        """
        self.template = template
        self.required_params = required_params or []
        
    def generate(self, **kwargs: Any) -> Dict[str, Any]:
        """Generate example from template.
        
        Args:
            **kwargs: Template parameters
            
        Returns:
            Generated example
            
        Raises:
            ValueError: If required parameters are missing
        """
        # Validate required parameters
        missing_params = [
            param for param in self.required_params
            if param not in kwargs
        ]
        if missing_params:
            raise ValueError(
                f"Missing required parameters: {', '.join(missing_params)}"
            )
            
        # Format template with parameters
        try:
            return self._format_value(self.template, kwargs)
            
        except KeyError as e:
            raise ValueError(f"Missing template parameter: {e}")
        except Exception as e:
            raise ValueError(f"Failed to format template: {e}")
            
    def _format_value(
        self,
        value: Any,
        params: Dict[str, Any],
    ) -> Any:
        """Format template value with parameters.
        
        Args:
            value: Template value
            params: Template parameters
            
        Returns:
            Formatted value
        """
        if isinstance(value, str):
            return value.format(**params)
            
        elif isinstance(value, dict):
            return {
                key: self._format_value(val, params)
                for key, val in value.items()
            }
            
        elif isinstance(value, list):
            return [
                self._format_value(item, params)
                for item in value
            ]
            
        return value


class ListTemplate(ExampleTemplate):
    """List example template implementation."""
    
    def __init__(
        self,
        template: List[Any],
        required_params: Optional[List[str]] = None,
    ) -> None:
        """Initialize list template.
        
        Args:
            template: Template list with placeholders
            required_params: Optional list of required parameters
        """
        self.template = template
        self.required_params = required_params or []
        
    def generate(self, **kwargs: Any) -> List[Any]:
        """Generate example from template.
        
        Args:
            **kwargs: Template parameters
            
        Returns:
            Generated example
            
        Raises:
            ValueError: If required parameters are missing
        """
        # Validate required parameters
        missing_params = [
            param for param in self.required_params
            if param not in kwargs
        ]
        if missing_params:
            raise ValueError(
                f"Missing required parameters: {', '.join(missing_params)}"
            )
            
        # Format template with parameters
        try:
            return self._format_value(self.template, kwargs)
            
        except KeyError as e:
            raise ValueError(f"Missing template parameter: {e}")
        except Exception as e:
            raise ValueError(f"Failed to format template: {e}")
            
    def _format_value(
        self,
        value: Any,
        params: Dict[str, Any],
    ) -> Any:
        """Format template value with parameters.
        
        Args:
            value: Template value
            params: Template parameters
            
        Returns:
            Formatted value
        """
        if isinstance(value, str):
            return value.format(**params)
            
        elif isinstance(value, dict):
            return {
                key: self._format_value(val, params)
                for key, val in value.items()
            }
            
        elif isinstance(value, list):
            return [
                self._format_value(item, params)
                for item in value
            ]
            
        return value 