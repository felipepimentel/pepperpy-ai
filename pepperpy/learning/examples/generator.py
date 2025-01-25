"""Example generator implementation."""

import logging
from typing import Any, Dict, List, Optional, Protocol, runtime_checkable

from pepperpy.core.utils.errors import PepperpyError
from pepperpy.core.lifecycle import Lifecycle


logger = logging.getLogger(__name__)


class ExampleGeneratorError(PepperpyError):
    """Example generator error."""
    pass


@runtime_checkable
class ExampleTemplate(Protocol):
    """Example template protocol."""
    
    def generate(self, **kwargs: Any) -> Any:
        """Generate example from template.
        
        Args:
            **kwargs: Template parameters
            
        Returns:
            Generated example
        """
        ...


class ExampleGenerator(Lifecycle):
    """Example generator implementation."""
    
    def __init__(
        self,
        name: str,
        config: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize example generator.
        
        Args:
            name: Generator name
            config: Optional generator configuration
        """
        super().__init__()
        self.name = name
        self._config = config or {}
        self._templates: Dict[str, ExampleTemplate] = {}
        
    @property
    def config(self) -> Dict[str, Any]:
        """Get generator configuration."""
        return self._config
        
    async def initialize(self) -> None:
        """Initialize generator."""
        try:
            # Load templates from configuration
            for name, config in self._config.get("templates", {}).items():
                self._templates[name] = await self._load_template(name, config)
                
        except Exception as e:
            logger.error(f"Failed to initialize example generator: {e}")
            raise ExampleGeneratorError(str(e))
            
    async def cleanup(self) -> None:
        """Clean up generator."""
        try:
            self._templates.clear()
            
        except Exception as e:
            logger.error(f"Failed to clean up example generator: {e}")
            raise ExampleGeneratorError(str(e))
            
    async def add_template(
        self,
        name: str,
        template: ExampleTemplate,
    ) -> None:
        """Add template to generator.
        
        Args:
            name: Template name
            template: Template implementation
            
        Raises:
            ExampleGeneratorError: If template addition fails
        """
        try:
            if not isinstance(template, ExampleTemplate):
                raise ValueError(f"Template must implement ExampleTemplate protocol")
                
            self._templates[name] = template
            
        except Exception as e:
            logger.error(f"Failed to add template: {e}")
            raise ExampleGeneratorError(str(e))
            
    async def get_template(
        self,
        name: str,
    ) -> Optional[ExampleTemplate]:
        """Get template by name.
        
        Args:
            name: Template name
            
        Returns:
            Template if found, None otherwise
            
        Raises:
            ExampleGeneratorError: If template retrieval fails
        """
        try:
            return self._templates.get(name)
            
        except Exception as e:
            logger.error(f"Failed to get template: {e}")
            raise ExampleGeneratorError(str(e))
            
    async def delete_template(
        self,
        name: str,
    ) -> None:
        """Delete template by name.
        
        Args:
            name: Template name
            
        Raises:
            ExampleGeneratorError: If template deletion fails
        """
        try:
            if name in self._templates:
                del self._templates[name]
                
        except Exception as e:
            logger.error(f"Failed to delete template: {e}")
            raise ExampleGeneratorError(str(e))
            
    async def generate_example(
        self,
        template_name: str,
        **kwargs: Any,
    ) -> Any:
        """Generate example from template.
        
        Args:
            template_name: Template name
            **kwargs: Template parameters
            
        Returns:
            Generated example
            
        Raises:
            ExampleGeneratorError: If example generation fails
        """
        try:
            template = await self.get_template(template_name)
            if not template:
                raise ValueError(f"Template not found: {template_name}")
                
            return template.generate(**kwargs)
            
        except Exception as e:
            logger.error(f"Failed to generate example: {e}")
            raise ExampleGeneratorError(str(e))
            
    async def _load_template(
        self,
        name: str,
        config: Dict[str, Any],
    ) -> ExampleTemplate:
        """Load template from configuration.
        
        Args:
            name: Template name
            config: Template configuration
            
        Returns:
            Template implementation
            
        Raises:
            ExampleGeneratorError: If template loading fails
        """
        raise NotImplementedError
        
    def validate(self) -> None:
        """Validate generator state."""
        super().validate()
        
        if not self.name:
            raise ValueError("Generator name cannot be empty") 