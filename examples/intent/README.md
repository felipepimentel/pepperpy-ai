# Intent Recognition Examples

This directory contains examples demonstrating how to use the intent recognition and processing capabilities in the PepperPy framework.

## Available Examples

### Intent Recognition Example

The `intent_recognition_example.py` file demonstrates the three main aspects of intent handling:

1. **Intent Recognition**: Converting raw user input (text, voice, etc.) into structured intent objects
2. **Intent Processing**: Taking action based on recognized intents
3. **Intent Classification**: Identifying multiple possible intents from ambiguous input

The example shows:

- How to use the intent recognition API to understand user commands
- How to manually create intents using the `IntentBuilder`
- How to process intents to perform actions
- How to classify text into multiple possible intents

To run this example:

```bash
python examples/intent/intent_recognition_example.py
```

## Key Concepts

### Intent Structure

An intent in PepperPy consists of:

- **Name**: The identifier for the intent (e.g., "play_music")
- **Type**: The category of intent (e.g., COMMAND, QUERY, INFORMATION)
- **Confidence**: A score indicating how confident the system is in the recognition
- **Entities**: Named parameters extracted from the input (e.g., "song", "artist")
- **Raw Text**: The original text that was processed

### Intent Recognition Flow

The typical flow for intent handling is:

1. **Recognition**: Convert raw input to an intent object
   ```python
   intent = await recognize_intent(text, recognizer_type="text")
   ```

2. **Processing**: Take action based on the intent
   ```python
   result = await process_intent(intent, processor_type="command")
   ```

3. **Classification** (optional): Identify multiple possible intents
   ```python
   intents = await classify_intent(text, classifier_type="rule")
   ```

### Intent Builder

The `IntentBuilder` provides a fluent interface for creating intent objects:

```python
intent = (
    IntentBuilder("play_music")
    .with_type(IntentType.COMMAND)
    .with_confidence(0.95)
    .with_entity("song", "Bohemian Rhapsody")
    .with_entity("artist", "Queen")
    .with_text("play Bohemian Rhapsody by Queen")
    .build()
)
``` 