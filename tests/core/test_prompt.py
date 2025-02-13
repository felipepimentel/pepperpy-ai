"""Tests for the prompt template system."""

from typing import Any, AsyncGenerator, Dict

import pytest

from pepperpy.core.errors import ValidationError
from pepperpy.core.prompt.template import (
    BaseTemplate,
    PromptTemplate,
    create_prompt_template,
    register_template,
)


@register_template("test")
class TestTemplate(BaseTemplate):
    """Test implementation of BaseTemplate."""

    def __init__(self, config: Dict[str, Any]) -> None:
        """Initialize the template."""
        super().__init__(config)

    async def initialize(self) -> None:
        """Initialize the template."""
        pass

    async def cleanup(self) -> None:
        """Clean up template resources."""
        pass

    async def render(self, variables: Dict[str, Any]) -> str:
        """Test implementation of render."""
        return f"Test prompt with {variables.get('variable', 'default')}"


@pytest.fixture
def template_config() -> Dict[str, Any]:
    """Create a test template configuration."""
    return {
        "type": "test",
        "template": "Test prompt with {{ variable }}",
        "variables": ["variable"],
        "required_variables": ["variable"],
    }


@pytest.fixture
async def template(
    template_config: Dict[str, Any],
) -> AsyncGenerator[PromptTemplate, None]:
    """Create a test template."""
    template = await create_prompt_template(template_config)
    await template.initialize()
    yield template
    await template.cleanup()


@pytest.mark.asyncio
async def test_template_creation(template_config: Dict[str, Any]):
    """Test template creation."""
    template = await create_prompt_template(template_config)
    assert isinstance(template, TestTemplate)
    await template.cleanup()


@pytest.mark.asyncio
async def test_template_missing_type():
    """Test template creation with missing type."""
    with pytest.raises(ValidationError) as exc_info:
        await create_prompt_template({})
    assert "Missing required field: type" in str(exc_info.value)


@pytest.mark.asyncio
async def test_template_unknown_type():
    """Test template creation with unknown type."""
    with pytest.raises(ValidationError) as exc_info:
        await create_prompt_template({"type": "unknown"})
    assert "Unknown template type: unknown" in str(exc_info.value)


@pytest.mark.asyncio
async def test_template_render(template: PromptTemplate):
    """Test template rendering."""
    result = await template.render({"variable": "test"})
    assert result == "Test prompt with test"

    # Test with default value
    result = await template.render({})
    assert result == "Test prompt with default"


@pytest.mark.asyncio
async def test_template_lifecycle(template_config: Dict[str, Any]):
    """Test template lifecycle."""
    # Create and initialize
    template = await create_prompt_template(template_config)
    await template.initialize()

    # Use template
    result = await template.render({"variable": "test"})
    assert result == "Test prompt with test"

    # Cleanup
    await template.cleanup()
