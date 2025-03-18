"""Testes para o domínio de templates de workflow.

Este módulo contém testes para o domínio de templates de workflow, incluindo
testes para registro, recuperação e execução de templates.
"""

from unittest.mock import AsyncMock, patch

import pytest

from pepperpy.workflows.public import (
    create_parameter,
    execute_template,
    get_template,
    list_templates,
    register_template,
)
from pepperpy.workflows.types import (
    TemplateDefinition,
    TemplateParameter,
    TemplateParameterType,
)


class TestRegisterTemplate:
    """Testes para a função register_template."""

    def test_register_template_creates_template(self):
        """Teste que register_template cria um template."""
        # Mock para o registro de templates
        with patch(
            "pepperpy.workflows.public._template_registry.register"
        ) as mock_register:
            # Create a template definition
            template = TemplateDefinition(
                name="test_template",
                description="Test template",
                parameters=[],
                steps=[],
            )

            # Register the template
            register_template(template)

            # Assert that the template was registered
            mock_register.assert_called_once()
            assert mock_register.call_args[0][0].name == "test_template"
            assert mock_register.call_args[0][0].description == "Test template"


class TestGetTemplate:
    """Testes para a função get_template."""

    def test_get_template_returns_template(self):
        """Teste que get_template retorna um template."""
        # Mock para a recuperação de templates
        with patch("pepperpy.workflows.public._template_registry.get") as mock_get:
            # Setup the mock to return a template
            mock_get.return_value = mock_template = AsyncMock()
            mock_template.name = "test_template"
            mock_template.description = "Test template"
            mock_template.steps = []
            mock_template.metadata = {"parameters": []}

            # Get the template
            template = get_template("test_template")

            # Assert that the template was returned
            assert template is not None
            assert template.name == "test_template"
            assert template.description == "Test template"


class TestListTemplates:
    """Testes para a função list_templates."""

    def test_list_templates_returns_template_names(self):
        """Teste que list_templates retorna nomes de templates."""
        # Mock para a listagem de templates
        with patch("pepperpy.workflows.public._template_registry.list") as mock_list:
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
        # Mock para a recuperação e execução de templates
        with patch("pepperpy.workflows.public.get_template") as mock_get:
            # Setup the mock to return a template
            template = TemplateDefinition(
                name="podcast_template",
                description="Podcast template",
                parameters=[
                    TemplateParameter(
                        name="source_url",
                        description="URL da fonte de dados",
                        type=TemplateParameterType.STRING,
                        required=True,
                    ),
                    TemplateParameter(
                        name="output_path",
                        description="Caminho de saída",
                        type=TemplateParameterType.STRING,
                        required=True,
                    ),
                ],
                steps=[],
            )
            mock_get.return_value = template

            # Execute the template
            result = await execute_template(
                "podcast_template",
                {
                    "source_url": "https://example.com/rss",
                    "output_path": "test_output.mp3",
                },
            )

            # Assert that the result was returned
            assert result is not None
            assert result["status"] == "success"
            assert result["template"] == "podcast_template"
            assert result["parameters"]["source_url"] == "https://example.com/rss"
            assert result["parameters"]["output_path"] == "test_output.mp3"


class TestCreateParameter:
    """Testes para a função create_parameter."""

    def test_create_parameter_creates_parameter(self):
        """Teste que create_parameter cria um parâmetro de template."""
        parameter = create_parameter(
            name="source_url",
            description="URL da fonte de dados",
            param_type=TemplateParameterType.STRING,
            required=True,
        )

        assert parameter is not None
        assert parameter.name == "source_url"
        assert parameter.type == TemplateParameterType.STRING
        assert parameter.description == "URL da fonte de dados"
        assert parameter.required is True
