"""PepperPy main module.

This module provides the main PepperPy class and builder classes for
working with LLMs, RAG, and other AI capabilities.
"""

from typing import (
    Any,
    AsyncIterator,
    Dict,
    List,
    Optional,
    Self,
    Union,
    cast,
)

from pepperpy.llm import (
    GenerationChunk,
    GenerationResult,
    LLMProvider,
    Message,
    MessageRole,
)
from pepperpy.rag import (
    Document,
    Query,
    RAGProvider,
    RetrievalResult,
)
from pepperpy.tts import TTSProvider
from pepperpy.workflow.base import (
    DocumentWorkflow,
    PipelineContext,
    WorkflowProvider,
)


class ChatBuilder:
    """Fluent builder for chat interactions."""

    def __init__(self, llm: LLMProvider) -> None:
        """Initialize chat builder.

        Args:
            llm: LLM provider to use
        """
        self._llm = llm
        self._messages: List[Message] = []
        self._temperature: float = 0.7
        self._max_tokens: Optional[int] = None

    def with_system(self, content: str) -> Self:
        """Add a system message.

        Args:
            content: Message content

        Returns:
            Self for chaining
        """
        self._messages.append(Message(role=MessageRole.SYSTEM, content=content))
        return self

    def with_user(self, content: str) -> Self:
        """Add a user message.

        Args:
            content: Message content

        Returns:
            Self for chaining
        """
        self._messages.append(Message(role=MessageRole.USER, content=content))
        return self

    def with_assistant(self, content: str) -> Self:
        """Add an assistant message.

        Args:
            content: Message content

        Returns:
            Self for chaining
        """
        self._messages.append(Message(role=MessageRole.ASSISTANT, content=content))
        return self

    def with_message(self, role: Union[str, MessageRole], content: str) -> Self:
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

    def with_temperature(self, temperature: float) -> Self:
        """Set temperature for generation.

        Args:
            temperature: Temperature value between 0 and 1

        Returns:
            Self for chaining

        Raises:
            ValueError: If temperature is not between 0 and 1
        """
        if not 0 <= temperature <= 1:
            raise ValueError("Temperature must be between 0 and 1")
        self._temperature = temperature
        return self

    def with_max_tokens(self, max_tokens: Optional[int]) -> Self:
        """Set maximum tokens for generation.

        Args:
            max_tokens: Maximum tokens to generate, or None for no limit

        Returns:
            Self for chaining

        Raises:
            ValueError: If max_tokens is negative
        """
        if max_tokens is not None and max_tokens < 0:
            raise ValueError("max_tokens must be positive or None")
        self._max_tokens = max_tokens
        return self

    async def generate(self, **kwargs: Any) -> GenerationResult:
        """Generate response from messages.

        Args:
            **kwargs: Additional generation options

        Returns:
            Generation result

        Raises:
            ValueError: If no messages have been added
        """
        if not self._messages:
            raise ValueError(
                "No messages added. Add at least one message before generating."
            )

        generation_kwargs = {"temperature": self._temperature, **kwargs}
        if self._max_tokens is not None:
            generation_kwargs["max_tokens"] = self._max_tokens

        return await self._llm.generate(self._messages, **generation_kwargs)

    async def stream(self, **kwargs: Any) -> AsyncIterator[GenerationChunk]:
        """Stream response from messages.

        Args:
            **kwargs: Additional generation options

        Returns:
            AsyncIterator yielding generation chunks

        Raises:
            ValueError: If no messages have been added
        """
        if not self._messages:
            raise ValueError(
                "No messages added. Add at least one message before streaming."
            )

        generation_kwargs = {"temperature": self._temperature, **kwargs}
        if self._max_tokens is not None:
            generation_kwargs["max_tokens"] = self._max_tokens

        stream = cast(
            AsyncIterator[GenerationChunk],
            self._llm.stream(self._messages, **generation_kwargs),
        )
        async for chunk in stream:
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

        stream = cast(
            AsyncIterator[GenerationChunk],
            self._llm.stream(
                messages,
                temperature=self._temperature,
                max_tokens=self._max_tokens,
                stop_sequences=self._stop_sequences if self._stop_sequences else None,
            ),
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


class PepperPy:  # type: ignore[attr-defined]
    """Main class for interacting with the PepperPy framework."""

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        """Initialize PepperPy.

        Args:
            config: Optional configuration dictionary
        """
        self._config = config or {}
        self._llm_provider: Optional[LLMProvider] = None
        self._rag_provider: Optional[RAGProvider] = None
        self._workflow_provider: Optional[WorkflowProvider] = None
        self._tts_provider: Optional[TTSProvider] = None

    def with_rag(self, provider: Optional[RAGProvider] = None) -> "PepperPy":
        """Configure RAG support.

        Args:
            provider: Optional RAG provider (uses InMemoryProvider if None)

        Returns:
            Self for chaining
        """
        if provider is None:
            provider = cast(RAGProvider, InMemoryProvider())
        self._rag_provider = provider
        return self

    def with_llm(self, provider: LLMProvider) -> "PepperPy":
        """Configure LLM support.

        Args:
            provider: LLM provider to use

        Returns:
            Self for chaining
        """
        self._llm_provider = provider
        return self

    def with_workflow(self, provider: WorkflowProvider) -> "PepperPy":
        """Configure workflow support.

        Args:
            provider: Workflow provider to use

        Returns:
            Self for chaining
        """
        self._workflow_provider = provider
        return self

    def with_tts(self, provider: TTSProvider) -> "PepperPy":
        """Configure TTS support.

        Args:
            provider: TTS provider to use

        Returns:
            Self for chaining
        """
        self._tts_provider = provider
        return self

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
        return list(cast(Sequence[RetrievalResult], results))

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
        """Get chat builder."""
        if not self._llm_provider:
            raise ValueError("LLM provider not configured. Call with_llm() first.")
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

    async def __aenter__(self) -> "PepperPy":
        """Enter async context.

        Returns:
            Self for use in context
        """
        if self._rag_provider:
            await self._rag_provider.initialize()
        if self._llm_provider:
            await self._llm_provider.initialize()
        if self._workflow_provider:
            await self._workflow_provider.initialize()
        if self._tts_provider:
            await self._tts_provider.initialize()
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Exit async context."""
        if self._rag_provider:
            await self._rag_provider.cleanup()
        if self._llm_provider:
            await self._llm_provider.cleanup()
        if self._workflow_provider:
            await self._workflow_provider.cleanup()
        if self._tts_provider:
            await self._tts_provider.cleanup()
