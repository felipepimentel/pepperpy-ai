#!/usr/bin/env python3
"""
Content Processing Workflow Example

This example demonstrates PepperPy's content processing capabilities for:
1. Text extraction from documents
2. Text normalization
3. Content generation
4. Content summarization
"""

import asyncio
import os
from pathlib import Path

from pepperpy import PepperPy

# Output directory for results
OUTPUT_DIR = Path(__file__).parent / "output" / "content"
os.makedirs(OUTPUT_DIR, exist_ok=True)

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


async def text_extraction_example() -> None:
    """Demonstrate text extraction functionality."""
    # PepperPy handles both text extraction, logging, and result saving
    async with PepperPy().with_llm() as pepper:
        # Execute with automatic logging of operations
        await pepper.execute(
            "Extract and list all machine learning types and algorithms mentioned in this document.",
            context={"document": SAMPLE_DOCUMENT},
            output_path=OUTPUT_DIR / "extraction_result.txt",
        )


async def text_normalization_example() -> None:
    """Demonstrate text normalization functionality."""
    # Text with inconsistencies to normalize
    inconsistent_text = """
    machine Learning can be divided into: supervised learning, UNsupervised learning, 
    & reinforcement learning. Common algorithms include: linear regression, LOGISTIC 
    regression, decision trees, etc. Neural nets are also popular ML algorithms.
    """

    # PepperPy handles both normalization, logging, and result saving
    async with PepperPy().with_llm() as pepper:
        # Execute with automatic logging
        await pepper.execute(
            "Normalize this text by using consistent terminology, proper capitalization, and professional formatting.",
            context={"text": inconsistent_text},
            output_path=OUTPUT_DIR / "normalization_result.txt",
        )


async def content_generation_example() -> None:
    """Demonstrate content generation functionality."""
    # PepperPy handles both content generation, logging, and result saving
    async with PepperPy().with_llm() as pepper:
        # Execute with automatic logging
        await pepper.execute(
            "Generate a short introduction paragraph about deep learning, explaining how it relates to machine learning.",
            output_path=OUTPUT_DIR / "generation_result.txt",
        )


async def content_summarization_example() -> None:
    """Demonstrate content summarization functionality."""
    # PepperPy handles both summarization, logging, and result saving
    async with PepperPy().with_llm() as pepper:
        # Execute with automatic logging
        await pepper.execute(
            "Provide a concise 3-sentence summary of this document about machine learning.",
            context={"document": SAMPLE_DOCUMENT},
            output_path=OUTPUT_DIR / "summarization_result.txt",
        )


async def main() -> None:
    """Run all content processing examples."""
    # PepperPy should handle both console output and logging
    pepper = PepperPy()
    await pepper.log_header("PEPPERPY CONTENT PROCESSING WORKFLOW EXAMPLE")

    # Initialize for this example with automatic logging of operations
    await pepper.initialize(
        output_dir=OUTPUT_DIR, log_level="INFO", log_to_console=True, log_to_file=True
    )

    await text_extraction_example()
    await text_normalization_example()
    await content_generation_example()
    await content_summarization_example()

    # Finalize with automatic summary of results
    await pepper.finalize(
        summary_message="All content processing examples completed!",
        output_dir=OUTPUT_DIR,
    )


if __name__ == "__main__":
    asyncio.run(main())
