#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Registry for workflow templates.

This module provides a registry for workflow templates, allowing templates
to be registered, retrieved, and instantiated.
"""

from typing import Dict, List, Optional

from pepperpy.workflows.templates.types import (
    TemplateDefinition,
    TemplateInstance,
    TemplateType,
)


class TemplateRegistryError(Exception):
    """Exception raised when there is an error with the template registry."""

    pass


class WorkflowTemplateRegistry:
    """Registry for workflow templates.

    This class provides a registry for workflow templates, allowing templates
    to be registered, retrieved, and instantiated.
    """

    _templates: Dict[str, TemplateDefinition] = {}
    _template_instances: Dict[str, Dict[str, TemplateInstance]] = {}

    @classmethod
    def register_template(cls, template: TemplateDefinition) -> None:
        """Register a template.

        Args:
            template: The template to register.

        Raises:
            TemplateRegistryError: If a template with the same name already exists.
        """
        if template.name in cls._templates:
            raise TemplateRegistryError(f"Template already registered: {template.name}")

        cls._templates[template.name] = template

    @classmethod
    def unregister_template(cls, name: str) -> None:
        """Unregister a template.

        Args:
            name: The name of the template to unregister.

        Raises:
            TemplateRegistryError: If the template is not found.
        """
        if name not in cls._templates:
            raise TemplateRegistryError(f"Template not found: {name}")

        del cls._templates[name]
        if name in cls._template_instances:
            del cls._template_instances[name]

    @classmethod
    def get_template(cls, name: str) -> Optional[TemplateDefinition]:
        """Get a template by name.

        Args:
            name: The name of the template.

        Returns:
            The template, or None if not found.
        """
        return cls._templates.get(name)

    @classmethod
    def list_templates(cls) -> List[str]:
        """List all registered templates.

        Returns:
            A list of template names.
        """
        return list(cls._templates.keys())

    @classmethod
    def list_templates_by_type(cls, template_type: TemplateType) -> List[str]:
        """List all registered templates of a specific type.

        Args:
            template_type: The type of templates to list.

        Returns:
            A list of template names.
        """
        return [
            name
            for name, template in cls._templates.items()
            if template.type == template_type
        ]

    @classmethod
    def register_instance(cls, instance: TemplateInstance, instance_id: str) -> None:
        """Register a template instance.

        Args:
            instance: The template instance to register.
            instance_id: The ID of the instance.

        Raises:
            TemplateRegistryError: If an instance with the same ID already exists.
        """
        template_name = instance.template.name
        if template_name not in cls._template_instances:
            cls._template_instances[template_name] = {}

        if instance_id in cls._template_instances[template_name]:
            raise TemplateRegistryError(
                f"Instance already registered: {template_name}/{instance_id}"
            )

        cls._template_instances[template_name][instance_id] = instance

    @classmethod
    def get_instance(
        cls, template_name: str, instance_id: str
    ) -> Optional[TemplateInstance]:
        """Get a template instance by ID.

        Args:
            template_name: The name of the template.
            instance_id: The ID of the instance.

        Returns:
            The template instance, or None if not found.
        """
        if template_name not in cls._template_instances:
            return None

        return cls._template_instances[template_name].get(instance_id)

    @classmethod
    def list_instances(cls, template_name: str) -> List[str]:
        """List all instances of a template.

        Args:
            template_name: The name of the template.

        Returns:
            A list of instance IDs.
        """
        if template_name not in cls._template_instances:
            return []

        return list(cls._template_instances[template_name].keys())

    @classmethod
    def clear(cls) -> None:
        """Clear the registry."""
        cls._templates.clear()
        cls._template_instances.clear()
