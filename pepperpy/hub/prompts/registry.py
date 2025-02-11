"""Prompt registry for managing and formatting prompt templates."""

from pathlib import Path
from typing import Any, Dict, List, Union

from structlog import get_logger

logger = get_logger()


class PromptRegistry:
    """Registry for managing and formatting prompt templates."""

    def __init__(self):
        """Initialize the prompt registry."""
        self._prompts: Dict[str, str] = {}

    def register_prompt(
        self,
        prompt_id: str,
        template_or_path: Union[str, Path],
    ) -> None:
        """Register a prompt template or load from path.

        Args:
            prompt_id: ID to register the prompt under
            template_or_path: The template string or path to template file

        """
        if isinstance(template_or_path, str):
            self._prompts[prompt_id] = template_or_path
        else:
            # Load from file
            with open(template_or_path, "r", encoding="utf-8") as f:
                self._prompts[prompt_id] = f.read()

    def load_prompt(self, prompt_id: str, **kwargs: Any) -> str:
        """Load and format a prompt template.

        Args:
            prompt_id: ID of the prompt to load
            **kwargs: Format arguments for the template

        Returns:
            The formatted prompt string

        Raises:
            ValueError: If the prompt is not found

        """
        if prompt_id not in self._prompts:
            raise ValueError(f"Prompt '{prompt_id}' not found")

        return self.format_prompt(self._prompts[prompt_id], **kwargs)

    def format_prompt(self, template: str, **kwargs: Any) -> str:
        """Format a prompt template with the given arguments.

        Args:
            template: The prompt template string
            **kwargs: Format arguments for the template

        Returns:
            The formatted prompt string

        """
        try:
            return template.format(**kwargs)
        except KeyError as e:
            logger.error(
                "Missing required argument for prompt template",
                missing_key=str(e),
            )
            raise
        except Exception as e:
            logger.error(
                "Failed to format prompt template",
                error=str(e),
            )
            raise

    def has_prompt(self, prompt_id: str) -> bool:
        """Check if a prompt is registered.

        Args:
            prompt_id: ID of the prompt to check

        Returns:
            True if the prompt is registered, False otherwise

        """
        return prompt_id in self._prompts

    def list_prompts(self) -> List[str]:
        """Get a list of all registered prompt IDs.

        Returns:
            List of registered prompt IDs

        """
        return list(self._prompts.keys())
