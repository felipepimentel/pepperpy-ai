"""Main PepperPy module.

This module provides the main PepperPy class with a fluent API for
interacting with the framework's components.
"""

import os
from typing import Any, Dict, List, Optional, Union

from pepperpy.core.config import Config
from pepperpy.llm import LLMProvider, Message, MessageRole
from pepperpy.llm import create_provider as create_llm_provider
from pepperpy.rag import Document, RAGProvider, SearchResult
from pepperpy.rag import create_provider as create_rag_provider
from pepperpy.tts import TTSProvider
from pepperpy.tts import create_provider as create_tts_provider


class ChatBuilder:
    """Fluent builder for chat interactions."""

    def __init__(self, llm: LLMProvider) -> None:
        """Initialize chat builder.

        Args:
            llm: LLM provider to use
        """
        self._llm = llm
        self._messages: List[Message] = []

    def with_system(self, content: str) -> "ChatBuilder":
        """Add a system message.

        Args:
            content: Message content

        Returns:
            Self for chaining
        """
        self._messages.append(Message(role=MessageRole.SYSTEM, content=content))
        return self

    def with_user(self, content: str) -> "ChatBuilder":
        """Add a user message.

        Args:
            content: Message content

        Returns:
            Self for chaining
        """
        self._messages.append(Message(role=MessageRole.USER, content=content))
        return self

    def with_assistant(self, content: str) -> "ChatBuilder":
        """Add an assistant message.

        Args:
            content: Message content

        Returns:
            Self for chaining
        """
        self._messages.append(Message(role=MessageRole.ASSISTANT, content=content))
        return self

    def with_message(
        self, role: Union[str, MessageRole], content: str
    ) -> "ChatBuilder":
        """Add a message with specific role.

        Args:
            role: Message role
            content: Message content

        Returns:
            Self for chaining
        """
        if isinstance(role, str):
            role = MessageRole(role)
        self._messages.append(Message(role=role, content=content))
        return self

    async def generate(self, **kwargs: Any) -> Any:
        """Generate response from messages.

        Args:
            **kwargs: Additional generation options

        Returns:
            Generation result
        """
        return await self._llm.generate(self._messages, **kwargs)

    async def stream(self, **kwargs: Any) -> Any:
        """Stream response from messages.

        Args:
            **kwargs: Additional generation options

        Returns:
            AsyncIterator of generation chunks
        """
        return self._llm.stream(self._messages, **kwargs)


class TTSBuilder:
    """Fluent builder for TTS interactions."""

    def __init__(self, tts: TTSProvider) -> None:
        """Initialize TTS builder.

        Args:
            tts: TTS provider to use
        """
        self._tts = tts
        self._text: Optional[str] = None
        self._voice_id: Optional[str] = None
        self._options: Dict[str, Any] = {}

    def with_text(self, text: str) -> "TTSBuilder":
        """Set text to synthesize.

        Args:
            text: Text to synthesize

        Returns:
            Self for chaining
        """
        self._text = text
        return self

    def with_voice(self, voice_id: str) -> "TTSBuilder":
        """Set voice to use.

        Args:
            voice_id: Voice identifier

        Returns:
            Self for chaining
        """
        self._voice_id = voice_id
        return self

    def with_options(self, **options: Any) -> "TTSBuilder":
        """Set additional options.

        Args:
            **options: Additional synthesis options

        Returns:
            Self for chaining
        """
        self._options.update(options)
        return self

    async def generate(self) -> Any:
        """Generate audio from text.

        Returns:
            TTSAudio object

        Raises:
            TTSError: If text is not set or synthesis fails
        """
        if not self._text:
            raise ValueError("Text must be set before generating audio")

        return await self._tts.synthesize(
            text=self._text, voice_id=self._voice_id, **self._options
        )


class RAGBuilder:
    """Fluent builder for RAG operations."""

    def __init__(self, rag: RAGProvider) -> None:
        """Initialize RAG builder.

        Args:
            rag: RAG provider to use
        """
        self._rag = rag
        self._documents: List[Document] = []
        self._query_text: Optional[str] = None
        self._query_embeddings: Optional[List[float]] = None
        self._limit: int = 5

    def with_document(
        self,
        text: str,
        metadata: Optional[Dict[str, Any]] = None,
        embeddings: Optional[List[float]] = None,
    ) -> "RAGBuilder":
        """Add a document.

        Args:
            text: Document text
            metadata: Optional document metadata
            embeddings: Optional document embeddings

        Returns:
            Self for chaining
        """
        doc = Document(text=text, metadata=metadata or {})
        if embeddings:
            doc["embeddings"] = embeddings
        self._documents.append(doc)
        return self

    def search(self, text: str) -> "RAGBuilder":
        """Start a search operation.

        Args:
            text: Search query text

        Returns:
            Self for chaining
        """
        self._query_text = text
        return self

    def with_embeddings(self, embeddings: List[float]) -> "RAGBuilder":
        """Set query embeddings.

        Args:
            embeddings: Query embeddings

        Returns:
            Self for chaining
        """
        self._query_embeddings = embeddings
        return self

    def with_limit(self, limit: int) -> "RAGBuilder":
        """Set search result limit.

        Args:
            limit: Maximum number of results

        Returns:
            Self for chaining
        """
        self._limit = limit
        return self

    async def store(self) -> None:
        """Store documents."""
        if not self._documents:
            raise ValueError("No documents to store")
        await self._rag.store(self._documents)
        self._documents = []

    async def generate(self) -> List[SearchResult]:
        """Generate search results.

        Returns:
            List of search results
        """
        if not self._query_text and not self._query_embeddings:
            raise ValueError("Query text or embeddings must be set")

        from pepperpy.rag import Query

        query = Query(text=self._query_text or "", embeddings=self._query_embeddings)
        return await self._rag.search(query, limit=self._limit)


class PepperPy:
    """Main PepperPy class with fluent API."""

    def __init__(self, config: Optional[Union[Dict[str, Any], Config]] = None) -> None:
        """Initialize PepperPy.

        Args:
            config: Optional configuration dictionary or Config instance
        """
        self.config = config if isinstance(config, Config) else Config(config)
        self._llm: Optional[LLMProvider] = None
        self._tts: Optional[TTSProvider] = None
        self._rag: Optional[RAGProvider] = None

    def with_config(self, config: Union[Dict[str, Any], Config]) -> "PepperPy":
        """Configure PepperPy.

        Args:
            config: Configuration dictionary or Config instance

        Returns:
            Self for chaining
        """
        self.config = config if isinstance(config, Config) else Config(config)
        return self

    def with_llm(
        self, provider: Optional[Union[str, LLMProvider]] = None, **kwargs: Any
    ) -> "PepperPy":
        """Configure LLM provider.

        Args:
            provider: LLM provider instance or type name
            **kwargs: Additional provider options

        Returns:
            Self for chaining
        """
        if isinstance(provider, LLMProvider):
            self._llm = provider
        else:
            provider_type = provider or os.getenv("PEPPERPY_LLM__PROVIDER", "openai")
            provider_config = self.config.get("llm.config", {})
            provider_config.update(kwargs)
            self._llm = create_llm_provider(
                provider_type=provider_type, **provider_config
            )
        return self

    def with_tts(
        self, provider: Optional[Union[str, TTSProvider]] = None, **kwargs: Any
    ) -> "PepperPy":
        """Configure TTS provider.

        Args:
            provider: TTS provider instance or type name
            **kwargs: Additional provider options

        Returns:
            Self for chaining
        """
        if isinstance(provider, TTSProvider):
            self._tts = provider
        else:
            provider_type = provider or os.getenv(
                "PEPPERPY_TTS__PROVIDER", "elevenlabs"
            )
            provider_config = self.config.get("tts.config", {})
            provider_config.update(kwargs)
            self._tts = create_tts_provider(
                provider_type=provider_type, **provider_config
            )
        return self

    def with_rag(
        self, provider: Optional[Union[str, RAGProvider]] = None, **kwargs: Any
    ) -> "PepperPy":
        """Configure RAG provider.

        Args:
            provider: RAG provider instance or type name
            **kwargs: Additional provider options

        Returns:
            Self for chaining
        """
        if isinstance(provider, RAGProvider):
            self._rag = provider
        else:
            provider_type = provider or os.getenv("PEPPERPY_RAG__PROVIDER", "sqlite")
            provider_config = self.config.get("rag.config", {})
            provider_config.update(kwargs)
            self._rag = create_rag_provider(
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
    def chat(self) -> ChatBuilder:
        """Get chat builder."""
        return ChatBuilder(self.llm)

    @property
    def tts(self) -> TTSBuilder:
        """Get TTS builder."""
        if not self._tts:
            raise ValueError("TTS provider not configured. Call with_tts() first.")
        return TTSBuilder(self._tts)

    @property
    def rag(self) -> RAGBuilder:
        """Get RAG builder."""
        if not self._rag:
            raise ValueError("RAG provider not configured. Call with_rag() first.")
        return RAGBuilder(self._rag)

    async def __aenter__(self) -> "PepperPy":
        """Enter async context."""
        if self._llm:
            await self._llm.initialize()
        if self._tts:
            await self._tts.initialize()
        if self._rag:
            await self._rag.initialize()
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Exit async context."""
        if self._llm:
            await self._llm.cleanup()
        if self._tts:
            await self._tts.cleanup()
        if self._rag:
            await self._rag.cleanup()
