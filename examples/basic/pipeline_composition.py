"""Example demonstrating basic pipeline composition in PepperPy.

This example shows how to:
1. Create pipeline stages
2. Compose stages into a pipeline
3. Execute the pipeline with different inputs
4. Handle pipeline context and metadata
"""

import logging
from typing import Dict

from pepperpy.core.pipeline import FunctionStage, Pipeline, PipelineContext

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def tokenize_text(text: str, context: PipelineContext) -> list[str]:
    """Split text into words and store the word count in context."""
    words = text.split()
    context.metadata["word_count"] = len(words)
    return words


def remove_stopwords(words: list[str], context: PipelineContext) -> list[str]:
    """Remove common English stopwords."""
    stopwords = {"the", "a", "an", "and", "or", "but", "in", "on", "at", "to"}
    filtered = [word for word in words if word.lower() not in stopwords]
    context.metadata["removed_stopwords"] = len(words) - len(filtered)
    return filtered


def count_frequencies(words: list[str], context: PipelineContext) -> Dict[str, int]:
    """Count word frequencies."""
    frequencies = {}
    for word in words:
        frequencies[word] = frequencies.get(word, 0) + 1
    context.metadata["unique_words"] = len(frequencies)
    return frequencies


def main():
    # Create pipeline stages
    tokenizer = FunctionStage(
        name="tokenizer", func=tokenize_text, description="Splits text into words"
    )

    stopword_remover = FunctionStage(
        name="stopword_remover",
        func=remove_stopwords,
        description="Removes common stopwords",
    )

    frequency_counter = FunctionStage(
        name="frequency_counter",
        func=count_frequencies,
        description="Counts word frequencies",
    )

    # Create and configure the pipeline
    pipeline = Pipeline(name="text_analysis")
    pipeline.add_stage(tokenizer)
    pipeline.add_stage(stopword_remover)
    pipeline.add_stage(frequency_counter)

    # Example text to process
    text = "The quick brown fox jumps over the lazy dog"

    # Create pipeline context
    context = PipelineContext()
    context.metadata["input_length"] = len(text)

    # Execute the pipeline
    try:
        result = pipeline.execute(text, context)

        # Print results
        logger.info("Pipeline execution completed successfully")
        logger.info("Input text: %s", text)
        logger.info("Word frequencies: %s", result)
        logger.info("Pipeline metadata:")
        for key, value in context.metadata.items():
            logger.info("  %s: %s", key, value)

    except Exception as e:
        logger.error("Pipeline execution failed: %s", str(e))


if __name__ == "__main__":
    main()
