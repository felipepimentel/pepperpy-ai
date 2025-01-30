"""Tests for prompt template functionality."""

import pytest
from pathlib import Path
from typing import Dict, Any

from pepperpy.prompts.template import (
    PromptTemplate,
    PromptMetadata,
    PromptContext,
    PromptValidation,
)


@pytest.fixture
def sample_template() -> Dict[str, Any]:
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
        "template": "Hello {{name}}!",
        "validation": {
            "required_fields": ["name"],
            "constraints": {"max_length": 100},
        },
    }


def test_prompt_template_creation(sample_template: Dict[str, Any]) -> None:
    """Test creating a PromptTemplate instance."""
    metadata = PromptMetadata(**sample_template["metadata"])
    context = PromptContext(**sample_template["context"])
    validation = PromptValidation(**sample_template["validation"])

    template = PromptTemplate(
        template=sample_template["template"],
        metadata=metadata,
        context=context,
        validation=validation,
    )

    assert template.template == "Hello {{name}}!"
    assert template.metadata.name == "test_prompt"
    assert template.context.description == "Test prompt"
    assert template.validation.required_fields == ["name"]


def test_prompt_template_format(sample_template: Dict[str, Any]) -> None:
    """Test formatting a prompt template."""
    template = PromptTemplate(
        template=sample_template["template"],
        metadata=PromptMetadata(**sample_template["metadata"]),
        context=PromptContext(**sample_template["context"]),
        validation=PromptValidation(**sample_template["validation"]),
    )

    result = template.format(name="World")
    assert result == "Hello World!"


def test_prompt_template_missing_required_field(
    sample_template: Dict[str, Any]
) -> None:
    """Test formatting with missing required field."""
    template = PromptTemplate(
        template=sample_template["template"],
        metadata=PromptMetadata(**sample_template["metadata"]),
        context=PromptContext(**sample_template["context"]),
        validation=PromptValidation(**sample_template["validation"]),
    )

    with pytest.raises(ValueError, match="Missing required fields"):
        template.format()


def test_prompt_template_max_length_constraint(
    sample_template: Dict[str, Any]
) -> None:
    """Test max length constraint validation."""
    template = PromptTemplate(
        template=sample_template["template"],
        metadata=PromptMetadata(**sample_template["metadata"]),
        context=PromptContext(**sample_template["context"]),
        validation=PromptValidation(**sample_template["validation"]),
    )

    with pytest.raises(ValueError, match="exceeds max length"):
        template.format(name="x" * 101)


@pytest.mark.asyncio
async def test_prompt_template_execute(
    sample_template: Dict[str, Any],
    mocker: Any,
) -> None:
    """Test executing a prompt template with a provider."""
    mock_provider = mocker.AsyncMock()
    mock_provider.generate.return_value = "Generated response"

    template = PromptTemplate(
        template=sample_template["template"],
        metadata=PromptMetadata(**sample_template["metadata"]),
        context=PromptContext(**sample_template["context"]),
        validation=PromptValidation(**sample_template["validation"]),
    )

    result = await template.execute(mock_provider, name="World")

    assert result == "Generated response"
    mock_provider.generate.assert_called_once_with(
        "Hello World!",
        model="gpt-4",
        temperature=0.7,
    ) 