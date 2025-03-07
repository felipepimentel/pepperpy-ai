"""Template management for developer assistants."""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Union, cast

from pepperpy.core.assistant.types import TemplateCategory, TemplateMetadata

# Default templates directory
DEFAULT_TEMPLATES_DIR = Path(__file__).parent / "templates"


def get_template(
    template_name: str,
    category: Optional[Union[str, TemplateCategory]] = None,
    custom_path: Optional[str] = None,
) -> Dict[str, Any]:
    """Get a template by name.

    Args:
        template_name: Name of the template
        category: Optional category to filter by
        custom_path: Optional custom path to look for templates

    Returns:
        Template configuration

    Raises:
        ValueError: If the template is not found
    """
    # Normalize category if provided
    if category and isinstance(category, str):
        try:
            category = TemplateCategory(category)
        except ValueError:
            valid_categories = ", ".join([c.value for c in TemplateCategory])
            raise ValueError(
                f"Invalid template category: {category}. "
                f"Valid categories are: {valid_categories}"
            )

    # Get all templates
    templates = _load_templates(custom_path)

    # Filter by category if provided
    if category:
        templates = [
            t
            for t in templates
            if t.get("metadata", {}).get("category") == category.value
        ]

    # Find the template by name
    for template in templates:
        if template.get("name") == template_name:
            return template

    # If we get here, the template was not found
    raise ValueError(f"Template not found: {template_name}")


def list_templates(
    category: Optional[Union[str, TemplateCategory]] = None,
    custom_path: Optional[str] = None,
) -> List[TemplateMetadata]:
    """List available templates.

    Args:
        category: Optional category to filter by
        custom_path: Optional custom path to look for templates

    Returns:
        List of template metadata
    """
    # Normalize category if provided
    if category and isinstance(category, str):
        try:
            category = TemplateCategory(category)
        except ValueError:
            valid_categories = ", ".join([c.value for c in TemplateCategory])
            raise ValueError(
                f"Invalid template category: {category}. "
                f"Valid categories are: {valid_categories}"
            )

    # Get all templates
    templates = _load_templates(custom_path)

    # Extract metadata
    metadata_list = [cast(TemplateMetadata, t.get("metadata", {})) for t in templates]

    # Filter by category if provided
    if category:
        metadata_list = [
            m for m in metadata_list if m.get("category") == category.value
        ]

    return metadata_list


def _load_templates(custom_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """Load templates from the templates directory.

    Args:
        custom_path: Optional custom path to look for templates

    Returns:
        List of template configurations
    """
    # Determine the templates directory
    templates_dir = Path(custom_path) if custom_path else DEFAULT_TEMPLATES_DIR

    # Ensure the directory exists
    if not templates_dir.exists():
        return []

    # Load all template files
    templates = []
    for file_path in templates_dir.glob("**/*.json"):
        try:
            with open(file_path, "r") as f:
                template = json.load(f)
                templates.append(template)
        except (json.JSONDecodeError, IOError):
            # Skip invalid templates
            continue

    return templates
