"""Public interface for workflow templates."""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Type

from pepperpy.core.base_manager import BaseManager
from pepperpy.core.errors import PepperPyError
from pepperpy.providers.base import BaseProvider
from pepperpy.registry.base import Registry


@dataclass
class Template:
    """Workflow template definition."""

    name: str
    description: str
    steps: List[Dict[str, Any]]
    metadata: Dict[str, Any] = field(default_factory=dict)


class TemplateProvider(BaseProvider):
    """Base class for template providers."""

    async def load_template(self, template_id: str) -> Template:
        """Load a template by ID.

        Args:
            template_id: Template identifier

        Returns:
            Loaded template

        Raises:
            PepperPyError: If template cannot be loaded
        """
        raise PepperPyError("Not implemented")

    async def save_template(self, template: Template) -> str:
        """Save a template.

        Args:
            template: Template to save

        Returns:
            Template identifier

        Raises:
            PepperPyError: If template cannot be saved
        """
        raise PepperPyError("Not implemented")

    async def list_templates(self) -> List[str]:
        """List available template IDs.

        Returns:
            List of template IDs

        Raises:
            PepperPyError: If templates cannot be listed
        """
        raise PepperPyError("Not implemented")


class TemplateManager(BaseManager[TemplateProvider]):
    """Manager for workflow templates."""

    def __init__(self):
        """Initialize the manager."""
        registry = Registry[Type[TemplateProvider]]("template_registry", "template")
        super().__init__("template_manager", "template", registry)

    async def load_template(
        self,
        template_id: str,
        provider_id: Optional[str] = None,
    ) -> Template:
        """Load a template by ID.

        Args:
            template_id: Template identifier
            provider_id: Optional provider to use

        Returns:
            Loaded template

        Raises:
            PepperPyError: If template cannot be loaded
        """
        provider = await self.get_provider(provider_id)
        return await provider.load_template(template_id)

    async def save_template(
        self,
        template: Template,
        provider_id: Optional[str] = None,
    ) -> str:
        """Save a template.

        Args:
            template: Template to save
            provider_id: Optional provider to use

        Returns:
            Template identifier

        Raises:
            PepperPyError: If template cannot be saved
        """
        provider = await self.get_provider(provider_id)
        return await provider.save_template(template)

    async def list_templates(
        self,
        provider_id: Optional[str] = None,
    ) -> List[str]:
        """List available template IDs.

        Args:
            provider_id: Optional provider to use

        Returns:
            List of template IDs

        Raises:
            PepperPyError: If templates cannot be listed
        """
        provider = await self.get_provider(provider_id)
        return await provider.list_templates()


# Export all public classes
__all__ = [
    "Template",
    "TemplateProvider",
    "TemplateManager",
]
