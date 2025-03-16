"""Generation stage for the RAG pipeline."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from pepperpy.core.errors import PepperPyError
from pepperpy.llm.utils import Message, Prompt, Response
from pepperpy.rag.document.core import DocumentChunk


@dataclass
class GenerationResult:
    """Result from the generation stage."""

    text: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    usage: Dict[str, int] = field(default_factory=dict)


@dataclass
class GenerationStageConfig:
    """Configuration for the generation stage."""

    provider: str
    model: str
    temperature: float = 0.7
    max_tokens: Optional[int] = None
    stop: Optional[List[str]] = None
    system_message: Optional[str] = None


class GenerationProvider(ABC):
    """Base class for generation providers."""

    @abstractmethod
    async def generate(
        self,
        prompt: Prompt,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Response:
        """Generate a response from a prompt.

        Args:
            prompt: The prompt to generate from
            metadata: Optional metadata

        Returns:
            Generated response

        Raises:
            PepperpyError: If generation fails
        """
        pass


class GenerationStage:
    """Stage for generating responses using an LLM."""

    def __init__(self, config: GenerationStageConfig):
        """Initialize the stage.

        Args:
            config: Stage configuration
        """
        self.config = config

    async def process(
        self,
        query: str,
        chunks: List[DocumentChunk],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Response:
        """Process the query and chunks to generate a response.

        Args:
            query: User query
            chunks: Retrieved document chunks
            metadata: Optional metadata

        Returns:
            Generated response

        Raises:
            PepperpyError: If generation fails
        """
        try:
            # Create messages
            messages = []

            # Add system message if provided
            if self.config.system_message:
                messages.append(
                    Message(role="system", content=self.config.system_message)
                )

            # Add context from chunks
            context = "\n\n".join(chunk.content for chunk in chunks)
            messages.append(
                Message(
                    role="system",
                    content=f"Context:\n{context}\n\nUse this context to answer the following question.",
                )
            )

            # Add user query
            messages.append(Message(role="user", content=query))

            # Create prompt
            prompt = Prompt(
                messages=messages,
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
                stop=self.config.stop,
                metadata=metadata or {},
            )

            # TODO: Call LLM provider to generate response
            # This should be implemented by the provider
            raise PepperPyError("Generation not implemented")

        except Exception as e:
            raise PepperPyError(f"Error in generation stage: {e}")


# Export all classes
__all__ = [
    "GenerationStageConfig",
    "GenerationProvider",
    "GenerationStage",
    "GenerationResult",
]
