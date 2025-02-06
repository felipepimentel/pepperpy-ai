"""Test cases for the prompt template module."""

# Standard library imports
from typing import Any
from unittest.mock import Mock

# Third-party imports
import pytest
from jinja2 import UndefinedError
from pydantic import ValidationError

# Local imports
from pepperpy.core.templates.prompt import PromptTemplate
from pepperpy.providers.provider import Provider


@pytest.fixture
def sample_template() -> dict[str, Any]:
    """Create a sample template configuration."""
    return {
        "metadata": {
            "name": "test_prompt",
            "version": "1.0",
            "category": "test",
            "model": "gpt-4",
            "temperature": 0.7,
            "tags": ["test"],
        },
        "context": {
            "description": "Test prompt",
            "input_format": "Test input",
            "output_format": "Test output",
            "examples": [
                {
                    "input": "test input",
                    "output": "test output",
                }
            ],
        },
        "template": "Hello {{ name }}!",
        "validation": {
            "required_fields": ["name"],
            "constraints": {"max_length": 100},
        },
    }


def test_prompt_template_creation(sample_template: dict[str, Any]) -> None:
    """Test creating a PromptTemplate instance."""
    template = PromptTemplate(
        template=sample_template["template"], variables={"name": "test"}
    )

    assert template.template == "Hello {{ name }}!"
    assert template.variables == {"name": "test"}


def test_prompt_template_render() -> None:
    """Test rendering a template with variables."""
    template = PromptTemplate(template="Hello {{ name }}!", variables={"name": "test"})

    result = template.render({})
    assert result == "Hello test!"

    result = template.render({"name": "world"})
    assert result == "Hello world!"


def test_prompt_template_render_with_filters() -> None:
    """Test rendering a template with Jinja2 filters."""
    template = PromptTemplate(
        template="Hello {{ name | upper }}!", variables={"name": "test"}
    )

    result = template.render({})
    assert result == "Hello TEST!"


def test_prompt_template_validation() -> None:
    """Test prompt template validation."""
    template = PromptTemplate(
        template="Hello {{name}}",
        variables={"name": None},
    )
    with pytest.raises(ValidationError):
        template.model_validate({"name": None})


@pytest.mark.asyncio
async def test_prompt_template_execute() -> None:
    """Test executing a template with a provider."""
    mock_provider = Mock(spec=Provider)
    mock_provider.complete.return_value = "Hello test!"

    template = PromptTemplate(
        template="Hello {{ name }}!",
        variables={"name": "test", "model": "test-model", "temperature": 0.7},
    )

    result = await template.execute(mock_provider)
    assert result == "Hello test!"
    mock_provider.complete.assert_called_once_with(
        "Hello test!", stream=False, model="test-model", temperature=0.7
    )


def test_prompt_template_basic():
    """Test basic prompt template functionality."""
    template = PromptTemplate(template="Hello {name}!")
    result = template.render({"name": "World"})
    assert result == "Hello World!"


def test_prompt_template_missing_variable():
    """Test prompt template with missing variable."""
    template = PromptTemplate(template="Hello {name}!")
    with pytest.raises(
        UndefinedError
    ):  # Jinja2's specific error for undefined variables
        template.render({"wrong_name": "World"})


def test_prompt_template_extra_variable():
    """Test prompt template with extra variable."""
    template = PromptTemplate(template="Hello {name}!")
    result = template.render({"name": "World", "extra": "ignored"})
    assert result == "Hello World!"


def test_prompt_template_multiple_variables():
    """Test prompt template with multiple variables."""
    template = PromptTemplate(template="Hello {first} {last}!")
    result = template.render({"first": "John", "last": "Doe"})
    assert result == "Hello John Doe!"


def test_prompt_template_repeated_variable():
    """Test prompt template with repeated variable."""
    template = PromptTemplate(template="{name}, {name}!")
    result = template.render({"name": "Echo"})
    assert result == "Echo, Echo!"
