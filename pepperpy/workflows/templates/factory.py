#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Factory para criação de templates de workflow.

Este módulo fornece factory functions para criar templates de workflow
com base em definições de template e parâmetros.
"""

from typing import Any, Dict, Type

from pepperpy.workflows.templates.base import WorkflowTemplate
from pepperpy.workflows.templates.implementation import (
    ContentProcessingTemplate,
    ConversationalTemplate,
    DataPipelineTemplate,
)
from pepperpy.workflows.templates.registry import WorkflowTemplateRegistry
from pepperpy.workflows.templates.types import TemplateType


class TemplateNotFoundError(Exception):
    """Erro lançado quando um template não é encontrado."""

    pass


class TemplateCreationError(Exception):
    """Erro lançado quando ocorre um erro na criação de um template."""

    pass


class TemplateFactory:
    """Factory para criação de templates de workflow.

    Esta classe fornece métodos factory para criar templates de workflow
    com base em definições de template e parâmetros.
    """

    _template_classes: Dict[str, Type[WorkflowTemplate]] = {}

    @classmethod
    def register_template_class(
        cls, template_type: str, template_class: Type[WorkflowTemplate]
    ) -> None:
        """Registra uma classe de template.

        Args:
            template_type: O tipo de template.
            template_class: A classe de template.
        """
        cls._template_classes[template_type] = template_class

    @classmethod
    def create_template(
        cls, template_name: str, parameters: Dict[str, Any]
    ) -> WorkflowTemplate:
        """Cria um template de workflow.

        Args:
            template_name: O nome do template.
            parameters: Os parâmetros do template.

        Returns:
            O template criado.

        Raises:
            TemplateNotFoundError: Se o template não for encontrado.
            TemplateCreationError: Se ocorrer um erro na criação do template.
        """
        template_def = WorkflowTemplateRegistry.get_template(template_name)
        if template_def is None:
            raise TemplateNotFoundError(f"Template '{template_name}' não encontrado")

        template_type = template_def.type.value
        if template_type not in cls._template_classes:
            # Usar factory functions específicas para tipos conhecidos
            if template_type == TemplateType.CONTENT_PROCESSING.value:
                return create_content_processing_template(template_name, parameters)
            elif template_type == TemplateType.CONVERSATIONAL.value:
                return create_conversational_template(template_name, parameters)
            elif template_type == TemplateType.DATA_PIPELINE.value:
                return create_data_pipeline_template(template_name, parameters)
            else:
                raise TemplateCreationError(
                    f"Tipo de template '{template_type}' não suportado"
                )

        try:
            template_class = cls._template_classes[template_type]
            return template_class(template_name, parameters)
        except Exception as e:
            raise TemplateCreationError(f"Erro ao criar template: {str(e)}")


def create_content_processing_template(
    name: str, parameters: Dict[str, Any]
) -> ContentProcessingTemplate:
    """Cria um template de processamento de conteúdo.

    Args:
        name: O nome do template.
        parameters: Os parâmetros do template.

    Returns:
        O template criado.
    """
    parameters["application_type"] = "content_processing"
    return ContentProcessingTemplate(name, parameters)


def create_conversational_template(
    name: str, parameters: Dict[str, Any]
) -> ConversationalTemplate:
    """Cria um template conversacional.

    Args:
        name: O nome do template.
        parameters: Os parâmetros do template.

    Returns:
        O template criado.
    """
    parameters["application_type"] = "conversational"
    return ConversationalTemplate(name, parameters)


def create_data_pipeline_template(
    name: str, parameters: Dict[str, Any]
) -> DataPipelineTemplate:
    """Cria um template de pipeline de dados.

    Args:
        name: O nome do template.
        parameters: Os parâmetros do template.

    Returns:
        O template criado.
    """
    parameters["application_type"] = "data_pipeline"
    return DataPipelineTemplate(name, parameters)


# Register template classes
TemplateFactory.register_template_class(
    TemplateType.CONTENT_PROCESSING.value, ContentProcessingTemplate
)
TemplateFactory.register_template_class(
    TemplateType.CONVERSATIONAL.value, ConversationalTemplate
)
TemplateFactory.register_template_class(
    TemplateType.DATA_PIPELINE.value, DataPipelineTemplate
)
