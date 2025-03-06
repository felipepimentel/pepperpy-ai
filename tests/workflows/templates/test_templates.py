"""Testes para o domínio de templates de workflow.

Este módulo contém testes para o domínio de templates de workflow, incluindo
testes para registro, recuperação e execução de templates.
"""

from unittest.mock import AsyncMock, patch

import pytest

from pepperpy.workflows.templates.public import (
    create_parameter,
    execute_template,
    get_template,
    list_templates,
    register_template,
)
from pepperpy.workflows.templates.types import (
    TemplateDefinition,
    TemplateParameterType,
    TemplateType,
)
from pepperpy.workflows.types import WorkflowResult


class TestRegisterTemplate:
    """Testes para a função register_template."""

    def test_register_template_creates_template(self):
        """Teste que register_template cria um template."""
        # Mock para o registro de templates
        with patch(
            "pepperpy.workflows.templates.public.register_template"
        ) as mock_register:
            mock_register.return_value = TemplateDefinition(
                name="test_template",
                type=TemplateType.CONTENT_PROCESSING,
                description="Test template",
                parameters=[],
            )

            template = register_template(
                name="test_template",
                template_type=TemplateType.CONTENT_PROCESSING,
                description="Test template",
                parameters=[],
            )

            assert template is not None
            assert template.name == "test_template"
            assert template.type == TemplateType.CONTENT_PROCESSING
            assert template.description == "Test template"


class TestGetTemplate:
    """Testes para a função get_template."""

    def test_get_template_returns_template(self):
        """Teste que get_template retorna um template."""
        # Mock para a recuperação de templates
        with patch("pepperpy.workflows.templates.public.get_template") as mock_get:
            mock_get.return_value = TemplateDefinition(
                name="test_template",
                type=TemplateType.CONTENT_PROCESSING,
                description="Test template",
                parameters=[],
            )

            template = get_template("test_template")

            assert template is not None
            assert template.name == "test_template"
            assert template.type == TemplateType.CONTENT_PROCESSING
            assert template.description == "Test template"


class TestListTemplates:
    """Testes para a função list_templates."""

    def test_list_templates_returns_template_names(self):
        """Teste que list_templates retorna nomes de templates."""
        # Mock para a listagem de templates
        with patch("pepperpy.workflows.templates.public.list_templates") as mock_list:
            mock_list.return_value = ["template1", "template2", "template3"]

            templates = list_templates()

            assert templates is not None
            assert len(templates) == 3
            assert "template1" in templates
            assert "template2" in templates
            assert "template3" in templates


class TestExecuteTemplate:
    """Testes para a função execute_template."""

    @pytest.mark.asyncio
    async def test_execute_template_runs_template(self):
        """Teste que execute_template executa um template."""
        # Mock para a execução de templates
        with patch(
            "pepperpy.workflows.templates.public.execute_template",
            new_callable=AsyncMock,
        ) as mock_execute:
            mock_execute.return_value = WorkflowResult(
                status="success",
                result={"output": "test_output.mp3"},
                metadata={"duration": 120},
            )

            result = await execute_template(
                "podcast_template",
                {
                    "source_url": "https://example.com/rss",
                    "output_path": "test_output.mp3",
                },
            )

            assert result is not None
            assert result.status == "success"
            assert result.result["output"] == "test_output.mp3"
            assert result.metadata["duration"] == 120


class TestCreateParameter:
    """Testes para a função create_parameter."""

    def test_create_parameter_creates_parameter(self):
        """Teste que create_parameter cria um parâmetro de template."""
        parameter = create_parameter(
            name="source_url",
            parameter_type=TemplateParameterType.STRING,
            description="URL da fonte de dados",
            required=True,
        )

        assert parameter is not None
        assert parameter.name == "source_url"
        assert parameter.type == TemplateParameterType.STRING
        assert parameter.description == "URL da fonte de dados"
        assert parameter.required is True
