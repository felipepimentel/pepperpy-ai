"""Assistant builder module."""

from typing import Dict, Optional

from pepperpy.core.base import BaseBuilder


class AssistantBuilder(BaseBuilder):
    """Builder for creating assistants."""

    def __init__(self, pepper: "PepperPy", name: Optional[str] = None) -> None:
        """Initialize assistant builder.

        Args:
            pepper: PepperPy instance
            name: Optional assistant name
        """
        super().__init__()
        self.pepper = pepper
        self.name = name or "assistant"
        self._llm_options: Dict = {}
        self._rag_options: Dict = {}
        self._github_options: Dict = {}

    def with_llm(self, **options: Dict) -> "AssistantBuilder":
        """Configure LLM component.

        Args:
            **options: LLM configuration options

        Returns:
            Self for chaining
        """
        self._llm_options.update(options)
        return self

    def with_rag(
        self, collection_name: str, persist_directory: str, **options: Dict
    ) -> "AssistantBuilder":
        """Configure RAG component.

        Args:
            collection_name: Name of the collection
            persist_directory: Directory to persist data
            **options: Additional RAG configuration options

        Returns:
            Self for chaining
        """
        self._rag_options.update(options)
        self._rag_options["collection_name"] = collection_name
        self._rag_options["persist_directory"] = persist_directory
        return self

    def with_github(self, **options: Dict) -> "AssistantBuilder":
        """Configure GitHub component.

        Args:
            **options: GitHub configuration options

        Returns:
            Self for chaining
        """
        self._github_options.update(options)
        return self

    def build(self) -> "RepositoryAssistant":
        """Build the assistant.

        Returns:
            Configured assistant instance
        """
        from pepperpy.assistants.repository import RepositoryAssistant

        # Configure components
        if self._llm_options:
            self.pepper.llm.configure(**self._llm_options)

        if self._rag_options:
            collection_name = self._rag_options.pop("collection_name")
            persist_directory = self._rag_options.pop("persist_directory")
            self.pepper.rag.configure(
                collection_name=collection_name,
                persist_directory=persist_directory,
                **self._rag_options,
            )

        if self._github_options:
            self.pepper.github.configure(**self._github_options)

        # Create assistant
        return RepositoryAssistant(
            name=self.name,
            llm=self.pepper.llm,
            rag=self.pepper.rag,
            github=self.pepper.github,
        )
