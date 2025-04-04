#!/usr/bin/env python3
"""
Content Processing Workflow Example

This example demonstrates PepperPy's declarative API for content processing workflows:
1. Text extraction from documents
2. Text normalization
3. Content generation
4. Content summarization
"""

import asyncio
from pathlib import Path

from pepperpy import PepperPy

# Define output directory
OUTPUT_DIR = Path(__file__).parent / "output" / "content"

# Sample document for processing
SAMPLE_DOCUMENT = """
# Machine Learning: A Brief Overview

## Introduction
Machine learning is a subset of artificial intelligence that focuses on developing algorithms 
that enable computers to learn patterns from data without being explicitly programmed. 
These algorithms improve their performance as they are exposed to more data over time.

## Types of Machine Learning

### Supervised Learning
In supervised learning, algorithms are trained using labeled data, where the desired output is known. 
The algorithm learns to map inputs to outputs based on example input-output pairs.
Examples include classification and regression.

### Unsupervised Learning
Unsupervised learning deals with unlabeled data. The algorithm tries to learn the inherent structure 
of the data without predefined outputs. Clustering and dimensionality reduction are common applications.

### Reinforcement Learning
Reinforcement learning involves an agent learning to make decisions by taking actions in an environment 
to maximize some notion of cumulative reward. It's widely used in robotics, gaming, and navigation.

## Common Algorithms
- Linear Regression
- Logistic Regression
- Decision Trees
- Random Forests
- Support Vector Machines
- Neural Networks
- K-means Clustering

## Challenges in Machine Learning
- Overfitting and underfitting
- Feature selection
- Bias and variance trade-off
- Data quality and quantity
- Interpretability vs. performance

## Applications
Machine learning has transformed numerous industries including healthcare, finance, transportation, 
and entertainment. From medical diagnosis to autonomous vehicles, the applications continue to expand.
"""


async def main():
    """Demonstrate content processing using PepperPy's declarative API."""
    # Text with inconsistencies to normalize
    inconsistent_text = """
    machine Learning can be divided into: supervised learning, UNsupervised learning, 
    & reinforcement learning. Common algorithms include: linear regression, LOGISTIC 
    regression, decision trees, etc. Neural nets are also popular ML algorithms.
    """

    # Setup pipeline with declarative configuration
    pepper = PepperPy().configure(
        output_dir=OUTPUT_DIR,
        log_level="INFO",
        log_to_console=True,
        auto_save_results=True,
    )

    # Define all content processing steps
    processors = [
        # Text extraction processor
        pepper.processor("text_extraction")
        .prompt(
            "Extract and list all machine learning types and algorithms mentioned in this document."
        )
        .input(SAMPLE_DOCUMENT)
        .output("extraction_result.txt"),
        # Text normalization processor
        pepper.processor("text_normalization")
        .prompt(
            "Normalize this text by using consistent terminology, proper capitalization, and professional formatting."
        )
        .input(inconsistent_text)
        .output("normalization_result.txt"),
        # Content generation processor
        pepper.processor("content_generation")
        .prompt(
            "Generate a short introduction paragraph about deep learning, explaining how it relates to machine learning."
        )
        .parameters({"max_length": 200, "style": "educational"})
        .output("generation_result.txt"),
        # Content summarization processor
        pepper.processor("content_summarization")
        .prompt(
            "Provide a concise 3-sentence summary of this document about machine learning."
        )
        .input(SAMPLE_DOCUMENT)
        .parameters({"sentences": 3, "style": "concise"})
        .output("summarization_result.txt"),
    ]

    # Execute all processors at once - potentially in parallel
    await pepper.run_processors(processors)

    # Generate report showing results
    print("\nAll content processing completed successfully!")
    print(f"Results saved to {OUTPUT_DIR}")
    for processor in processors:
        print(f"- {processor.name}: Processing completed")

    # Optional: run a sequential workflow instead
    # workflow = pepper.workflow("content_processing")
    # workflow.add_steps(processors)
    # workflow.set_dependencies({"text_normalization": ["text_extraction"]})
    # await workflow.execute()


if __name__ == "__main__":
    asyncio.run(main())
