#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Tipos para o domínio de templates de workflow.

Este módulo define os tipos utilizados no domínio de templates de workflow,
incluindo enums, dataclasses e classes de registro.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class TemplateType(Enum):
    """Tipos de templates de workflow."""

    CONTENT_PROCESSING = "content_processing"
    CONVERSATIONAL = "conversational"
    DATA_PIPELINE = "data_pipeline"
    INTEGRATION = "integration"
    CUSTOM = "custom"


class TemplateParameterType(Enum):
    """Tipos de parâmetros de template."""

    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    OBJECT = "object"
    ARRAY = "array"
    ENUM = "enum"


@dataclass
class TemplateParameter:
    """Definição de um parâmetro de template.

    Attributes:
        name: O nome do parâmetro.
        type: O tipo do parâmetro.
        description: Uma descrição do parâmetro.
        required: Se o parâmetro é obrigatório.
        default: O valor padrão do parâmetro.
        enum_values: Valores possíveis para parâmetros do tipo enum.
    """

    name: str
    type: TemplateParameterType
    description: str
    required: bool = False
    default: Optional[Any] = None
    enum_values: Optional[List[str]] = None


@dataclass
class TemplateDefinition:
    """Definição de um template de workflow.

    Attributes:
        name: O nome do template.
        type: O tipo do template.
        description: Uma descrição do template.
        parameters: Os parâmetros do template.
        metadata: Metadados adicionais para o template.
    """

    name: str
    type: TemplateType
    description: str
    parameters: List[TemplateParameter]
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TemplateInstance:
    """Instância de um template.

    Uma instância de template representa um template com valores de parâmetros
    específicos, pronto para ser executado.

    Attributes:
        template: A definição do template.
        parameter_values: Os valores dos parâmetros.
        metadata: Metadados adicionais para a instância.
    """

    template: TemplateDefinition
    parameter_values: Dict[str, Any]
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Inicializa a instância do template."""
        # Validar parâmetros obrigatórios
        missing_params = []
        for param in self.template.parameters:
            if param.required and param.name not in self.parameter_values:
                missing_params.append(param.name)

        if missing_params:
            raise ValueError(
                f"Missing required parameters: {', '.join(missing_params)}"
            )


class TemplateRegistry:
    """Registry for workflow templates.

    This class provides a registry for workflow templates, allowing templates
    to be registered, retrieved, and instantiated.
    """

    _templates: Dict[str, TemplateDefinition] = {}

    @classmethod
    def register_template(cls, template: TemplateDefinition) -> None:
        """Register a template.

        Args:
            template: The template to register.
        """
        cls._templates[template.name] = template

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
    def create_instance(
        cls, name: str, parameter_values: Dict[str, Any]
    ) -> TemplateInstance:
        """Create an instance of a template.

        Args:
            name: The name of the template.
            parameter_values: The values for the template parameters.

        Returns:
            An instance of the template.

        Raises:
            ValueError: If the template is not found.
        """
        template = cls.get_template(name)
        if template is None:
            raise ValueError(f"Template not found: {name}")

        return TemplateInstance(template, parameter_values)
