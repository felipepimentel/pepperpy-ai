"""Base tool implementation."""
from abc import abstractmethod
from typing import Any, Dict, List, Optional

from ..base.capability import BaseCapability

class BaseTool(BaseCapability):
    """Base class for all tools."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the tool."""
        super().__init__(config)
        self.name = config.get("name", self.__class__.__name__)
        self.description = config.get("description", "")
        self.required_params = config.get("required_params", [])
        self.optional_params = config.get("optional_params", {})
    
    @abstractmethod
    async def execute(
        self,
        params: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Any:
        """Execute the tool with the given parameters."""
        pass
    
    def validate_params(self, params: Dict[str, Any]) -> None:
        """Validate the provided parameters."""
        # Check required parameters
        missing = [
            param for param in self.required_params
            if param not in params
        ]
        if missing:
            raise ValueError(f"Missing required parameters: {', '.join(missing)}")
        
        # Check parameter types
        for param, value in params.items():
            if param in self.optional_params:
                expected_type = self.optional_params[param]["type"]
                if not isinstance(value, expected_type):
                    raise TypeError(
                        f"Parameter '{param}' must be of type {expected_type.__name__}"
                    )
    
    def get_schema(self) -> Dict[str, Any]:
        """Get the tool's schema."""
        return {
            "name": self.name,
            "description": self.description,
            "required_params": self.required_params,
            "optional_params": {
                name: {
                    "type": param["type"].__name__,
                    "description": param.get("description", ""),
                    "default": param.get("default")
                }
                for name, param in self.optional_params.items()
            }
        }
    
    def format_error(self, error: Exception) -> str:
        """Format an error message."""
        return f"{self.name} error: {str(error)}" 