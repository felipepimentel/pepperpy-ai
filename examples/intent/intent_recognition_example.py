#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Example demonstrating the use of intent recognition in the PepperPy framework.

This example shows how to create and use intent recognizers, processors, and classifiers
to understand and respond to user intents.
"""

import asyncio

from pepperpy.core.intent.public import (
    IntentBuilder,
    classify_intent,
    process_intent,
    recognize_intent,
)
from pepperpy.core.intent.types import IntentType


async def demonstrate_intent_recognition():
    """Demonstrate basic intent recognition."""
    print("\n=== Intent Recognition Example ===\n")

    # Example 1: Recognize a command intent
    text = "please play the song 'Bohemian Rhapsody' by Queen"
    print(f"Input text: '{text}'")

    intent = await recognize_intent(text, recognizer_type="text")

    print(f"Recognized intent: {intent.name}")
    print(f"Intent type: {intent.intent_type.value}")
    print(f"Confidence: {intent.confidence}")
    print("Entities:")
    for entity_name, entity_value in intent.entities.items():
        print(f"  - {entity_name}: {entity_value}")


async def demonstrate_intent_processing():
    """Demonstrate intent processing."""
    print("\n=== Intent Processing Example ===\n")

    # Create a command intent manually
    intent = (
        IntentBuilder("play_music")
        .with_type(IntentType.COMMAND)
        .with_confidence(0.95)
        .with_entity("song", "Bohemian Rhapsody")
        .with_entity("artist", "Queen")
        .with_text("play Bohemian Rhapsody by Queen")
        .build()
    )

    print(f"Processing intent: {intent}")

    # Process the intent
    result = await process_intent(intent, processor_type="command")

    print("Processing result:")
    for key, value in result.items():
        print(f"  - {key}: {value}")


async def demonstrate_intent_classification():
    """Demonstrate intent classification."""
    print("\n=== Intent Classification Example ===\n")

    # Example text for classification
    text = "what's the weather like in New York today?"
    print(f"Input text: '{text}'")

    # Classify the intent
    intents = await classify_intent(text, classifier_type="rule")

    print(f"Found {len(intents)} possible intents:")
    for i, intent in enumerate(intents, 1):
        print(f"\nIntent {i}:")
        print(f"  - Name: {intent.name}")
        print(f"  - Type: {intent.intent_type.value}")
        print(f"  - Confidence: {intent.confidence}")
        print("  - Entities:")
        for entity_name, entity_value in intent.entities.items():
            print(f"    * {entity_name}: {entity_value}")


async def main():
    """Run all the intent examples."""
    await demonstrate_intent_recognition()
    await demonstrate_intent_processing()
    await demonstrate_intent_classification()


if __name__ == "__main__":
    asyncio.run(main())
