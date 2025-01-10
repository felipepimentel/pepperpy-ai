"""Prompt template system"""

from string import Formatter
from typing import Any


class PromptTemplate:
    """Template for generating prompts with variables"""

    def __init__(
        self,
        template: str,
        validator: dict[str, Any] | None = None,
        description: str | None = None,
    ):
        self.template = template
        self.validator = validator
        self.description = description
        self._variables = self._extract_variables()

    def _extract_variables(self) -> set[str]:
        """Extract variable names from template"""
        return {
            fname
            for _, fname, _, _ in Formatter().parse(self.template)
            if fname is not None
        }

    def validate_variables(self, **kwargs: Any) -> None:
        """Validate provided variables against template requirements"""
        missing = self._variables - set(kwargs.keys())
        if missing:
            raise ValueError(f"Missing required variables: {missing}")

        if self.validator:
            for var, value in kwargs.items():
                if var in self.validator:
                    validator = self.validator[var]
                    if isinstance(validator, type):
                        if not isinstance(value, validator):
                            raise TypeError(
                                f"Variable '{var}' must be of type {validator.__name__}",
                            )
                    elif callable(validator):
                        if not validator(value):
                            raise ValueError(f"Variable '{var}' failed validation")

    def format(self, **kwargs: Any) -> str:
        """Format template with provided variables"""
        self.validate_variables(**kwargs)
        return self.template.format(**kwargs)

    @classmethod
    def from_file(cls, path: str) -> "PromptTemplate":
        """Load template from file"""
        with open(path, encoding="utf-8") as f:
            return cls(f.read())


class TemplateRegistry:
    """Central registry for prompt templates"""

    _templates: dict[str, PromptTemplate] = {}

    @classmethod
    def register(cls, name: str, template: PromptTemplate) -> None:
        """Register new template"""
        cls._templates[name] = template

    @classmethod
    def get(cls, name: str) -> PromptTemplate | None:
        """Get template by name"""
        return cls._templates.get(name)

    @classmethod
    def list_templates(cls) -> dict[str, str]:
        """List all registered templates with descriptions"""
        return {
            name: template.description or "No description"
            for name, template in cls._templates.items()
        }


def load_template(
    name: str, variables: dict[str, Any] | None = None, language: str | None = None
) -> str:
    """Load template."""
    if not name:
        raise ValueError("Template name is required")
    return ""  # Add your implementation here
