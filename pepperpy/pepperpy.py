"""Main PepperPy class.

This module provides the main entry point for using the PepperPy framework.
It abstracts the plugin system and provides a fluent API for configuring
and using providers.
"""

import os
import sys
import time
from collections.abc import AsyncIterator
from typing import (
    Any,
    Callable,
    Dict,
    List,
    Optional,
    Self,
    Type,
    Union,
    cast,
)

from pepperpy.agents.orchestrator import Orchestrator, get_orchestrator
from pepperpy.cache import cached, get_result_cache, invalidate_cache
from pepperpy.core.errors import (
    APIError,
    RateLimitError,
    ValidationError,
)
from pepperpy.core.logging import get_logger
from pepperpy.core.retry import retry_async, retry_strategy
from pepperpy.discovery.content_type import detect_content_type
from pepperpy.llm import GenerationChunk, GenerationResult, LLMProvider, Message
from pepperpy.llm.base import MessageRole
from pepperpy.plugins import (
    PepperpyPlugin,
    PluginError,
    discover_plugins,
    get_plugin,
    register_plugin,
    register_plugin_path,
    set_autodiscovery,
)
from pepperpy.plugins.registry import enable_hot_reload, scan_available_plugins
from pepperpy.rag import (
    Document,
    Query,
    RAGProvider,
    RetrievalResult,
)
from pepperpy.tts import TTSProvider
from pepperpy.workflow import WorkflowProvider

logger = get_logger(__name__)

# Singleton instance management
_singleton_instance: Optional["PepperPy"] = None
_framework_initialized = False


async def init_framework() -> None:
    """Initialize the PepperPy framework.

    This function initializes the framework by discovering plugins and
    setting up the necessary components.
    """
    global _framework_initialized

    if _framework_initialized:
        return

    # Discover plugins in default locations
    plugin_paths = [
        # Apenas diretórios de plugins válidos, fora do pacote pepperpy
        os.path.join(os.path.dirname(os.path.dirname(__file__)), "plugins"),
        os.path.join(os.getcwd(), "plugins"),
    ]

    # Register paths and discover plugins
    for path in plugin_paths:
        register_plugin_path(path)

    # Call discover_plugins without await because it's not async
    discover_plugins()

    # Import and register OpenRouter provider directly
    # This ensures it's available even if plugin discovery fails
    openrouter_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)), "plugins", "llm", "openrouter"
    )
    if os.path.exists(openrouter_path) and os.path.isdir(openrouter_path):
        try:
            # Tentar importar do caminho correto em /plugins
            sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
            from plugins.llm.openrouter.provider import OpenRouterProvider

            register_plugin("llm", "openrouter", OpenRouterProvider)
            logger.info("Successfully registered OpenRouter provider")
        except ImportError as e:
            logger.warning(f"Failed to import OpenRouter provider: {e}")

    _framework_initialized = True


class ChatBuilder:
    """Builder for chat interactions."""

    def __init__(self, provider: LLMProvider) -> None:
        """Initialize chat builder.

        Args:
            provider: LLM provider to use
        """
        self._provider = provider
        self._messages: List[Message] = []
        self._temperature: Optional[float] = None
        self._max_tokens: Optional[int] = None

    def with_system(self, message: str) -> Self:
        """Add system message.

        Args:
            message: System message content

        Returns:
            Self for chaining
        """
        self._messages.append(Message(role=MessageRole.SYSTEM, content=message))
        return self

    def with_user(self, message: str) -> Self:
        """Add user message.

        Args:
            message: User message content

        Returns:
            Self for chaining
        """
        self._messages.append(Message(role=MessageRole.USER, content=message))
        return self

    def with_assistant(self, message: str) -> Self:
        """Add assistant message.

        Args:
            message: Assistant message content

        Returns:
            Self for chaining
        """
        self._messages.append(Message(role=MessageRole.ASSISTANT, content=message))
        return self

    def with_temperature(self, temperature: float) -> Self:
        """Set temperature for generation.

        Args:
            temperature: Temperature value (0.0 to 1.0)

        Returns:
            Self for chaining
        """
        self._temperature = temperature
        return self

    def with_max_tokens(self, max_tokens: int) -> Self:
        """Set maximum tokens for generation.

        Args:
            max_tokens: Maximum tokens to generate

        Returns:
            Self for chaining
        """
        self._max_tokens = max_tokens
        return self

    async def generate(self) -> GenerationResult:
        """Generate response using the configured messages.

        Returns:
            GenerationResult containing the response

        Raises:
            ValidationError: If no messages are configured
        """
        if not self._messages:
            raise ValidationError("No messages configured for generation")

        kwargs: Dict[str, Any] = {}
        if self._temperature is not None:
            kwargs["temperature"] = self._temperature
        if self._max_tokens is not None:
            kwargs["max_tokens"] = self._max_tokens

        return await self._provider.generate(self._messages, **kwargs)

    async def stream(self) -> AsyncIterator[GenerationChunk]:
        """Generate response in streaming mode.

        Returns:
            AsyncIterator yielding GenerationChunk objects

        Raises:
            ValidationError: If no messages are configured
        """
        if not self._messages:
            raise ValidationError("No messages configured for generation")

        kwargs: Dict[str, Any] = {}
        if self._temperature is not None:
            kwargs["temperature"] = self._temperature
        if self._max_tokens is not None:
            kwargs["max_tokens"] = self._max_tokens

        async for chunk in self._provider.stream(self._messages, **kwargs):
            yield chunk


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
        self._options: Dict[str, Any] = {
            "speed": 1.0,
            "pitch": 1.0,
            "volume": 1.0,
        }

    def with_text(self, text: str) -> Self:
        """Set text to synthesize.

        Args:
            text: Text to synthesize

        Returns:
            Self for chaining

        Raises:
            ValueError: If text is empty
        """
        if not text.strip():
            raise ValueError("Text cannot be empty")
        self._text = text
        return self

    def with_voice(self, voice_id: str) -> Self:
        """Set voice to use.

        Args:
            voice_id: Voice identifier

        Returns:
            Self for chaining

        Raises:
            ValueError: If voice_id is empty
        """
        if not voice_id.strip():
            raise ValueError("Voice ID cannot be empty")
        self._voice_id = voice_id
        return self

    def with_speed(self, speed: float) -> Self:
        """Set speech speed.

        Args:
            speed: Speed multiplier (0.5 to 2.0)

        Returns:
            Self for chaining

        Raises:
            ValueError: If speed is out of range
        """
        if not 0.5 <= speed <= 2.0:
            raise ValueError("Speed must be between 0.5 and 2.0")
        self._options["speed"] = speed
        return self

    def with_pitch(self, pitch: float) -> Self:
        """Set voice pitch.

        Args:
            pitch: Pitch multiplier (0.5 to 2.0)

        Returns:
            Self for chaining

        Raises:
            ValueError: If pitch is out of range
        """
        if not 0.5 <= pitch <= 2.0:
            raise ValueError("Pitch must be between 0.5 and 2.0")
        self._options["pitch"] = pitch
        return self

    def with_volume(self, volume: float) -> Self:
        """Set audio volume.

        Args:
            volume: Volume multiplier (0.0 to 2.0)

        Returns:
            Self for chaining

        Raises:
            ValueError: If volume is out of range
        """
        if not 0.0 <= volume <= 2.0:
            raise ValueError("Volume must be between 0.0 and 2.0")
        self._options["volume"] = volume
        return self

    def with_options(self, **options: Any) -> Self:
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
            ValueError: If text is not set or synthesis fails
        """
        if not self._text:
            raise ValueError("Text must be set before generating audio")

        return await self._tts.synthesize(
            text=self._text, voice_id=self._voice_id, **self._options
        )


class RAGBuilder:
    """Fluent builder for RAG operations."""

    def __init__(self, rag_provider: RAGProvider) -> None:
        """Initialize RAG builder.

        Args:
            rag_provider: RAG provider to use
        """
        self._rag = rag_provider
        self._documents: List[str] = []
        self._query: str = ""
        self._limit: int = 5
        self._auto_embeddings: bool = False
        self._filters: Dict[str, Any] = {}
        self._rerank: bool = False

    def add_documents(self, documents: Union[str, List[str]]) -> Self:
        """Add documents to store.

        Args:
            documents: Document or list of documents to store

        Returns:
            Self for chaining

        Raises:
            ValueError: If any document is empty
        """
        if isinstance(documents, str):
            documents = [documents]

        for doc in documents:
            if not doc.strip():
                raise ValueError("Documents cannot be empty")

        self._documents.extend(documents)
        return self

    def with_auto_embeddings(self, enabled: bool = True) -> Self:
        """Enable/disable automatic embeddings generation.

        Args:
            enabled: Whether to enable auto embeddings

        Returns:
            Self for chaining
        """
        self._auto_embeddings = enabled
        return self

    def with_filter(self, **filters: Any) -> Self:
        """Add filters for search.

        Args:
            **filters: Filter key-value pairs

        Returns:
            Self for chaining
        """
        self._filters.update(filters)
        return self

    def with_reranking(self, enabled: bool = True) -> Self:
        """Enable/disable result reranking.

        Args:
            enabled: Whether to enable reranking

        Returns:
            Self for chaining
        """
        self._rerank = enabled
        return self

    async def store(self) -> None:
        """Store documents in RAG provider.

        Raises:
            ValueError: If no documents have been added
        """
        if not self._documents:
            raise ValueError("No documents added. Add documents before storing.")

        for text in self._documents:
            doc = Document(text=text)
            if self._auto_embeddings:
                # TODO: Generate embeddings
                pass
            await self._rag.store(doc)

    def search(self, query: str) -> Self:
        """Set search query.

        Args:
            query: Search query

        Returns:
            Self for chaining

        Raises:
            ValueError: If query is empty
        """
        if not query.strip():
            raise ValueError("Search query cannot be empty")
        self._query = query
        return self

    def limit(self, limit: int) -> Self:
        """Set maximum number of results.

        Args:
            limit: Maximum number of results

        Returns:
            Self for chaining

        Raises:
            ValueError: If limit is not positive
        """
        if limit <= 0:
            raise ValueError("Result limit must be positive")
        self._limit = limit
        return self

    async def execute(self) -> List[RetrievalResult]:
        """Execute search query.

        Returns:
            Search results

        Raises:
            ValueError: If no query has been set
        """
        if not self._query:
            raise ValueError("No query set. Call search() before executing.")

        results = await self._rag.search(
            self._query,
            limit=self._limit,
            filters=self._filters if self._filters else None,
            rerank=self._rerank,
        )
        return list(cast(Sequence[RetrievalResult], results))


class ContentBuilder:
    """Fluent builder for content generation."""

    def __init__(self, llm_provider: LLMProvider) -> None:
        """Initialize content builder.

        Args:
            llm_provider: LLM provider to use for content generation
        """
        self._llm = llm_provider
        self._style: List[str] = []
        self._topic: str = ""
        self._type: str = ""
        self._language: str = "en"
        self._tone: str = "neutral"
        self._target_audience: Optional[str] = None
        self._max_length: Optional[int] = None

    def article(self, topic: str) -> Self:
        """Set content type to article with given topic.

        Args:
            topic: Topic to write about

        Returns:
            Self for chaining

        Raises:
            ValueError: If topic is empty
        """
        if not topic.strip():
            raise ValueError("Topic cannot be empty")
        self._type = "article"
        self._topic = topic
        return self

    def blog_post(self, topic: str) -> Self:
        """Set content type to blog post with given topic.

        Args:
            topic: Topic to write about

        Returns:
            Self for chaining

        Raises:
            ValueError: If topic is empty
        """
        if not topic.strip():
            raise ValueError("Topic cannot be empty")
        self._type = "blog_post"
        self._topic = topic
        return self

    def informative(self) -> Self:
        """Set style to informative.

        Returns:
            Self for chaining
        """
        self._style.append("informative")
        return self

    def conversational(self) -> Self:
        """Set style to conversational.

        Returns:
            Self for chaining
        """
        self._style.append("conversational")
        return self

    def engaging(self) -> Self:
        """Set style to engaging.

        Returns:
            Self for chaining
        """
        self._style.append("engaging")
        return self

    def with_citations(self) -> Self:
        """Add citations to content.

        Returns:
            Self for chaining
        """
        self._style.append("citations")
        return self

    def in_language(self, language: str) -> Self:
        """Set content language.

        Args:
            language: ISO language code (e.g., 'en', 'pt', 'es')

        Returns:
            Self for chaining

        Raises:
            ValueError: If language code is invalid
        """
        if not language.strip() or len(language) < 2:
            raise ValueError("Invalid language code")
        self._language = language.lower()
        return self

    def with_tone(self, tone: str) -> Self:
        """Set content tone.

        Args:
            tone: Content tone (e.g., 'formal', 'casual', 'professional')

        Returns:
            Self for chaining

        Raises:
            ValueError: If tone is empty
        """
        if not tone.strip():
            raise ValueError("Tone cannot be empty")
        self._tone = tone
        return self

    def for_audience(self, audience: str) -> Self:
        """Set target audience.

        Args:
            audience: Target audience description

        Returns:
            Self for chaining

        Raises:
            ValueError: If audience is empty
        """
        if not audience.strip():
            raise ValueError("Audience cannot be empty")
        self._target_audience = audience
        return self

    def with_max_length(self, words: int) -> Self:
        """Set maximum content length in words.

        Args:
            words: Maximum number of words

        Returns:
            Self for chaining

        Raises:
            ValueError: If words is not positive
        """
        if words <= 0:
            raise ValueError("Maximum length must be positive")
        self._max_length = words
        return self

    async def generate(self) -> Dict[str, Any]:
        """Generate content based on configuration.

        Returns:
            Generated content with metadata

        Raises:
            ValueError: If topic or type is not set
        """
        if not self._topic or not self._type:
            raise ValueError("Topic and content type must be set before generating")

        style_str = ", ".join(self._style) if self._style else self._tone
        system_prompt = [
            f"You are a professional content writer specializing in {style_str} content.",
            f"Write in {self._language} language.",
        ]

        if self._target_audience:
            system_prompt.append(f"Your target audience is: {self._target_audience}")

        if "citations" in self._style:
            system_prompt.append(
                "Include proper citations and references to support your points."
            )

        if self._max_length:
            system_prompt.append(f"Keep the content under {self._max_length} words.")

        messages = [
            Message(
                role=MessageRole.SYSTEM,
                content=" ".join(system_prompt),
            ),
            Message(
                role=MessageRole.USER,
                content=f"Write a {self._type} about: {self._topic}",
            ),
        ]

        result = await self._llm.generate(messages)

        content = {
            "title": self._topic,
            "content": result.content,
            "metadata": {
                "style": style_str,
                "type": self._type,
                "language": self._language,
                "tone": self._tone,
                "word_count": len(result.content.split()),
                "target_audience": self._target_audience,
            },
        }

        if "citations" in self._style:
            # TODO: Extract citations from content
            content["references"] = []

        return content

    async def stream(self) -> AsyncIterator[GenerationChunk]:
        """Stream content generation results.

        Returns:
            AsyncIterator yielding generation chunks

        Raises:
            ValueError: If topic or type is not set
        """
        if not self._topic or not self._type:
            raise ValueError("Topic and content type must be set before generating")

        style_str = ", ".join(self._style) if self._style else self._tone
        system_prompt = [
            f"You are a professional content writer specializing in {style_str} content.",
            f"Write in {self._language} language.",
        ]

        if self._target_audience:
            system_prompt.append(f"Your target audience is: {self._target_audience}")

        if "citations" in self._style:
            system_prompt.append(
                "Include proper citations and references to support your points."
            )

        if self._max_length:
            system_prompt.append(f"Keep the content under {self._max_length} words.")

        messages = [
            Message(
                role=MessageRole.SYSTEM,
                content=" ".join(system_prompt),
            ),
            Message(
                role=MessageRole.USER,
                content=f"Write a {self._type} about: {self._topic}",
            ),
        ]

        stream = cast(AsyncIterator[GenerationChunk], self._llm.stream(messages))
        async for chunk in stream:
            yield chunk


class TextBuilder:
    """Fluent builder for text generation."""

    def __init__(self, llm_provider: LLMProvider) -> None:
        """Initialize text builder.

        Args:
            llm_provider: LLM provider to use for text generation
        """
        self._llm = llm_provider
        self._prompt: str = ""
        self._system_prompt: str = ""
        self._temperature: float = 0.7
        self._max_tokens: Optional[int] = None
        self._stop_sequences: List[str] = []
        self._format: Optional[str] = None

    def with_prompt(self, prompt: str) -> Self:
        """Set the user prompt.

        Args:
            prompt: The prompt to generate text from

        Returns:
            Self for chaining

        Raises:
            ValueError: If prompt is empty
        """
        if not prompt.strip():
            raise ValueError("Prompt cannot be empty")
        self._prompt = prompt
        return self

    def with_system_prompt(self, prompt: str) -> Self:
        """Set the system prompt.

        Args:
            prompt: The system prompt to use

        Returns:
            Self for chaining

        Raises:
            ValueError: If prompt is empty
        """
        if not prompt.strip():
            raise ValueError("System prompt cannot be empty")
        self._system_prompt = prompt
        return self

    def with_temperature(self, temperature: float) -> Self:
        """Set the temperature for generation.

        Args:
            temperature: Temperature value between 0 and 2

        Returns:
            Self for chaining

        Raises:
            ValueError: If temperature is out of range
        """
        if not 0 <= temperature <= 2:
            raise ValueError("Temperature must be between 0 and 2")
        self._temperature = temperature
        return self

    def with_max_tokens(self, max_tokens: int) -> Self:
        """Set maximum number of tokens to generate.

        Args:
            max_tokens: Maximum number of tokens

        Returns:
            Self for chaining

        Raises:
            ValueError: If max_tokens is not positive
        """
        if max_tokens <= 0:
            raise ValueError("Maximum tokens must be positive")
        self._max_tokens = max_tokens
        return self

    def with_stop_sequence(self, sequence: str) -> Self:
        """Add a stop sequence.

        Args:
            sequence: Stop sequence to add

        Returns:
            Self for chaining

        Raises:
            ValueError: If sequence is empty
        """
        if not sequence:
            raise ValueError("Stop sequence cannot be empty")
        self._stop_sequences.append(sequence)
        return self

    def as_json(self) -> Self:
        """Format output as JSON.

        Returns:
            Self for chaining
        """
        self._format = "json"
        return self

    def as_markdown(self) -> Self:
        """Format output as Markdown.

        Returns:
            Self for chaining
        """
        self._format = "markdown"
        return self

    async def generate(self) -> str:
        """Generate text based on configuration.

        Returns:
            Generated text

        Raises:
            ValueError: If prompt is not set
        """
        if not self._prompt:
            raise ValueError("Prompt must be set before generating")

        messages = []
        if self._system_prompt:
            if self._format:
                messages.append(
                    Message(
                        role=MessageRole.SYSTEM,
                        content=f"{self._system_prompt}\nFormat the output as {self._format}.",
                    )
                )
            else:
                messages.append(
                    Message(
                        role=MessageRole.SYSTEM,
                        content=self._system_prompt,
                    )
                )

        messages.append(
            Message(
                role=MessageRole.USER,
                content=self._prompt,
            )
        )

        result = await self._llm.generate(
            messages,
            temperature=self._temperature,
            max_tokens=self._max_tokens,
            stop_sequences=self._stop_sequences if self._stop_sequences else None,
        )

        return result.content

    async def stream(self) -> AsyncIterator[GenerationChunk]:
        """Stream text generation results.

        Returns:
            AsyncIterator yielding generation chunks

        Raises:
            ValueError: If prompt is not set
        """
        if not self._prompt:
            raise ValueError("Prompt must be set before streaming")

        messages = []
        if self._system_prompt:
            if self._format:
                messages.append(
                    Message(
                        role=MessageRole.SYSTEM,
                        content=f"{self._system_prompt}\nFormat the output as {self._format}.",
                    )
                )
            else:
                messages.append(
                    Message(
                        role=MessageRole.SYSTEM,
                        content=self._system_prompt,
                    )
                )

        messages.append(
            Message(
                role=MessageRole.USER,
                content=self._prompt,
            )
        )

        stream = await self._llm.stream(
            messages,
            temperature=self._temperature,
            max_tokens=self._max_tokens,
            stop_sequences=self._stop_sequences if self._stop_sequences else None,
        )
        async for chunk in stream:
            yield chunk


class DocumentBuilder:
    """Builder for configuring document operations."""

    def __init__(self, provider: WorkflowProvider) -> None:
        self._provider = provider
        self._context: PipelineContext = PipelineContext()
        self._file_path: Optional[str] = None
        self._text: Optional[str] = None
        self._extract_text: bool = False
        self._classify: bool = False
        self._extract_metadata: bool = False

    def with_context(self, context: PipelineContext) -> "DocumentBuilder":
        """Set the context for document operations.

        Args:
            context: Pipeline context to use

        Returns:
            Self for chaining
        """
        self._context = context
        return self

    def from_file(self, file_path: str) -> "DocumentBuilder":
        """Set the input file path.

        Args:
            file_path: Path to the input file

        Returns:
            Self for chaining
        """
        self._file_path = file_path
        return self

    def from_text(self, text: str) -> "DocumentBuilder":
        """Set the input text.

        Args:
            text: Input text to process

        Returns:
            Self for chaining
        """
        self._text = text
        return self

    def extract_text(self) -> "DocumentBuilder":
        """Extract text from the document.

        Returns:
            Self for chaining
        """
        self._extract_text = True
        return self

    def classify(self) -> "DocumentBuilder":
        """Classify the document.

        Returns:
            Self for chaining
        """
        self._classify = True
        return self

    def extract_metadata(self) -> "DocumentBuilder":
        """Extract metadata from the document.

        Returns:
            Self for chaining
        """
        self._extract_metadata = True
        return self

    async def execute(self) -> Union[str, Dict[str, Any]]:
        """Execute the document operation.

        Returns:
            Extracted text, classification results, or metadata

        Raises:
            ValueError: If no input is set
        """
        if not self._file_path and not self._text:
            raise ValueError("No input set. Call from_file() or from_text() first.")

        # Create a workflow for document processing
        input_data = self._file_path or self._text
        if input_data is None:
            raise ValueError("No input data available")

        workflow = DocumentWorkflow(input_data)

        result = await self._provider.execute_workflow(workflow, self._context)

        # Return mock results for now
        text = "This is the extracted text from the document."
        classification = {
            "document_type": "article",
            "content_category": "technical",
            "language": "en",
        }
        metadata = {
            "title": "Sample Document",
            "author": "John Doe",
            "date": "2024-03-29",
        }

        # If only one operation is requested, return its specific result
        if self._extract_text and not self._classify and not self._extract_metadata:
            return text
        elif self._classify and not self._extract_text and not self._extract_metadata:
            return classification
        elif self._extract_metadata and not self._extract_text and not self._classify:
            return metadata

        # If multiple operations are requested, return a combined result
        result = {}
        if self._extract_text:
            result["text"] = text
        if self._classify:
            result["classification"] = classification
        if self._extract_metadata:
            result["metadata"] = metadata

        return result or {
            "text": text,
            "classification": classification,
            "metadata": metadata,
        }


class LLMBuilder:
    """Builder for configuring LLM operations."""

    def __init__(self, provider: LLMProvider) -> None:
        self._provider = provider
        self._context: List[Message] = []
        self._system_prompt: Optional[str] = None

    def with_context(self, context: List[Message]) -> "LLMBuilder":
        """Set the context for LLM operations.

        Args:
            context: List of messages to use as context

        Returns:
            Self for chaining
        """
        self._context = context
        return self

    def with_system_prompt(self, prompt: str) -> "LLMBuilder":
        """Set the system prompt for LLM operations.

        Args:
            prompt: System prompt to use

        Returns:
            Self for chaining
        """
        self._system_prompt = prompt
        return self

    async def generate(self, prompt: str) -> GenerationResult:
        """Generate a response using the LLM.

        Args:
            prompt: The user prompt to generate from

        Returns:
            The generated message
        """
        messages = []
        if self._system_prompt:
            messages.append(
                Message(role=MessageRole.SYSTEM, content=self._system_prompt)
            )
        messages.extend(self._context)
        messages.append(Message(role=MessageRole.USER, content=prompt))
        return await self._provider.generate(messages)


class PepperPy:
    """Main PepperPy framework class."""

    def __init__(self) -> None:
        """Initialize the PepperPy class."""
        self._providers: Dict[str, PepperpyPlugin] = {}
        self._llm_provider: Optional[LLMProvider] = None
        self._rag_provider: Optional[RAGProvider] = None
        self._tts_provider: Optional[TTSProvider] = None
        self._workflow_provider: Optional[WorkflowProvider] = None
        self._embeddings_provider: Optional[PepperpyPlugin] = None
        self._content_provider: Optional[PepperpyPlugin] = None
        self._orchestrator: Optional[Orchestrator] = None
        self._context: Dict[str, Any] = {}
        self._error_handlers: Dict[Type[Exception], Callable] = {}
        self._initialized = False
        self._retry_config = {
            "max_retries": 3,
            "retry_delay": 1.0,
            "backoff_factor": 2.0,
            "retry_exceptions": [
                RateLimitError,
                APIError,
                ConnectionError,
                TimeoutError,
            ],
        }

    @classmethod
    def get_instance(cls) -> "PepperPy":
        """Get the singleton instance of PepperPy.

        If an instance doesn't exist, it creates one.

        Returns:
            Singleton PepperPy instance
        """
        global _singleton_instance
        if _singleton_instance is None:
            _singleton_instance = cls()
        return _singleton_instance

    @staticmethod
    def create() -> "PepperPy":
        """Create a new PepperPy instance.

        This method is provided for backward compatibility.
        New code should use the constructor directly.

        Returns:
            New PepperPy instance
        """
        return PepperPy()

    def with_plugin(
        self, plugin_type: str, provider_type: str, **config: Any
    ) -> "PepperPy":
        """Configure a plugin.

        Args:
            plugin_type: Type of plugin to configure
            provider_type: Type of provider to use
            **config: Plugin configuration

        Returns:
            Self for chaining

        Raises:
            ValidationError: If provider type not found
        """
        # Get plugin class
        plugin_class = get_plugin(plugin_type, provider_type)
        if not plugin_class:
            raise ValidationError(f"Provider type '{provider_type}' not found")

        # Create provider instance
        provider = plugin_class(**config)
        self._providers[plugin_type] = provider

        return self

    def get_provider(self, plugin_type: str) -> PepperpyPlugin:
        """Get a configured provider.

        Args:
            plugin_type: Type of plugin to get

        Returns:
            Provider instance

        Raises:
            ValidationError: If provider not found
        """
        provider = self._providers.get(plugin_type)
        if not provider:
            raise ValidationError(f"Provider '{plugin_type}' not configured")
        return provider

    def _ensure_orchestrator(self) -> Orchestrator:
        """Ensure that an orchestrator is available.

        Returns:
            The orchestrator instance

        Raises:
            ValidationError: If initialization fails
        """
        if self._orchestrator is None:
            try:
                self._orchestrator = get_orchestrator()
            except Exception as e:
                logger.error(f"Failed to initialize orchestrator: {e}")
                raise ValidationError(f"Failed to initialize orchestrator: {e}")
        return self._orchestrator

    def _get_context(self) -> Dict[str, Any]:
        """Get current execution context.

        Returns:
            Dictionary of context variables
        """
        return self._context.copy()

    def add_context(self, **kwargs: Any) -> Self:
        """Add values to the global context.

        Args:
            **kwargs: Key-value pairs to add to context

        Returns:
            Self for chaining
        """
        self._context.update(kwargs)
        return self

    def set_retry_config(
        self,
        max_retries: Optional[int] = None,
        retry_delay: Optional[float] = None,
        backoff_factor: Optional[float] = None,
        retry_exceptions: Optional[List[Type[Exception]]] = None,
    ) -> Self:
        """Configure retry behavior.

        Args:
            max_retries: Maximum number of retry attempts
            retry_delay: Initial delay between retries in seconds
            backoff_factor: Multiplier for delay on each retry
            retry_exceptions: List of exception types to retry on

        Returns:
            Self for chaining
        """
        if max_retries is not None:
            self._retry_config["max_retries"] = max_retries
        if retry_delay is not None:
            self._retry_config["retry_delay"] = retry_delay
        if backoff_factor is not None:
            self._retry_config["backoff_factor"] = backoff_factor
        if retry_exceptions is not None:
            self._retry_config["retry_exceptions"] = retry_exceptions
        return self

    def register_error_handler(
        self, exception_type: Type[Exception], handler: Callable
    ) -> Self:
        """Register a handler for a specific exception type.

        Args:
            exception_type: Type of exception to handle
            handler: Function to call when exception occurs

        Returns:
            Self for chaining
        """
        self._error_handlers[exception_type] = handler
        return self

    def _handle_error(self, error: Exception) -> Any:
        """Handle error using registered handlers.

        Args:
            error: The exception that occurred

        Returns:
            Result from handler or re-raises exception

        Raises:
            Exception: If no handler is registered for this error
        """
        for error_type, handler in self._error_handlers.items():
            if isinstance(error, error_type):
                return handler(error)
        raise error

    @cached(namespace="pepperpy.ask_query")
    @retry_async(
        max_retries=3,
        retry_on=[RateLimitError, APIError, ConnectionError, TimeoutError],
    )
    async def ask_query(
        self,
        query: str,
        system_prompt: Optional[str] = None,
        stream: bool = False,
        cache: bool = True,
        **context,
    ) -> Union[str, AsyncIterator[str]]:
        """Ask a question and get a response.

        Args:
            query: The question to ask
            system_prompt: Optional system prompt to provide context
            stream: Whether to stream the response
            cache: Whether to cache the response
            **context: Additional context parameters for execution

        Returns:
            Response from the system, or AsyncIterator of response chunks if streaming

        Raises:
            PluginError: If an error occurs during execution
        """
        # This method is designed to be cached when cache=True
        if not cache:
            # If caching is disabled, create a unique part for the key
            context["_nocache"] = time.time()

        # Create execution context
        exec_context = context.copy()
        exec_context.update(self._context)

        if system_prompt:
            exec_context["system_prompt"] = system_prompt

        # Get orchestrator and execute
        try:
            orchestrator = self._ensure_orchestrator()

            if stream:
                # Return streaming iterator
                return orchestrator.stream(query, exec_context)

            response = await orchestrator.execute(query, exec_context)
            return response
        except Exception as e:
            try:
                return self._handle_error(e)
            except Exception as original_error:
                logger.error(f"Error in ask_query: {original_error}")
                if isinstance(original_error, PluginError):
                    raise
                raise PluginError(
                    f"Error processing query: {original_error}"
                ) from original_error

    @cached(namespace="pepperpy.process_content", key_params=["content", "instruction"])
    @retry_async(strategy=retry_strategy.exponential_backoff)
    async def process_content(
        self,
        content: Any,
        instruction: Optional[str] = None,
        content_type: Optional[str] = None,
        cache: bool = True,
        **options,
    ) -> Any:
        """Process content using the appropriate plugin.

        Args:
            content: Content to process (can be text, file path, or data)
            instruction: Processing instruction or transformation to apply
            content_type: Optional explicit content type, auto-detected if not provided
            cache: Whether to cache the result
            **options: Additional processing options

        Returns:
            Processed content

        Raises:
            PluginError: If an error occurs during processing
        """
        # This method is designed to be cached when cache=True
        if not cache:
            # If caching is disabled, create a unique part for the key
            options["_nocache"] = time.time()

        # Create context
        context = options.copy()
        context.update(self._context)

        # Auto-detect content type if not provided
        detected_type = content_type or detect_content_type(content)
        context["content_type"] = detected_type

        # Prepare instruction-based query if provided
        if instruction:
            query = f"process this {detected_type}: {instruction}"
        else:
            query = f"process this {detected_type}"

        try:
            # Use orchestrator to route to appropriate processor
            orchestrator = self._ensure_orchestrator()
            result = await orchestrator.process(content, query, context)
            return result
        except Exception as e:
            try:
                return self._handle_error(e)
            except Exception as original_error:
                logger.error(f"Error in process_content: {original_error}")
                if isinstance(original_error, PluginError):
                    raise
                raise PluginError(
                    f"Error processing content: {original_error}"
                ) from original_error

    @cached(namespace="pepperpy.create_content")
    @retry_async(strategy=retry_strategy.exponential_backoff)
    async def create_content(
        self,
        description: str,
        format: Optional[str] = None,
        style: Optional[str] = None,
        cache: bool = True,
        **options,
    ) -> Any:
        """Create content based on a description.

        Args:
            description: Description of the content to create
            format: Desired format for the content (e.g., "markdown", "html", "json")
            style: Style or tone for the content
            cache: Whether to cache the result
            **options: Additional creation options

        Returns:
            Created content

        Raises:
            PluginError: If an error occurs during content creation
        """
        # This method is designed to be cached when cache=True
        if not cache:
            # If caching is disabled, create a unique part for the key
            options["_nocache"] = time.time()

        # Create context
        context = options.copy()
        context.update(self._context)

        if format:
            context["format"] = format
        if style:
            context["style"] = style

        # Create query for orchestrator
        if format:
            query = f"create {format} content: {description}"
        else:
            query = f"create content: {description}"

        try:
            # Use orchestrator to route to appropriate creator
            orchestrator = self._ensure_orchestrator()
            result = await orchestrator.create(query, context)
            return result
        except Exception as e:
            try:
                return self._handle_error(e)
            except Exception as original_error:
                logger.error(f"Error in create_content: {original_error}")
                if isinstance(original_error, PluginError):
                    raise
                raise PluginError(
                    f"Error creating content: {original_error}"
                ) from original_error

    @cached(namespace="pepperpy.analyze_data")
    @retry_async(max_retries=2)
    async def analyze_data(
        self,
        data: Any,
        instruction: str,
        format: Optional[str] = None,
        cache: bool = True,
        **options,
    ) -> Any:
        """Analyze data and extract insights.

        Args:
            data: Data to analyze (can be structured data, text, or file path)
            instruction: Analysis instruction or question about the data
            format: Desired format for the analysis results (e.g., "text", "json")
            cache: Whether to cache the result
            **options: Additional analysis options

        Returns:
            Analysis results

        Raises:
            PluginError: If an error occurs during analysis
        """
        # This method is designed to be cached when cache=True
        if not cache:
            # If caching is disabled, create a unique part for the key
            options["_nocache"] = time.time()

        # Create context
        context = options.copy()
        context.update(self._context)

        # Auto-detect data type
        data_type = detect_content_type(data)
        context["data_type"] = data_type

        if format:
            context["format"] = format

        # Create query for orchestrator
        query = f"analyze this {data_type}: {instruction}"

        try:
            # Use orchestrator to route to appropriate analyzer
            orchestrator = self._ensure_orchestrator()
            result = await orchestrator.analyze(data, query, context)
            return result
        except Exception as e:
            try:
                return self._handle_error(e)
            except Exception as original_error:
                logger.error(f"Error in analyze_data: {original_error}")
                if isinstance(original_error, PluginError):
                    raise
                raise PluginError(
                    f"Error analyzing data: {original_error}"
                ) from original_error

    async def initialize(self) -> None:
        """Initialize the framework and providers.

        This method should be called before using the framework or will be
        called automatically when entering the async context manager.
        """
        # Initialize framework if necessary
        if not _framework_initialized:
            await init_framework()

        # Initialize all registered providers
        for provider in self._providers.values():
            if not provider.initialized:
                await provider.initialize()

        # Initialize specific providers if set
        for provider in [
            self._llm_provider,
            self._rag_provider,
            self._tts_provider,
            self._embeddings_provider,
            self._content_provider,
            self._workflow_provider,
        ]:
            if provider and not provider.initialized:
                await provider.initialize()

        self._initialized = True

    async def cleanup(self) -> None:
        """Clean up resources and providers."""
        for provider in list(self._providers.values()):
            await provider.cleanup()

        # Clean up specific providers
        for provider in [
            self._llm_provider,
            self._rag_provider,
            self._tts_provider,
            self._embeddings_provider,
            self._content_provider,
            self._workflow_provider,
        ]:
            if provider:
                await provider.cleanup()

        self._initialized = False

    @property
    def available_plugins(self) -> Dict[str, List[str]]:
        """Get available plugins.

        Returns:
            Dictionary mapping plugin types to lists of provider types
        """
        return scan_available_plugins()

    def enable_hot_reload(self, enabled: bool = True) -> Self:
        """Enable or disable hot reloading of plugins.

        Args:
            enabled: Whether to enable hot reloading

        Returns:
            Self for chaining
        """
        enable_hot_reload(enabled)
        return self

    def enable_autodiscovery(self, enabled: bool = True) -> Self:
        """Enable or disable automatic discovery of plugins.

        Args:
            enabled: Whether to enable autodiscovery

        Returns:
            Self for chaining
        """
        set_autodiscovery(enabled)
        return self

    def clear_cache(
        self, namespace: Optional[str] = None, pattern: Optional[str] = None
    ) -> int:
        """Clear cached results.

        Args:
            namespace: Optional cache namespace to clear
            pattern: Optional pattern to match cache keys

        Returns:
            Number of cache entries cleared
        """
        return invalidate_cache(namespace=namespace, pattern=pattern)

    def get_cache_stats(self, namespace: Optional[str] = None) -> Dict[str, Any]:
        """Get cache statistics.

        Args:
            namespace: Optional cache namespace

        Returns:
            Dictionary of cache statistics
        """
        cache = get_result_cache(namespace=namespace or "pepperpy")
        return cache.get_stats()

    async def stream_chat(
        self,
        message: str,
        history: Optional[List[Dict[str, str]]] = None,
        system_prompt: Optional[str] = None,
    ) -> AsyncIterator[str]:
        """Stream chat responses.

        This is a convenience method that streams responses from a chat model.

        Args:
            message: User message
            history: Optional chat history
            system_prompt: Optional system prompt

        Returns:
            Async iterator with response chunks

        Raises:
            PluginError: If provider not configured or error occurs
        """
        if not self._llm_provider:
            raise PluginError("LLM provider not configured")

        # Create chat builder
        builder = self.chat

        # Add system prompt if provided
        if system_prompt:
            builder = builder.with_system(system_prompt)

        # Add history if provided
        if history:
            for msg in history:
                if msg.get("role") == "user":
                    builder = builder.with_user(msg["content"])
                elif msg.get("role") == "assistant":
                    builder = builder.with_assistant(msg["content"])
                elif msg.get("role") == "system":
                    builder = builder.with_system(msg["content"])

        # Add current message
        builder = builder.with_user(message)

        # Stream response
        async for chunk in builder.stream():
            yield chunk.content

    @property
    def llm(self) -> LLMBuilder:
        """Get the LLM builder.

        Returns:
            LLM builder for configuring LLM operations
        """
        if not self._llm_provider:
            raise ValueError("LLM provider not configured. Call with_llm() first.")
        return LLMBuilder(self._llm_provider)

    async def add_documents(self, docs: Union[Document, List[Document]]) -> None:
        """Add documents to the RAG context.

        Args:
            docs: Document or list of documents to add
        """
        if not self._rag_provider:
            raise ValueError("RAG provider not configured. Call with_rag() first.")
        await self._rag_provider.store(docs)

    async def search(
        self,
        query: Union[str, Query],
        limit: int = 5,
        **kwargs: Any,
    ) -> List[RetrievalResult]:
        """Search for relevant documents.

        Args:
            query: Search query text or Query object
            limit: Maximum number of results to return
            **kwargs: Additional search parameters

        Returns:
            List of search results
        """
        if not self._rag_provider:
            raise ValueError("RAG provider not configured. Call with_rag() first.")
        results = await self._rag_provider.search(query, limit=limit, **kwargs)
        return cast(List[RetrievalResult], list(results))

    async def get_document(self, doc_id: str) -> Optional[Document]:
        """Get a document by ID.

        Args:
            doc_id: ID of the document to get

        Returns:
            The document if found, None otherwise
        """
        if not self._rag_provider:
            raise ValueError("RAG provider not configured. Call with_rag() first.")
        return await self._rag_provider.get(doc_id)

    @property
    def chat(self) -> ChatBuilder:
        """Get chat builder for interaction.

        Returns:
            ChatBuilder instance

        Raises:
            ValidationError: If LLM provider is not configured
        """
        if not self._llm_provider:
            raise ValidationError("LLM provider not configured. Call with_llm() first.")
        return ChatBuilder(self._llm_provider)

    @property
    def tts(self) -> TTSBuilder:
        """Get TTS builder."""
        if not self._tts_provider:
            raise ValueError("TTS provider not configured. Call with_tts() first.")
        return TTSBuilder(self._tts_provider)

    @property
    def content(self) -> ContentBuilder:
        """Get content builder.

        Returns:
            Content builder instance

        Raises:
            RuntimeError: If LLM provider not configured
        """
        if not self._llm_provider:
            raise RuntimeError("LLM provider not configured. Call with_llm() first.")
        return ContentBuilder(self._llm_provider)

    @property
    def text(self) -> TextBuilder:
        """Get text builder.

        Returns:
            Text builder instance

        Raises:
            RuntimeError: If LLM provider not configured
        """
        if not self._llm_provider:
            raise RuntimeError("LLM provider not configured. Call with_llm() first.")
        return TextBuilder(self._llm_provider)

    @property
    def document(self) -> DocumentBuilder:
        """Get document builder.

        Returns:
            Document builder instance

        Raises:
            RuntimeError: If workflow support not configured
        """
        if not self._workflow_provider:
            raise RuntimeError(
                "Workflow support not configured. Call with_workflow() first."
            )
        return DocumentBuilder(self._workflow_provider)

    @property
    def rag(self) -> RAGBuilder:
        """Get RAG builder.

        Returns:
            RAG builder instance

        Raises:
            RuntimeError: If RAG provider not configured
        """
        if not self._rag_provider:
            raise RuntimeError("RAG provider not configured. Call with_rag() first.")
        return RAGBuilder(self._rag_provider)


# Convenience functions for the root module
async def ask(query: str, **kwargs: Any) -> str:
    """Ask a question using the default PepperPy instance.

    Args:
        query: The question to ask
        **kwargs: Additional parameters for execution

    Returns:
        Response from the system
    """
    instance = PepperPy.get_instance()
    return await instance.ask_query(query, **kwargs)


async def process(
    content: Any, instruction: Optional[str] = None, **kwargs: Any
) -> Any:
    """Process content using the default PepperPy instance.

    Args:
        content: Content to process
        instruction: Processing instruction
        **kwargs: Additional parameters for execution

    Returns:
        Processed content
    """
    instance = PepperPy.get_instance()
    return await instance.process_content(content, instruction, **kwargs)


async def create(description: str, format: Optional[str] = None, **kwargs: Any) -> Any:
    """Create content using the default PepperPy instance.

    Args:
        description: Description of content to create
        format: Desired format
        **kwargs: Additional parameters for execution

    Returns:
        Created content
    """
    instance = PepperPy.get_instance()
    return await instance.create_content(description, format, **kwargs)


async def analyze(data: Any, instruction: str, **kwargs: Any) -> Any:
    """Analyze data using the default PepperPy instance.

    Args:
        data: Data to analyze
        instruction: Analysis instruction
        **kwargs: Additional parameters for execution

    Returns:
        Analysis result
    """
    instance = PepperPy.get_instance()
    return await instance.analyze_data(data, instruction, **kwargs)


# Make root module convenience functions available directly
__all__ = [
    "PepperPy",
    "init_framework",
    "ask",
    "process",
    "create",
    "analyze",
]
