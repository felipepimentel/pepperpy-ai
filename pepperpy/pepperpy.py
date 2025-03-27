"""Main PepperPy module.

This module provides the main PepperPy class with a fluent API for
interacting with the framework's components.
"""

import json
import os
from typing import TYPE_CHECKING, Any, AsyncIterator, Dict, List, Optional, Union

from pepperpy.core.config import Config
from pepperpy.embeddings import create_provider as create_embeddings_provider
from pepperpy.llm import GenerationResult, LLMProvider, Message, MessageRole
from pepperpy.llm import create_provider as create_llm_provider
from pepperpy.rag import Document, Query, RAGProvider
from pepperpy.rag import create_provider as create_rag_provider
from pepperpy.storage import StorageProvider
from pepperpy.storage import create_provider as create_storage_provider
from pepperpy.tools.repository import RepositoryProvider
from pepperpy.tools.repository import create_provider as create_repository_provider
from pepperpy.tts import TTSProvider
from pepperpy.tts import create_provider as create_tts_provider
from pepperpy.workflow import WorkflowProvider
from pepperpy.workflow import create_provider as create_workflow_provider

if TYPE_CHECKING:
    from pepperpy.embeddings import EmbeddingsProvider


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
        self._embeddings: Optional["EmbeddingsProvider"] = None

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
        provider_config = self.config.get("llm.config", {})
        provider_config.update(kwargs)

        self._llm = create_llm_provider(provider_type=provider_type, **provider_config)
        return self

    def with_embeddings(
        self, provider_type: Optional[str] = None, **kwargs: Any
    ) -> "PepperPy":
        """Configure embeddings provider.

        Args:
            provider_type: Type of embeddings provider (defaults to config or PEPPERPY_EMBEDDINGS__PROVIDER)
            **kwargs: Additional provider options

        Returns:
            Self for chaining
        """
        provider_type = (
            provider_type
            or self.config.get("embeddings.provider")
            or os.getenv("PEPPERPY_EMBEDDINGS__PROVIDER", "local")
        )
        if provider_type is None:
            provider_type = "local"  # Default to local if no provider type is specified

        provider_config = self.config.get("embeddings.config", {})
        provider_config.update(kwargs)

        self._embeddings = create_embeddings_provider(
            provider_type=provider_type, **provider_config
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
        provider_config = self.config.get("rag.config", {})
        provider_config.update(kwargs)

        # Ensure embeddings provider is initialized first
        if not self._embeddings:
            self.with_embeddings()

        # At this point self._embeddings is guaranteed to be not None
        assert self._embeddings is not None
        provider_config["embedding_function"] = (
            self._embeddings.get_embedding_function()
        )

        self._rag = create_rag_provider(provider_type=provider_type, **provider_config)
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
        provider_config = self.config.get("storage.config", {})
        provider_config.update(kwargs)

        self._storage = create_storage_provider(
            provider_type=provider_type, **provider_config
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
        provider_config = self.config.get("tts.config", {})
        provider_config.update(kwargs)

        self._tts = create_tts_provider(provider_type=provider_type, **provider_config)
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
        provider_config = self.config.get("repository.config", {})
        provider_config.update(kwargs)

        self._repository = create_repository_provider(
            provider_type=provider_type, **provider_config
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
        provider_config = self.config.get("workflow.config", {})
        provider_config.update(kwargs)

        self._workflow = create_workflow_provider(
            provider_type=provider_type, **provider_config
        )
        return self

    @property
    def llm(self) -> LLMProvider:
        """Get LLM provider."""
        if not self._llm:
            raise ValueError("LLM provider not configured. Call with_llm() first.")
        return self._llm

    @property
    def embeddings(self) -> "EmbeddingsProvider":
        """Get embeddings provider."""
        if not self._embeddings:
            raise ValueError("Embeddings provider not configured")
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

    async def list_voices(self, **kwargs: Any) -> List[Dict[str, Any]]:
        """List available TTS voices.

        Args:
            **kwargs: Additional provider options

        Returns:
            List of available voices with details

        Example:
            >>> async with PepperPy() as pepperpy:
            ...     voices = await pepperpy.list_voices()
        """
        return await self.tts.get_voices(**kwargs)

    async def text_to_speech(
        self,
        text: str,
        voice: Optional[str] = None,
        output_format: Optional[str] = None,
        **kwargs: Any,
    ) -> bytes:
        """Convert text to speech.

        Args:
            text: Text to convert to speech
            voice: Voice to use (defaults to provider default)
            output_format: Output format (defaults to provider default)
            **kwargs: Additional provider options

        Returns:
            Audio data as bytes

        Example:
            >>> async with PepperPy() as pepperpy:
            ...     audio_data = await pepperpy.text_to_speech("Hello world")
            ...     with open("output.mp3", "wb") as f:
            ...         f.write(audio_data)
        """
        # Use default voice from provider if not specified
        voice_name = (
            voice
            if voice is not None
            else (self.config.get("tts.voice") or "en-US-JennyNeural")
        )

        # Use default format from provider if not specified
        format_name = (
            output_format
            if output_format is not None
            else (
                self.config.get("tts.output_format")
                or "audio-16khz-32kbitrate-mono-mp3"
            )
        )

        return await self.tts.synthesize(
            text=text, voice=voice_name, output_format=format_name, **kwargs
        )

    async def text_to_speech_stream(
        self, text: str, voice: Optional[str] = None, **kwargs: Any
    ) -> AsyncIterator[bytes]:
        """Stream text to speech conversion.

        Args:
            text: Text to convert to speech
            voice: Voice to use (defaults to provider default)
            **kwargs: Additional provider options

        Returns:
            Async iterator of audio data chunks

        Example:
            >>> async with PepperPy() as pepperpy:
            ...     async for chunk in pepperpy.text_to_speech_stream("Hello world"):
            ...         # Process audio chunk
            ...         pass
        """
        # Use default voice from provider if not specified
        voice_name = (
            voice
            if voice is not None
            else (self.config.get("tts.voice") or "en-US-JennyNeural")
        )

        async_iter = await self.tts.convert_text_stream(
            text=text, voice_id=voice_name, **kwargs
        )
        return async_iter
