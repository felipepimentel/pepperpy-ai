#!/usr/bin/env python
"""LLM Providers Example using PepperPy.

Purpose:
    Demonstrate how to use different LLM providers in the refactored PepperPy library, including:
    - Configuring providers with API keys
    - Creating LLM instances
    - Generating text with different models
    - Using streaming responses
    - Working with different provider-specific parameters

Requirements:
    - Python 3.9+
    - PepperPy library
    - API keys for the providers you want to use

Usage:
    1. Install dependencies:
       poetry install

    2. Set environment variables:
       export OPENAI_API_KEY=your_openai_api_key
       export ANTHROPIC_API_KEY=your_anthropic_api_key
       # Or use .env file (see .env.example)

    3. Run the example:
       poetry run python examples/llm_providers.py

IMPORTANT: This is a demonstration of the intended API after refactoring.
Some methods shown here may not be fully implemented yet.
"""

import asyncio
import logging

# Import utility functions
from utils import check_api_keys, load_env, setup_logging

import pepperpy as pp

# Set up logger
logger = logging.getLogger(__name__)


async def openai_example() -> None:
    """Example of using the OpenAI provider.

    Demonstrates how to:
    - Create an OpenAI LLM instance
    - Generate text with different models
    - Use streaming responses
    - Configure provider-specific parameters

    Note: This demonstrates the intended API pattern after refactoring.
    """
    logger.info("Running OpenAI example")
    print("\n=== OpenAI Example ===\n")

    # Create an OpenAI LLM instance
    print("Creating OpenAI LLM instance...")
    logger.info("Creating OpenAI LLM instance")

    # Note: pp.llm.create is the intended public API after refactoring
    llm = await pp.llm.create(
        provider="openai",
        model="gpt-4o",
        temperature=0.7,
        max_tokens=500,
    )

    # Generate text
    prompt = "Write a short poem about artificial intelligence."
    print(f"Generating text with prompt: '{prompt}'")
    logger.info(f"Generating text with prompt: '{prompt}'")

    # Note: llm.generate is the intended API after refactoring
    result = await llm.generate(prompt)

    print("\nGenerated text:")
    print(result.text)

    # Generate with streaming
    print("\nGenerating with streaming...")
    logger.info("Generating with streaming")
    prompt = "List 5 benefits of using Python for AI development."

    print(f"Streaming response for prompt: '{prompt}'")
    print("\nStreaming response:")

    # Note: llm.generate_stream is the intended API after refactoring
    async for chunk in llm.generate_stream(prompt):
        print(chunk.text, end="", flush=True)
    print("\n")

    # Using a different model
    print("Using a different model (gpt-3.5-turbo)...")
    logger.info("Using a different model (gpt-3.5-turbo)")

    # Note: pp.llm.create with different model is the intended API
    llm_turbo = await pp.llm.create(
        provider="openai",
        model="gpt-3.5-turbo",
        temperature=0.5,
    )

    prompt = "Explain what an LLM is in one sentence."
    print(f"Generating with prompt: '{prompt}'")
    logger.info(f"Generating with prompt: '{prompt}'")

    result = await llm_turbo.generate(prompt)
    print("\nGenerated text:")
    print(result.text)


async def anthropic_example() -> None:
    """Example of using the Anthropic provider.

    Demonstrates how to:
    - Create an Anthropic LLM instance
    - Generate text with Claude models
    - Use streaming responses
    - Configure provider-specific parameters

    Note: This demonstrates the intended API pattern after refactoring.
    """
    logger.info("Running Anthropic example")
    print("\n=== Anthropic Example ===\n")

    # Create an Anthropic LLM instance
    print("Creating Anthropic LLM instance...")
    logger.info("Creating Anthropic LLM instance")

    # Note: pp.llm.create is the intended public API after refactoring
    llm = await pp.llm.create(
        provider="anthropic",
        model="claude-3-opus-20240229",
        temperature=0.7,
        max_tokens=500,
    )

    # Generate text
    prompt = "Write a short story about a robot learning to paint."
    print(f"Generating text with prompt: '{prompt}'")
    logger.info(f"Generating text with prompt: '{prompt}'")

    # Note: llm.generate is the intended API after refactoring
    result = await llm.generate(prompt)

    print("\nGenerated text:")
    print(result.text)

    # Generate with streaming
    print("\nGenerating with streaming...")
    logger.info("Generating with streaming")
    prompt = "Explain the concept of neural networks to a 10-year-old."

    print(f"Streaming response for prompt: '{prompt}'")
    print("\nStreaming response:")

    # Note: llm.generate_stream is the intended API after refactoring
    async for chunk in llm.generate_stream(prompt):
        print(chunk.text, end="", flush=True)
    print("\n")

    # Using a different model
    print("Using a different model (claude-3-sonnet)...")
    logger.info("Using a different model (claude-3-sonnet)")

    # Note: pp.llm.create with different model is the intended API
    llm_sonnet = await pp.llm.create(
        provider="anthropic",
        model="claude-3-sonnet-20240229",
        temperature=0.5,
    )

    prompt = "What are the key differences between Claude and GPT models?"
    print(f"Generating with prompt: '{prompt}'")
    logger.info(f"Generating with prompt: '{prompt}'")

    result = await llm_sonnet.generate(prompt)
    print("\nGenerated text:")
    print(result.text)


async def custom_provider_example() -> None:
    """Example of using a custom provider configuration.

    Demonstrates how to:
    - Configure a custom provider
    - Create an LLM instance with the custom provider
    - Generate text with the custom provider

    Note: This demonstrates the intended API pattern after refactoring.
    """
    logger.info("Running custom provider example")
    print("\n=== Custom Provider Example ===\n")

    # Configure a custom provider
    print("Configuring custom provider...")
    logger.info("Configuring custom provider")

    # Note: pp.llm.configure is the intended public API after refactoring
    pp.llm.configure(
        provider="custom_api",
        api_url="https://api.example.com/v1/completions",
        api_key="your_api_key",
        headers={
            "Content-Type": "application/json",
            "User-Agent": "PepperPy/1.0",
        },
        default_params={
            "temperature": 0.8,
            "max_tokens": 1000,
        },
    )

    # Create an LLM instance with the custom provider
    print("Creating LLM instance with custom provider...")
    logger.info("Creating LLM instance with custom provider")

    # Note: pp.llm.create with custom provider is the intended API
    llm = await pp.llm.create(
        provider="custom_api",
        model="custom-model",
    )

    # Generate text
    prompt = "Explain the concept of API integration."
    print(f"Generating text with prompt: '{prompt}'")
    logger.info(f"Generating text with prompt: '{prompt}'")

    # Note: llm.generate is the intended API after refactoring
    # This is a simulated response since we're not actually connecting to a real API
    print("\nSimulated response from custom provider:")
    print(
        "API integration is the process of connecting different software applications"
    )
    print("to share data and functionality. This allows systems to work together")
    print("seamlessly, enabling automation and enhanced capabilities across platforms.")


async def main() -> None:
    """Run the LLM provider examples.

    Runs examples for different LLM providers, including OpenAI, Anthropic,
    and a custom provider configuration.
    """
    # Load environment variables from .env file
    load_env()

    # Set up logging
    setup_logging()

    # Check for required API keys
    required_keys = {
        "OPENAI_API_KEY": "OpenAI example",
        "ANTHROPIC_API_KEY": "Anthropic example",
    }
    check_api_keys(required_keys)

    logger.info("Starting LLM provider examples")

    try:
        # Run examples
        await openai_example()
        await anthropic_example()
        await custom_provider_example()

        logger.info("LLM provider examples completed successfully")
    except Exception as e:
        logger.error(f"Error running examples: {e}", exc_info=True)
        print(f"Error running examples: {e}")


if __name__ == "__main__":
    print("PepperPy LLM Providers Usage Examples")
    print("====================================")
    print("This example demonstrates the intended usage patterns after refactoring.")
    print("Some functionality may not be fully implemented yet.")
    print("This is a demonstration of the API design, not necessarily working code.")

    asyncio.run(main())
