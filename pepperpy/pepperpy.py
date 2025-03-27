"""Main PepperPy module.

This module provides the main PepperPy class with a fluent API for
interacting with the framework's components.
"""

import json
import os
from typing import Any, Dict, List, Optional, Union

from pepperpy.core.config import Config
from pepperpy.embeddings.base import EmbeddingProvider
from pepperpy.llm.base import GenerationResult, LLMProvider, Message, MessageRole
from pepperpy.rag.base import Document, Query, RAGProvider
from pepperpy.storage.base import StorageProvider
from pepperpy.tools.repository.base import RepositoryProvider
from pepperpy.tts.base import TTSProvider
from pepperpy.workflow.base import WorkflowProvider


class PepperPy:
    """Main PepperPy class with fluent API."""

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        """Initialize PepperPy.

        Args:
            config: Optional configuration dictionary
        """
        self.config = Config(config)
        self._llm: Optional[LLMProvider] = None
        self._rag: Optional[RAGProvider] = None
        self._storage: Optional[StorageProvider] = None
        self._tts: Optional[TTSProvider] = None
        self._repository: Optional[RepositoryProvider] = None
        self._workflow: Optional[WorkflowProvider] = None
        self._embeddings: Optional[EmbeddingProvider] = None

    def with_llm(
        self, provider_type: Optional[str] = None, **kwargs: Any
    ) -> "PepperPy":
        """Configure LLM provider.

        Args:
            provider_type: Type of LLM provider (defaults to PEPPERPY_LLM__PROVIDER)
            **kwargs: Additional provider options

        Returns:
            Self for chaining
        """
        provider_type = provider_type or os.getenv("PEPPERPY_LLM__PROVIDER", "openai")
        self._llm = self.config.load_llm_provider(provider_type=provider_type, **kwargs)
        return self

    def with_embeddings(
        self, provider_type: Optional[str] = None, **kwargs: Any
    ) -> "PepperPy":
        """Configure embeddings provider.

        Args:
            provider_type: Type of embeddings provider (defaults to PEPPERPY_EMBEDDINGS__PROVIDER)
            **kwargs: Additional provider options

        Returns:
            Self for chaining
        """
        provider_type = provider_type or os.getenv(
            "PEPPERPY_EMBEDDINGS__PROVIDER", "local"
        )
        self._embeddings = self.config.load_embeddings_provider(
            provider_type=provider_type, **kwargs
        )
        return self

    def with_rag(
        self, provider_type: Optional[str] = None, **kwargs: Any
    ) -> "PepperPy":
        """Configure RAG provider.

        Args:
            provider_type: Type of RAG provider (defaults to PEPPERPY_RAG__PROVIDER)
            **kwargs: Additional provider options

        Returns:
            Self for chaining
        """
        provider_type = provider_type or os.getenv("PEPPERPY_RAG__PROVIDER", "chroma")
        if not self._embeddings:
            self.with_embeddings()  # Use default embeddings provider
        kwargs["embedding_function"] = self._embeddings.get_embedding_function()
        self._rag = self.config.load_rag_provider(provider_type=provider_type, **kwargs)
        return self

    def with_storage(
        self, provider_type: Optional[str] = None, **kwargs: Any
    ) -> "PepperPy":
        """Configure storage provider.

        Args:
            provider_type: Type of storage provider (defaults to PEPPERPY_STORAGE__PROVIDER)
            **kwargs: Additional provider options

        Returns:
            Self for chaining
        """
        provider_type = provider_type or os.getenv(
            "PEPPERPY_STORAGE__PROVIDER", "local"
        )
        self._storage = self.config.load_storage_provider(
            provider_type=provider_type, **kwargs
        )
        return self

    def with_tts(
        self, provider_type: Optional[str] = None, **kwargs: Any
    ) -> "PepperPy":
        """Configure TTS provider.

        Args:
            provider_type: Type of TTS provider (defaults to PEPPERPY_TTS__PROVIDER)
            **kwargs: Additional provider options

        Returns:
            Self for chaining
        """
        provider_type = provider_type or os.getenv("PEPPERPY_TTS__PROVIDER", "azure")
        self._tts = self.config.load_tts_provider(provider_type=provider_type, **kwargs)
        return self

    def with_repository(
        self, provider_type: Optional[str] = None, **kwargs: Any
    ) -> "PepperPy":
        """Configure repository provider.

        Args:
            provider_type: Type of repository provider (defaults to PEPPERPY_REPOSITORY__PROVIDER)
            **kwargs: Additional provider options

        Returns:
            Self for chaining
        """
        provider_type = provider_type or os.getenv(
            "PEPPERPY_REPOSITORY__PROVIDER", "github"
        )
        self._repository = self.config.load_repository_provider(
            provider_type=provider_type, **kwargs
        )
        return self

    def with_workflow(
        self, provider_type: Optional[str] = None, **kwargs: Any
    ) -> "PepperPy":
        """Configure workflow provider.

        Args:
            provider_type: Type of workflow provider (defaults to PEPPERPY_WORKFLOW__PROVIDER)
            **kwargs: Additional provider options

        Returns:
            Self for chaining
        """
        provider_type = provider_type or os.getenv(
            "PEPPERPY_WORKFLOW__PROVIDER", "default"
        )
        self._workflow = self.config.load_workflow_provider(
            provider_type=provider_type, **kwargs
        )
        return self

    @property
    def llm(self) -> LLMProvider:
        """Get LLM provider."""
        if not self._llm:
            raise ValueError("LLM provider not configured. Call with_llm() first.")
        return self._llm

    @property
    def embeddings(self) -> EmbeddingProvider:
        """Get embeddings provider."""
        if not self._embeddings:
            raise ValueError(
                "Embeddings provider not configured. Call with_embeddings() first."
            )
        return self._embeddings

    @property
    def rag(self) -> RAGProvider:
        """Get RAG provider."""
        if not self._rag:
            raise ValueError("RAG provider not configured. Call with_rag() first.")
        return self._rag

    @property
    def storage(self) -> StorageProvider:
        """Get storage provider."""
        if not self._storage:
            raise ValueError(
                "Storage provider not configured. Call with_storage() first."
            )
        return self._storage

    @property
    def tts(self) -> TTSProvider:
        """Get TTS provider."""
        if not self._tts:
            raise ValueError("TTS provider not configured. Call with_tts() first.")
        return self._tts

    @property
    def repository(self) -> RepositoryProvider:
        """Get repository provider."""
        if not self._repository:
            raise ValueError(
                "Repository provider not configured. Call with_repository() first."
            )
        return self._repository

    @property
    def workflow(self) -> WorkflowProvider:
        """Get workflow provider."""
        if not self._workflow:
            raise ValueError(
                "Workflow provider not configured. Call with_workflow() first."
            )
        return self._workflow

    async def __aenter__(self) -> "PepperPy":
        """Enter async context."""
        if self._llm:
            await self._llm.initialize()
        if self._embeddings:
            await self._embeddings.initialize()
        if self._rag:
            await self._rag.initialize()
        if self._storage:
            await self._storage.initialize()
        if self._tts:
            await self._tts.initialize()
        if self._repository:
            await self._repository.initialize()
        if self._workflow:
            await self._workflow.initialize()
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Exit async context."""
        if self._llm:
            await self._llm.cleanup()
        if self._embeddings:
            await self._embeddings.cleanup()
        if self._rag:
            await self._rag.cleanup()
        if self._storage:
            await self._storage.cleanup()
        if self._tts:
            await self._tts.cleanup()
        if self._repository:
            await self._repository.cleanup()
        if self._workflow:
            await self._workflow.cleanup()

    async def send(self, message: str) -> GenerationResult:
        """Send a message to the LLM.

        Args:
            message: Message to send

        Returns:
            Generated response

        Example:
            >>> async with PepperPy() as pepperpy:
            ...     response = await pepperpy.send("What is Python?")
        """
        messages = [Message(role=MessageRole.USER, content=message)]
        return await self.llm.generate(messages)

    async def learn(self, content: Union[str, List[str], Dict[str, Any]]) -> None:
        """Learn from content (add to RAG).

        Args:
            content: Content to learn from

        Example:
            >>> async with PepperPy() as pepperpy:
            ...     await pepperpy.learn("Python is a programming language")
            ...     await pepperpy.learn(["fact1", "fact2"])
            ...     await pepperpy.learn({"title": "Python", "description": "A language"})
        """
        if isinstance(content, str):
            docs = [Document(text=content)]
        elif isinstance(content, list):
            docs = [Document(text=item) for item in content]
        else:
            docs = [Document(text=json.dumps(content))]
        await self.rag.store(docs)

    async def ask(self, question: str) -> GenerationResult:
        """Ask a question using RAG context.

        Args:
            question: Question to ask

        Returns:
            Generated response

        Example:
            >>> async with PepperPy() as pepperpy:
            ...     await pepperpy.learn("Python info")
            ...     response = await pepperpy.ask("What is Python?")
        """
        # Search for relevant documents
        query = Query(text=question)
        docs = await self.rag.search(query)

        # Generate response with context
        messages = [
            Message(
                role=MessageRole.SYSTEM,
                content="Use this context to answer: "
                + "\n".join(doc.text for doc in docs),
            ),
            Message(role=MessageRole.USER, content=question),
        ]
        return await self.llm.generate(messages)

    async def remember(self, file_or_dir: str) -> None:
        """Remember content from files/directories.

        Args:
            file_or_dir: File or directory path

        Example:
            >>> async with PepperPy() as pepperpy:
            ...     await pepperpy.remember("docs/")
            ...     await pepperpy.remember("knowledge.pdf")
        """
        # Load file
        content = await self.storage.read(file_or_dir)
        doc = Document(text=content.decode())

        # Add to RAG
        await self.rag.store([doc])
