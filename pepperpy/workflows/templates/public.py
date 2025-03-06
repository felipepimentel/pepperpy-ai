#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Public API for workflow templates.

This module provides the public API for working with workflow templates,
including functions for creating, registering, and executing templates.
"""

from typing import Any, Dict, List, Optional, cast

from pepperpy.workflows.templates.factory import (
    TemplateFactory,
)
from pepperpy.workflows.templates.registry import WorkflowTemplateRegistry
from pepperpy.workflows.templates.types import (
    TemplateDefinition,
    TemplateInstance,
    TemplateParameter,
    TemplateParameterType,
    TemplateType,
)
from pepperpy.workflows.types import WorkflowResult


def register_template(
    name: str,
    template_type: TemplateType,
    description: str,
    parameters: List[TemplateParameter],
    metadata: Optional[Dict[str, Any]] = None,
) -> TemplateDefinition:
    """Register a workflow template.

    Args:
        name: The name of the template.
        template_type: The type of the template.
        description: A description of the template.
        parameters: The parameters of the template.
        metadata: Additional metadata for the template.

    Returns:
        The registered template definition.

    Raises:
        ValueError: If a template with the same name already exists.
    """
    template = TemplateDefinition(
        name, template_type, description, parameters, metadata or {}
    )
    try:
        WorkflowTemplateRegistry.register_template(template)
        return template
    except Exception as e:
        raise ValueError(f"Failed to register template: {e}")


def get_template(name: str) -> Optional[TemplateDefinition]:
    """Get a template by name.

    Args:
        name: The name of the template.

    Returns:
        The template, or None if not found.
    """
    return WorkflowTemplateRegistry.get_template(name)


def list_templates() -> List[str]:
    """List all registered templates.

    Returns:
        A list of template names.
    """
    return WorkflowTemplateRegistry.list_templates()


def list_templates_by_type(template_type: TemplateType) -> List[str]:
    """List all registered templates of a specific type.

    Args:
        template_type: The type of templates to list.

    Returns:
        A list of template names.
    """
    return WorkflowTemplateRegistry.list_templates_by_type(template_type)


def create_template_instance(
    template_name: str, parameters: Dict[str, Any]
) -> TemplateInstance:
    """Create an instance of a template.

    Args:
        template_name: The name of the template.
        parameters: The values for the template parameters.

    Returns:
        An instance of the template.

    Raises:
        ValueError: If the template is not found or the parameters are invalid.
    """
    template = get_template(template_name)
    if template is None:
        raise ValueError(f"Template not found: {template_name}")

    try:
        return TemplateInstance(template, parameters)
    except Exception as e:
        raise ValueError(f"Failed to create template instance: {e}")


async def execute_template(
    template_name: str, parameters: Dict[str, Any]
) -> WorkflowResult:
    """Execute a template.

    Args:
        template_name: The name of the template.
        parameters: The values for the template parameters.

    Returns:
        The result of the template execution.

    Raises:
        ValueError: If the template is not found or the parameters are invalid.
    """
    template = get_template(template_name)
    if template is None:
        raise ValueError(f"Template not found: {template_name}")

    try:
        template_instance = create_template_instance(template_name, parameters)
        workflow_template = TemplateFactory.create_template(
            template_name, template_instance.parameter_values
        )
        result = await workflow_template.execute(parameters)
        return cast(WorkflowResult, result)
    except Exception as e:
        raise ValueError(f"Failed to execute template: {e}")


def create_parameter(
    name: str,
    parameter_type: TemplateParameterType,
    description: str,
    required: bool = False,
    default: Optional[Any] = None,
    enum_values: Optional[List[str]] = None,
) -> TemplateParameter:
    """Create a template parameter.

    Args:
        name: The name of the parameter.
        parameter_type: The type of the parameter.
        description: A description of the parameter.
        required: Whether the parameter is required.
        default: The default value of the parameter.
        enum_values: Possible values for enum parameters.

    Returns:
        A template parameter.
    """
    return TemplateParameter(
        name=name,
        type=parameter_type,
        description=description,
        required=required,
        default=default,
        enum_values=enum_values,
    )
