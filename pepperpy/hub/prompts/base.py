"""Base classes for prompt management.

This module provides base classes and utilities for managing AI prompts.
"""

from typing import Dict


class PromptRegistry:
    """Registry for managing and loading prompts."""

    _prompts: Dict[str, str] = {}

    @classmethod
    def register(cls, name: str, prompt: str) -> None:
        """Register a prompt.

        Args:
        ----
            name: Name to register the prompt under.
            prompt: The prompt template to register.

        """
        cls._prompts[name] = prompt

    @classmethod
    def get(cls, name: str) -> str:
        """Get a registered prompt by name.

        Args:
        ----
            name: Name of the prompt to get.

        Returns:
        -------
            The registered prompt template.

        Raises:
        ------
            KeyError: If no prompt is registered with the given name.

        """
        if name not in cls._prompts:
            raise KeyError(f"No prompt registered with name: {name}")
        return cls._prompts[name]

    @classmethod
    def format(cls, name: str, **kwargs) -> str:
        """Format a registered prompt with the given arguments.

        Args:
        ----
            name: Name of the prompt to format.
            **kwargs: Arguments to format the prompt with.

        Returns:
        -------
            The formatted prompt.

        Raises:
        ------
            KeyError: If no prompt is registered with the given name.

        """
        prompt = cls.get(name)
        return prompt.format(**kwargs)

    @classmethod
    def list(cls) -> Dict[str, str]:
        """List all registered prompts.

        Returns
        -------
            Dictionary of registered prompts.

        """
        return cls._prompts.copy()
