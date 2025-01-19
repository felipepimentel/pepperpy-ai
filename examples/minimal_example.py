"""Minimal example demonstrating text generation."""

import asyncio
from dataclasses import dataclass, field
from typing import Any, AsyncIterator


@dataclass
class LLMConfig:
    """LLM configuration."""

    model_name: str
    temperature: float = 0.7
    max_tokens: int = 100
    stop_sequences: list[str] | None = None
    model_kwargs: dict[str, Any] = field(default_factory=dict)


@dataclass
class LLMResponse:
    """LLM response."""

    text: str
    tokens_used: int
    finish_reason: str | None = None
    model_name: str | None = None


async def generate_text(prompt: str) -> LLMResponse:
    """Generate text using a simple mock LLM.
    
    Args:
        prompt: Input prompt
        
    Returns:
        Generated response
    """
    # Simulate text generation
    response = f"{prompt} continues with some generated text..."
    tokens = len(response.split())
    
    return LLMResponse(
        text=response,
        tokens_used=tokens,
        finish_reason="length",
        model_name="mock-model"
    )


async def stream_text(prompt: str) -> AsyncIterator[str]:
    """Stream text using a simple mock LLM.
    
    Args:
        prompt: Input prompt
        
    Returns:
        Async iterator of text chunks
    """
    words = prompt.split() + ["continues", "with", "some", "generated", "text..."]
    for word in words:
        yield word + " "
        await asyncio.sleep(0.2)  # Simulate streaming delay


async def main() -> None:
    """Run the example."""
    prompt = "The quick brown fox"
    
    # Generate text
    print(f"\nGenerating text for prompt: {prompt}")
    response = await generate_text(prompt)
    print(f"\nGenerated text: {response.text}")
    print(f"Tokens used: {response.tokens_used}")
    print(f"Model used: {response.model_name}")
    
    # Stream text
    print("\nStreaming text generation...")
    async for chunk in stream_text(prompt):
        print(chunk, end="", flush=True)
    print("\n")


if __name__ == "__main__":
    asyncio.run(main()) 