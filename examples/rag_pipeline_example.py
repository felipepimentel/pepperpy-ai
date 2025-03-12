#!/usr/bin/env python
"""Example demonstrating the RAG pipeline components.

This example demonstrates the usage of the RAG pipeline components, including
document transformation, metadata extraction, and chunking.
"""

import logging
import sys
from pathlib import Path
from typing import List

# Add the parent directory to the path so we can import pepperpy
sys.path.append(str(Path(__file__).parent.parent))

from pepperpy.core.telemetry import enable_telemetry, set_telemetry_level
from pepperpy.rag.chunking import ChunkingStrategy
from pepperpy.rag.metadata import MetadataType
from pepperpy.rag.pipeline import (
    RAGPipelineBuilder,
    create_default_pipeline,
    create_simple_pipeline,
)
from pepperpy.rag.transform import TransformationType
from pepperpy.types.common import Document, Metadata


def setup_logging():
    """Set up logging for the example."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler()],
    )


def create_sample_documents() -> List[Document]:
    """Create sample documents for demonstration.

    Returns:
        A list of sample documents.
    """
    # Sample document 1: Technical article
    technical_article = """
    # Introduction to Machine Learning

    Machine learning is a subset of artificial intelligence (AI) that provides systems the ability to automatically learn and improve from experience without being explicitly programmed. Machine learning focuses on the development of computer programs that can access data and use it to learn for themselves.

    The process of learning begins with observations or data, such as examples, direct experience, or instruction, in order to look for patterns in data and make better decisions in the future based on the examples that we provide. The primary aim is to allow the computers to learn automatically without human intervention or assistance and adjust actions accordingly.

    ## Types of Machine Learning

    1. **Supervised Learning**: The algorithm is trained on labeled data. The model learns to predict the output from the input data.
    2. **Unsupervised Learning**: The algorithm is trained on unlabeled data. The model learns patterns and relationships from the input data without any guidance.
    3. **Reinforcement Learning**: The algorithm learns by interacting with an environment. It receives feedback in the form of rewards or penalties.

    ## Applications of Machine Learning

    Machine learning has numerous applications across various industries:

    - **Healthcare**: Disease identification, patient monitoring
    - **Finance**: Fraud detection, risk assessment
    - **Retail**: Recommendation systems, inventory management
    - **Transportation**: Autonomous vehicles, traffic prediction

    For more information, visit our website at https://example.com/machine-learning or contact us at info@example.com.
    """

    # Sample document 2: News article
    news_article = """
    # Breaking News: New Technological Advancements Unveiled

    January 15, 2025 - San Francisco, CA

    In a groundbreaking announcement today, TechCorp Inc. revealed their latest innovations at the annual TechExpo conference. CEO Jane Smith presented three new products that promise to revolutionize the technology industry.

    "We're excited to share these advancements with the world," said Smith during her keynote address. "These products represent years of research and development by our talented team."

    The first product, an artificial intelligence assistant named "Nexus," can understand and respond to complex queries with human-like comprehension. Unlike existing AI assistants, Nexus can maintain context across multiple conversations and learn from user interactions.

    The second product, "QuantumLink," is a quantum computing platform accessible through cloud services. This makes quantum computing capabilities available to businesses without requiring specialized hardware.

    The third announcement was "EcoCharge," a sustainable battery technology that lasts five times longer than current lithium-ion batteries while using environmentally friendly materials.

    Market analysts predict these innovations could significantly impact TechCorp's stock (TECH), which closed at $342.15 yesterday.

    For more information, visit TechCorp's website at https://techcorp-example.com or contact their media relations department at media@techcorp-example.com.
    """

    # Sample document 3: Literary text
    literary_text = """
    # The Forgotten Garden

    The old house stood silent at the end of the winding path, its windows like vacant eyes staring across the overgrown garden. Sarah paused at the rusted gate, her hand hesitating on the latch. After twenty years, she had finally returned.

    The garden, once her grandmother's pride, had surrendered to wilderness. Roses climbed in tangled rebellion over crumbling stone walls. Forgotten statues peeked from beneath ivy cloaks, their features softened by time and weather.

    "I never thought I'd come back," she whispered to the listening silence.

    The key felt cold in her palm, an inheritance she had almost declined. Her grandmother's letter had arrived three weeks after the funeral, its yellowed pages filled with secrets Sarah had never suspected.

    As she pushed open the gate, its hinges protesting with a mournful creak, memories flooded back. Summer afternoons helping Grandmother plant seedlings. Autumn evenings gathering herbs before the first frost. The mysterious locked door in the garden wall that Grandmother had forbidden her to approach.

    "The truth waits for you in the forgotten garden," the letter had said. "What was hidden must now be found."

    Sarah took a deep breath and stepped forward, the tall grass brushing against her legs as she made her way toward the house and the secrets it had kept for so long.
    """

    # Create Document objects
    documents = [
        Document(
            id="doc1",
            content=technical_article,
            metadata=Metadata.from_dict({
                "title": "Introduction to Machine Learning",
                "type": "technical",
            }),
        ),
        Document(
            id="doc2",
            content=news_article,
            metadata=Metadata.from_dict({
                "title": "New Technological Advancements",
                "type": "news",
            }),
        ),
        Document(
            id="doc3",
            content=literary_text,
            metadata=Metadata.from_dict({
                "title": "The Forgotten Garden",
                "type": "fiction",
            }),
        ),
    ]

    return documents


def demonstrate_default_pipeline():
    """Demonstrate the default RAG pipeline."""
    print("\n=== Demonstrating Default Pipeline ===\n")

    # Create sample documents
    documents = create_sample_documents()

    # Create default pipeline
    pipeline = create_default_pipeline()

    # Process the first document
    print(f"Processing document: {documents[0].metadata.to_dict().get('title')}")
    processed_docs = pipeline.process(documents[0])

    # Print results
    print(f"Original document length: {len(documents[0].content)} characters")
    print(f"Processed into {len(processed_docs)} chunks")

    # Print the first chunk
    if processed_docs:
        first_chunk = processed_docs[0]
        print("\nFirst chunk:")
        print(f"  ID: {first_chunk.id}")
        print(f"  Length: {len(first_chunk.content)} characters")
        print(f"  Metadata: {first_chunk.metadata.to_dict()}")
        print(f"  Content preview: {first_chunk.content[:100]}...")


def demonstrate_custom_pipeline():
    """Demonstrate a custom RAG pipeline."""
    print("\n=== Demonstrating Custom Pipeline ===\n")

    # Create sample documents
    documents = create_sample_documents()

    # Create a custom pipeline with specific configurations
    pipeline = (
        RAGPipelineBuilder()
        .with_transformation(
            include_types=[
                TransformationType.NORMALIZE,
                TransformationType.LOWERCASE,
                TransformationType.REMOVE_URLS,
            ]
        )
        .with_metadata_extraction(
            include_types=[
                MetadataType.DATE,
                MetadataType.ENTITY,
                MetadataType.KEYWORD,
            ]
        )
        .with_chunking(
            strategy=ChunkingStrategy.PARAGRAPH,
            chunk_size=500,
            chunk_overlap=50,
        )
        .build()
    )

    # Process the news article
    print(f"Processing document: {documents[1].metadata.to_dict().get('title')}")
    processed_docs = pipeline.process(documents[1])

    # Print results
    print(f"Original document length: {len(documents[1].content)} characters")
    print(f"Processed into {len(processed_docs)} chunks")

    # Print extracted entities if available
    if processed_docs:
        for i, chunk in enumerate(processed_docs[:2]):  # Show first two chunks
            print(f"\nChunk {i + 1}:")
            print(f"  ID: {chunk.id}")
            print(f"  Length: {len(chunk.content)} characters")

            # Print entities if available
            metadata_dict = chunk.metadata.to_dict()
            if "entities" in metadata_dict:
                entities = metadata_dict["entities"]
                print("  Extracted entities:")
                if "people" in entities and entities["people"]:
                    print(f"    People: {', '.join(entities['people'][:3])}")
                if "organizations" in entities and entities["organizations"]:
                    print(
                        f"    Organizations: {', '.join(entities['organizations'][:3])}"
                    )

            # Print keywords if available
            if "keywords" in metadata_dict:
                print(f"  Keywords: {', '.join(metadata_dict['keywords'][:5])}")

            print(f"  Content preview: {chunk.content[:100]}...")


def demonstrate_pipeline_stages():
    """Demonstrate the individual stages of the RAG pipeline."""
    print("\n=== Demonstrating Pipeline Stages ===\n")

    # Create sample documents
    documents = create_sample_documents()
    literary_doc = documents[2]  # The literary text

    print(f"Processing document: {literary_doc.metadata.to_dict().get('title')}")

    # 1. Transformation only
    transform_pipeline = (
        RAGPipelineBuilder()
        .with_transformation(
            include_types=[
                TransformationType.REMOVE_PUNCTUATION,
                TransformationType.LOWERCASE,
            ]
        )
        .build()
    )
    transformed_doc = transform_pipeline.process(literary_doc)[0]
    print("\n1. After transformation:")
    print(f"  Content preview: {transformed_doc.content[:100]}...")

    # 2. Metadata extraction only
    metadata_pipeline = RAGPipelineBuilder().with_metadata_extraction().build()
    metadata_doc = metadata_pipeline.process(literary_doc)[0]
    print("\n2. After metadata extraction:")
    metadata_dict = metadata_doc.metadata.to_dict()
    print(f"  Metadata keys: {', '.join(metadata_dict.keys())}")
    if "summary" in metadata_dict:
        print(f"  Summary: {metadata_dict['summary']}")

    # 3. Chunking only
    chunking_pipeline = (
        RAGPipelineBuilder().with_chunking(strategy=ChunkingStrategy.SENTENCE).build()
    )
    chunked_docs = chunking_pipeline.process(literary_doc)
    print("\n3. After chunking:")
    print(f"  Number of chunks: {len(chunked_docs)}")
    if chunked_docs:
        print(f"  First chunk: {chunked_docs[0].content[:100]}...")
        if len(chunked_docs) > 1:
            print(f"  Second chunk: {chunked_docs[1].content[:100]}...")


def demonstrate_batch_processing():
    """Demonstrate batch processing of documents."""
    print("\n=== Demonstrating Batch Processing ===\n")

    # Create sample documents
    documents = create_sample_documents()

    # Create a simple pipeline
    pipeline = create_simple_pipeline()

    # Process all documents
    print(f"Batch processing {len(documents)} documents")
    processed_docs = pipeline.batch_process(documents)

    # Print results
    print(f"Processed into {len(processed_docs)} total chunks")

    # Group chunks by original document
    chunks_by_doc = {}
    for chunk in processed_docs:
        parent_id = chunk.metadata.to_dict().get("parent_id", "unknown")
        if parent_id not in chunks_by_doc:
            chunks_by_doc[parent_id] = []
        chunks_by_doc[parent_id].append(chunk)

    # Print chunk counts by document
    for doc_id, chunks in chunks_by_doc.items():
        print(f"Document {doc_id}: {len(chunks)} chunks")


def main():
    """Run the RAG pipeline examples."""
    # Set up logging
    setup_logging()

    # Enable telemetry for demonstration
    enable_telemetry()
    set_telemetry_level("INFO")

    print("=== RAG Pipeline Example ===")
    print("This example demonstrates the usage of the RAG pipeline components.")

    # Run demonstrations
    demonstrate_default_pipeline()
    demonstrate_custom_pipeline()
    demonstrate_pipeline_stages()
    demonstrate_batch_processing()

    print("\n=== Example Complete ===")


if __name__ == "__main__":
    main()
