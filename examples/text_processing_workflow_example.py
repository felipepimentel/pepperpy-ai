"""Example of using text processors in a workflow."""

import asyncio

from pepperpy.workflow.base import PipelineContext
from pepperpy.workflow.recipes.text_processing import (
    BatchTextProcessingStage,
    TextProcessingStage,
)


async def process_single_text() -> None:
    """Example of processing a single text."""
    # Create a pipeline with a text processing stage
    stage = TextProcessingStage(processor="spacy", model="en_core_web_sm")

    # Create context with processing options
    context = PipelineContext()
    context.set(
        "processing_options",
        {
            "disable": ["parser"]  # Disable specific components for speed
        },
    )

    try:
        # Initialize stage
        await stage.initialize()

        # Process text
        text = "Apple Inc. is planning to open a new office in London next year."
        result = await stage.process(text, context)

        # Print results
        print("\nSingle Text Processing Results:")
        print(f"Text: {result.text}")
        print(f"Tokens: {result.tokens}")
        print(f"Entities: {result.entities}")
        print(f"Metadata: {result.metadata}")
        print(f"Context metadata: {context.metadata}")
    finally:
        # Clean up resources
        await stage.cleanup()


async def process_batch_texts() -> None:
    """Example of processing multiple texts in batch."""
    # Create a pipeline with a batch text processing stage
    stage = BatchTextProcessingStage(
        processor="transformers",
        model="dbmdz/bert-large-cased-finetuned-conll03-english",
        device="cpu",
        batch_size=2,
    )

    # Create context
    context = PipelineContext()

    try:
        # Initialize stage
        await stage.initialize()

        # Process texts
        texts = [
            "Google announced a new AI model yesterday.",
            "Microsoft is investing heavily in OpenAI.",
            "Tesla's new factory will be built in Texas.",
        ]

        results = await stage.process(texts, context)

        # Print results
        print("\nBatch Processing Results:")
        for i, result in enumerate(results, 1):
            print(f"\nText {i}:")
            print(f"Original: {result.text}")
            print(f"Entities: {result.entities}")

        print(f"\nContext metadata: {context.metadata}")
    finally:
        # Clean up resources
        await stage.cleanup()


async def multi_processor_pipeline() -> None:
    """Example of using multiple processors in sequence."""
    # Create a pipeline that uses both NLTK and SpaCy
    nltk_stage = TextProcessingStage(
        processor="nltk",
        model=None,  # NLTK doesn't require a specific model
    )
    spacy_stage = TextProcessingStage(processor="spacy", model="en_core_web_sm")

    # Create context
    context = PipelineContext()

    try:
        # Initialize stages
        await nltk_stage.initialize()
        await spacy_stage.initialize()

        # Process text
        text = """
        The European Union has announced new climate goals. The targets aim to reduce
        emissions by 55% by 2030. Several member states, including France and Germany,
        have pledged additional support.
        """

        # Process with NLTK first
        nltk_result = await nltk_stage.process(text, context)

        # Then process with SpaCy
        final_result = await spacy_stage.process(nltk_result.text, context)

        # Print results
        print("\nMulti-Processor Pipeline Results:")
        print(f"Text: {final_result.text}")
        print(f"Tokens: {final_result.tokens}")
        print(f"Entities: {final_result.entities}")
        print(f"Metadata: {final_result.metadata}")
        print(f"Context metadata: {context.metadata}")
    finally:
        # Clean up resources
        await nltk_stage.cleanup()
        await spacy_stage.cleanup()


async def main() -> None:
    """Run all examples."""
    print("Starting text processing examples...")

    # Run examples
    await process_single_text()
    await process_batch_texts()
    await multi_processor_pipeline()

    print("\nAll examples completed!")


if __name__ == "__main__":
    asyncio.run(main())
