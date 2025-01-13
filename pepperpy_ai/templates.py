"""Template module."""

import re
from collections.abc import Callable
from typing import TypedDict


class TemplateVariables(TypedDict, total=False):
    """Type hints for template variables."""
    model: str
    temperature: float
    max_tokens: int
    top_p: float
    frequency_penalty: float
    presence_penalty: float
    stop: list[str]
    n: int
    stream: bool
    logprobs: int | None
    echo: bool
    best_of: int
    logit_bias: dict[str, float]
    user: str
    suffix: str | None
    timeout: float
    api_key: str
    api_base: str
    api_version: str
    organization_id: str


class TemplateParams(TypedDict, total=False):
    """Template parameters."""

    model: str | None
    temperature: float | None
    max_tokens: int | None
    top_p: float | None
    frequency_penalty: float | None
    presence_penalty: float | None
    timeout: float | None


class PromptTemplate:
    """Prompt template implementation."""

    def __init__(
        self,
        template: str,
        description: str | None = None,
        validators: dict[str, type | Callable[[str], bool]] | None = None,
    ) -> None:
        """Initialize template.

        Args:
            template: Template string.
            description: Template description.
            validators: Variable validators.
        """
        self.template = template
        self.description = description
        self.validators = validators or {}
        self._variables = self._extract_variables(template)

    def _extract_variables(self, template: str) -> set[str]:
        """Extract variable names from template.

        Args:
            template: Template string.

        Returns:
            set[str]: Set of variable names.
        """
        pattern = r"\{([^}]+)\}"
        matches = re.findall(pattern, template)
        return set(matches)

    def validate_variables(self, **kwargs: TemplateVariables) -> None:
        """Validate provided variables against template requirements.

        Args:
            **kwargs: Variables to validate.

        Raises:
            ValueError: If required variables are missing or validation fails.
        """
        missing = self._variables - set(kwargs.keys())
        if missing:
            raise ValueError(f"Missing required variables: {', '.join(missing)}")

        for var, value in kwargs.items():
            if var in self.validators:
                validator = self.validators[var]
                if isinstance(validator, type):
                    if not isinstance(value, validator):
                        raise ValueError(
                            f"Variable '{var}' must be of type {validator.__name__}"
                        )
                else:
                    if not validator(value):
                        raise ValueError(f"Variable '{var}' failed validation")

    def format(self, **kwargs: TemplateVariables) -> str:
        """Format template with provided variables.

        Args:
            **kwargs: Variables to format template with.

        Returns:
            str: Formatted template.

        Raises:
            ValueError: If required variables are missing or validation fails.
        """
        self.validate_variables(**kwargs)
        return self.template.format(**kwargs)
