#!/usr/bin/env python
"""
PepperPy API usage example.

This demonstrates how to use the main PepperPy API with a mock implementation.
"""

import asyncio
from collections.abc import AsyncIterator
from typing import Any, Dict, List, Optional, Union


# Mock classes to simulate PepperPy API functionality
class Message:
    """Message in a conversation."""

    def __init__(self, role: str, content: str):
        self.role = role
        self.content = content


class MessageRole:
    """Message roles."""

    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"


class GenerationResult:
    """Result of text generation."""

    def __init__(self, content: str):
        self.content = content


class GenerationChunk:
    """Chunk of generated text in streaming mode."""

    def __init__(self, content: str):
        self.content = content


class Document:
    """Document for RAG."""

    def __init__(self, text: str, metadata: Optional[Dict[str, Any]] = None):
        self.text = text
        self.metadata = metadata or {}
        self.id = f"doc_{hash(text) % 10000}"


class RetrievalResult:
    """Result of RAG retrieval."""

    def __init__(self, document: Document, score: float):
        self.document = document
        self.score = score


class MockLLMProvider:
    """Mock LLM provider."""

    def __init__(self, **config):
        self.config = config
        self.initialized = False

    async def initialize(self) -> None:
        """Initialize the provider."""
        print(f"Initializing LLM provider with config: {self.config}")
        self.initialized = True

    async def generate(self, messages: List[Message], **kwargs) -> GenerationResult:
        """Generate text based on messages."""
        last_message = next(
            (m for m in reversed(messages) if m.role == MessageRole.USER), None
        )

        if not last_message:
            return GenerationResult("I don't have anything to respond to.")

        prompt = last_message.content.lower()

        if "hello" in prompt or "hi" in prompt:
            return GenerationResult("Hello! How can I help you today?")
        elif "weather" in prompt:
            return GenerationResult(
                "I'm sorry, I can't check the weather in this mock example."
            )
        elif "joke" in prompt:
            return GenerationResult(
                "Why don't scientists trust atoms? Because they make up everything!"
            )
        elif "python" in prompt:
            return GenerationResult(
                "Python is a high-level programming language known for its readability."
            )
        else:
            return GenerationResult(
                f"I received your request about '{prompt}'. This is a mock response."
            )

    async def stream(
        self, messages: List[Message], **kwargs
    ) -> AsyncIterator[GenerationChunk]:
        """Stream text generation results."""
        result = await self.generate(messages, **kwargs)
        words = result.content.split()
        for word in words:
            yield GenerationChunk(word + " ")
            await asyncio.sleep(0.1)

    async def cleanup(self) -> None:
        """Clean up resources."""
        print("Cleaning up LLM provider")
        self.initialized = False


class MockRAGProvider:
    """Mock RAG provider."""

    def __init__(self, **config):
        self.config = config
        self.initialized = False
        self.documents = {}

    async def initialize(self) -> None:
        """Initialize the provider."""
        print(f"Initializing RAG provider with config: {self.config}")
        self.initialized = True

    async def store(self, doc: Union[Document, List[Document]]) -> None:
        """Store documents."""
        if isinstance(doc, list):
            for d in doc:
                self.documents[d.id] = d
        else:
            self.documents[doc.id] = doc

    async def search(
        self, query: str, limit: int = 5, **kwargs
    ) -> List[RetrievalResult]:
        """Search for documents."""
        print(f"Searching for: {query} (limit: {limit})")

        results = []
        for doc in self.documents.values():
            query_words = set(query.lower().split())
            doc_words = set(doc.text.lower().split())
            overlap = query_words.intersection(doc_words)

            if overlap:
                score = len(overlap) / len(query_words)
                results.append(RetrievalResult(doc, score))

        results.sort(key=lambda x: x.score, reverse=True)
        return results[:limit]

    async def cleanup(self) -> None:
        """Clean up resources."""
        print("Cleaning up RAG provider")
        self.initialized = False


class ChatBuilder:
    """Builder for chat interactions."""

    def __init__(self, provider: MockLLMProvider):
        self._provider = provider
        self._messages = []
        self._temperature = None
        self._max_tokens = None

    def with_system(self, message: str) -> "ChatBuilder":
        """Add system message."""
        self._messages.append(Message(role=MessageRole.SYSTEM, content=message))
        return self

    def with_user(self, message: str) -> "ChatBuilder":
        """Add user message."""
        self._messages.append(Message(role=MessageRole.USER, content=message))
        return self

    def with_assistant(self, message: str) -> "ChatBuilder":
        """Add assistant message."""
        self._messages.append(Message(role=MessageRole.ASSISTANT, content=message))
        return self

    def with_temperature(self, temperature: float) -> "ChatBuilder":
        """Set temperature for generation."""
        self._temperature = temperature
        return self

    def with_max_tokens(self, max_tokens: int) -> "ChatBuilder":
        """Set maximum tokens for generation."""
        self._max_tokens = max_tokens
        return self

    async def generate(self) -> GenerationResult:
        """Generate response."""
        if not self._messages:
            raise ValueError("No messages configured for generation")

        kwargs = {}
        if self._temperature is not None:
            kwargs["temperature"] = self._temperature
        if self._max_tokens is not None:
            kwargs["max_tokens"] = self._max_tokens

        return await self._provider.generate(self._messages, **kwargs)

    async def stream(self) -> AsyncIterator[GenerationChunk]:
        """Generate response in streaming mode."""
        if not self._messages:
            raise ValueError("No messages configured for generation")

        kwargs = {}
        if self._temperature is not None:
            kwargs["temperature"] = self._temperature
        if self._max_tokens is not None:
            kwargs["max_tokens"] = self._max_tokens

        async for chunk in self._provider.stream(self._messages, **kwargs):
            yield chunk


class TextBuilder:
    """Builder for text generation."""

    def __init__(self, provider: MockLLMProvider):
        self._provider = provider
        self._prompt = ""
        self._system_prompt = ""
        self._temperature = 0.7
        self._format = None

    def with_prompt(self, prompt: str) -> "TextBuilder":
        """Set prompt for generation."""
        self._prompt = prompt
        return self

    def with_system_prompt(self, prompt: str) -> "TextBuilder":
        """Set system prompt for generation."""
        self._system_prompt = prompt
        return self

    def with_temperature(self, temperature: float) -> "TextBuilder":
        """Set temperature for generation."""
        self._temperature = temperature
        return self

    def as_markdown(self) -> "TextBuilder":
        """Format output as markdown."""
        self._format = "markdown"
        return self

    async def generate(self) -> str:
        """Generate text."""
        messages = []
        if self._system_prompt:
            messages.append(
                Message(role=MessageRole.SYSTEM, content=self._system_prompt)
            )
        messages.append(Message(role=MessageRole.USER, content=self._prompt))

        result = await self._provider.generate(messages, temperature=self._temperature)
        return result.content


class ContentBuilder:
    """Builder for content generation."""

    def __init__(self, provider: MockLLMProvider):
        self._provider = provider
        self._topic = ""
        self._type = ""
        self._style = []
        self._tone = "neutral"
        self._max_length = None

    def blog_post(self, topic: str) -> "ContentBuilder":
        """Set content type to blog post."""
        self._type = "blog_post"
        self._topic = topic
        return self

    def informative(self) -> "ContentBuilder":
        """Set style to informative."""
        self._style.append("informative")
        return self

    def with_tone(self, tone: str) -> "ContentBuilder":
        """Set content tone."""
        self._tone = tone
        return self

    def with_max_length(self, words: int) -> "ContentBuilder":
        """Set maximum content length in words."""
        self._max_length = words
        return self

    async def generate(self) -> Dict[str, Any]:
        """Generate content."""
        style_str = ", ".join(self._style) if self._style else self._tone
        system_prompt = (
            f"You are a professional writer specializing in {style_str} content."
        )

        if self._max_length:
            system_prompt += f" Keep the content under {self._max_length} words."

        messages = [
            Message(role=MessageRole.SYSTEM, content=system_prompt),
            Message(
                role=MessageRole.USER,
                content=f"Write a {self._type} about: {self._topic}",
            ),
        ]

        result = await self._provider.generate(messages)

        return {
            "title": self._topic,
            "content": result.content,
            "metadata": {
                "type": self._type,
                "style": style_str,
                "word_count": len(result.content.split()),
            },
        }


class RAGBuilder:
    """Builder for RAG operations."""

    def __init__(self, provider: MockRAGProvider):
        self._provider = provider
        self._documents = []
        self._query = ""
        self._limit = 5

    def add_documents(self, documents: Union[str, List[str]]) -> "RAGBuilder":
        """Add documents to store."""
        if isinstance(documents, str):
            documents = [documents]

        self._documents.extend(documents)
        return self

    def search(self, query: str) -> "RAGBuilder":
        """Set search query."""
        self._query = query
        return self

    def limit(self, limit: int) -> "RAGBuilder":
        """Set maximum number of results."""
        self._limit = limit
        return self

    async def store(self) -> None:
        """Store documents."""
        if not self._documents:
            raise ValueError("No documents added")

        for text in self._documents:
            doc = Document(text=text)
            await self._provider.store(doc)

    async def execute(self) -> List[RetrievalResult]:
        """Execute search query."""
        if not self._query:
            raise ValueError("No query set")

        results = await self._provider.search(self._query, limit=self._limit)
        return results


class PepperPy:
    """Mock PepperPy framework class."""

    def __init__(self):
        self._llm_provider = None
        self._rag_provider = None
        self._providers = {}
        self._initialized = False

    def with_plugin(self, plugin_type: str, provider_type: str, **config) -> "PepperPy":
        """Configure a plugin."""
        if plugin_type == "llm":
            self._llm_provider = MockLLMProvider(**config)
            self._providers["llm"] = self._llm_provider
        elif plugin_type == "rag":
            self._rag_provider = MockRAGProvider(**config)
            self._providers["rag"] = self._rag_provider
        return self

    @property
    def chat(self) -> ChatBuilder:
        """Get chat builder."""
        if not self._llm_provider:
            raise ValueError("LLM provider not configured. Call with_plugin() first.")
        return ChatBuilder(self._llm_provider)

    @property
    def text(self) -> TextBuilder:
        """Get text builder."""
        if not self._llm_provider:
            raise ValueError("LLM provider not configured. Call with_plugin() first.")
        return TextBuilder(self._llm_provider)

    @property
    def content(self) -> ContentBuilder:
        """Get content builder."""
        if not self._llm_provider:
            raise ValueError("LLM provider not configured. Call with_plugin() first.")
        return ContentBuilder(self._llm_provider)

    @property
    def rag(self) -> RAGBuilder:
        """Get RAG builder."""
        if not self._rag_provider:
            raise ValueError("RAG provider not configured. Call with_plugin() first.")
        return RAGBuilder(self._rag_provider)

    async def ask_query(self, query: str, **kwargs) -> str:
        """Ask a question and get a response."""
        if not self._llm_provider:
            raise ValueError("LLM provider not configured. Call with_plugin() first.")

        messages = []
        if "system_prompt" in kwargs:
            messages.append(
                Message(role=MessageRole.SYSTEM, content=kwargs["system_prompt"])
            )

        messages.append(Message(role=MessageRole.USER, content=query))

        result = await self._llm_provider.generate(messages)
        return result.content

    async def initialize(self) -> None:
        """Initialize providers."""
        for provider in self._providers.values():
            await provider.initialize()

        self._initialized = True

    async def cleanup(self) -> None:
        """Clean up resources."""
        for provider in self._providers.values():
            await provider.cleanup()

        self._initialized = False

    async def __aenter__(self) -> "PepperPy":
        """Enter async context."""
        await self.initialize()
        return self

    async def __aexit__(self, *args) -> None:
        """Exit async context."""
        await self.cleanup()


# Convenience function to avoid importing the actual implementation
async def ask(query: str, **kwargs) -> str:
    """Ask a question using a temporary PepperPy instance."""
    pp = PepperPy()
    pp.with_plugin("llm", "openai")

    async with pp:
        return await pp.ask_query(query, **kwargs)


async def basic_example() -> None:
    """Basic example using PepperPy API."""
    print("\n=== Basic PepperPy Example ===")

    # Create and configure a PepperPy instance
    pp = PepperPy()

    # Configure with OpenAI provider
    pp.with_plugin("llm", "openai")

    # Use context manager for proper initialization and cleanup
    async with pp:
        # Simple question using ask_query
        print("\n--- Simple Question ---")
        question = "What is Python programming language?"
        print(f"Question: {question}")
        answer = await pp.ask_query(question)
        print(f"Answer: {answer}")

        # Chat with context using the chat builder
        print("\n--- Chat with Context ---")
        result = (
            await pp.chat.with_system("You are a helpful assistant.")
            .with_user("Tell me a joke about programming.")
            .generate()
        )

        print(f"Response: {result.content}")


async def rag_example() -> None:
    """Example of using RAG with PepperPy."""
    print("\n=== RAG Example ===")

    # Create PepperPy instance
    pp = PepperPy()

    # Configure providers
    pp.with_plugin("llm", "openai")
    pp.with_plugin("rag", "basic")

    # Use context manager
    async with pp:
        # Add sample documents using the RAG builder
        print("\n--- Adding Documents ---")
        await pp.rag.add_documents(
            [
                "Python is a high-level programming language known for its readability and versatility.",
                "PepperPy is a Python framework for AI applications that provides a unified interface.",
                "The YAML configuration system in PepperPy allows for flexible and modular configuration.",
                "Plugins in PepperPy follow a provider pattern with common lifecycle methods.",
            ]
        ).store()

        # Search using the RAG builder
        print("\n--- Searching Documents ---")
        query = "What is PepperPy?"
        print(f"Query: {query}")

        results = await pp.rag.search(query).limit(2).execute()

        for i, result in enumerate(results):
            print(f"\nResult {i+1} (Score: {result.score:.2f})")
            print(f"Text: {result.document.text}")


async def builder_pattern_example() -> None:
    """Example of using the builder pattern in PepperPy."""
    print("\n=== Builder Pattern Example ===")

    # Create PepperPy instance
    pp = PepperPy()

    # Configure providers
    pp.with_plugin("llm", "openai", temperature=0.7)

    # Use context manager
    async with pp:
        # Using text builder
        print("\n--- Text Builder ---")
        response = (
            await pp.text.with_prompt("Explain what a Python decorator is")
            .with_system_prompt("You are a Python expert. Be concise.")
            .with_temperature(0.5)
            .as_markdown()
            .generate()
        )

        print(f"Response: {response}")

        # Using content builder
        print("\n--- Content Builder ---")
        article = (
            await pp.content.blog_post("Python Type Hints")
            .informative()
            .with_tone("professional")
            .with_max_length(300)
            .generate()
        )

        print(f"Title: {article['title']}")
        print(f"Content: {article['content'][:150]}...")


async def streaming_example() -> None:
    """Example of streaming responses with PepperPy."""
    print("\n=== Streaming Example ===")

    # Create PepperPy instance
    pp = PepperPy()

    # Configure providers
    pp.with_plugin("llm", "openai")

    # Use context manager
    async with pp:
        # Streaming with chat builder
        print("\n--- Streaming Chat ---")
        print("Response: ", end="", flush=True)

        stream = (
            pp.chat.with_system("You are a concise assistant.")
            .with_user("Explain async/await in one sentence.")
            .stream()
        )

        async for chunk in stream:
            print(chunk.content, end="", flush=True)

        print("\n")


async def convenience_functions_example() -> None:
    """Example of using the convenience functions."""
    print("\n=== Convenience Functions Example ===")

    # Using the global ask function
    print("\n--- Global Ask ---")
    question = "What is the meaning of life?"
    print(f"Question: {question}")

    # This uses a default PepperPy instance
    answer = await ask(question)
    print(f"Answer: {answer}")


async def main() -> None:
    """Run all examples."""
    print("=== PepperPy API Examples ===")

    # Run examples
    try:
        await basic_example()
        await rag_example()
        await builder_pattern_example()
        await streaming_example()
        await convenience_functions_example()

        print("\nExamples completed successfully!")
    except Exception as e:
        print(f"\nError running examples: {e}")


if __name__ == "__main__":
    asyncio.run(main())
