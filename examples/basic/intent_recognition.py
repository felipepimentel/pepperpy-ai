"""Example demonstrating intent recognition in PepperPy.

This example shows how to:
1. Recognize intents from natural language text
2. Extract entities from recognized intents
3. Handle different types of intents
4. Work with confidence scores

Example:
    $ python examples/basic/intent_recognition.py
    Enter text (or 'quit' to exit): traduzir hello world
    Intent: translate (confidence: 0.85)
    Entities: {'text': 'hello world'}
"""

import logging
from typing import Optional

from pepperpy.core.intent import Intent, IntentType, recognize_intent

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def format_intent(intent: Intent) -> str:
    """Format an intent for display.

    Args:
        intent: The intent to format

    Returns:
        A formatted string representation of the intent
    """
    # Format basic info
    result = f"Intent: {intent.name} (confidence: {intent.confidence:.2f})"

    # Add type if not query
    if intent.type != IntentType.QUERY:
        result += f"\nType: {intent.type}"

    # Add entities if present
    if intent.entities:
        result += f"\nEntities: {intent.entities}"

    return result


async def process_text(text: str) -> Optional[str]:
    """Process text and return formatted intent info.

    Args:
        text: The text to process

    Returns:
        Formatted intent information or None if processing failed
    """
    try:
        # Recognize intent
        intent = await recognize_intent(text)

        # Format and return result
        return format_intent(intent)

    except ValueError as e:
        logger.error("Invalid input: %s", str(e))
        return None
    except Exception as e:
        logger.error("Error processing text: %s", str(e))
        return None


async def main():
    """Run the intent recognition example."""
    print("PepperPy Intent Recognition Example")
    print("Enter text (or 'quit' to exit)")

    while True:
        # Get input
        try:
            text = input("\nEnter text: ").strip()
        except (KeyboardInterrupt, EOFError):
            break

        # Check for exit
        if text.lower() == "quit":
            break

        # Skip empty input
        if not text:
            continue

        # Process text
        result = await process_text(text)
        if result:
            print(result)

    print("\nGoodbye!")


if __name__ == "__main__":
    import asyncio

    asyncio.run(main()) 