#!/usr/bin/env python
"""Example demonstrating RAG (Retrieval Augmented Generation) capabilities in PepperPy.

This example shows how to:
- Create and configure RAG providers
- Process and index documents with metadata
- Perform document retrieval with different strategies
- Handle document transformations and chunking
- Use advanced RAG features like reranking and hybrid search
"""

import asyncio
from typing import Dict, List, Optional

from pepperpy.llm import LLMProvider
from pepperpy.llm.providers.openai import OpenAIProvider
from pepperpy.llm.types import Message
from pepperpy.rag import Document, Query, RAGProvider, RetrievalResult
from pepperpy.rag.providers import LocalRAGProvider
from pepperpy.utils.logger import get_logger

# Configure logging
logger = get_logger(__name__)


def create_sample_documents() -> List[Document]:
    """Create sample documents for demonstration.

    Returns:
        List of sample documents with metadata
    """
    # Technical article
    technical_doc = Document(
        content="""
        Introduction to Machine Learning

        Machine learning is a subset of artificial intelligence (AI) that provides
        systems the ability to automatically learn and improve from experience
        without being explicitly programmed.

        Key concepts include:
        1. Supervised Learning
        2. Unsupervised Learning
        3. Reinforcement Learning

        Applications span healthcare, finance, retail, and transportation.
        """,
        metadata={
            "title": "Introduction to Machine Learning",
            "type": "technical",
            "tags": ["machine learning", "AI", "tutorial"],
        },
    )

    # News article
    news_doc = Document(
        content="""
        Breaking News: AI Breakthrough in Healthcare

        Researchers have developed a new AI system that can detect early signs
        of diseases with unprecedented accuracy. The system uses deep learning
        to analyze medical images and patient data.

        Clinical trials show a 95% accuracy rate in early detection.
        """,
        metadata={
            "title": "AI Breakthrough in Healthcare",
            "type": "news",
            "tags": ["AI", "healthcare", "research"],
            "date": "2024-03-20",
        },
    )

    # Research paper
    research_doc = Document(
        content="""
        Abstract: Advances in Natural Language Processing

        This paper presents recent advances in NLP, focusing on transformer
        architectures and their applications. We demonstrate improved performance
        on various benchmarks and introduce new techniques for efficient training.

        Keywords: NLP, transformers, deep learning
        """,
        metadata={
            "title": "Advances in Natural Language Processing",
            "type": "research",
            "tags": ["NLP", "transformers", "research"],
            "authors": ["Smith, J.", "Johnson, A."],
        },
    )

    return [technical_doc, news_doc, research_doc]


async def setup_rag_provider() -> RAGProvider:
    """Initialize and configure the RAG provider.

    Returns:
        Configured RAG provider
    """
    logger.info("Setting up RAG provider...")

    # Create local RAG provider
    provider = LocalRAGProvider(
        config={
            "embedding_model": "sentence-transformers/all-mpnet-base-v2",
            "chunk_size": 512,
            "chunk_overlap": 50,
        }
    )

    # Initialize provider
    await provider.initialize()
    logger.info("RAG provider initialized")

    return provider


async def index_documents(
    provider: RAGProvider,
    documents: List[Document],
) -> None:
    """Index documents using the RAG provider.

    Args:
        provider: The RAG provider to use
        documents: List of documents to index
    """
    logger.info(f"Indexing {len(documents)} documents...")

    for doc in documents:
        await provider.add_document(
            content=doc.content,
            metadata=doc.metadata,
        )

    logger.info("Document indexing complete")


async def perform_queries(
    provider: RAGProvider,
    queries: List[str],
    llm_provider: Optional[LLMProvider] = None,
) -> Dict[str, RetrievalResult]:
    """Perform queries and optionally enhance results with LLM.

    Args:
        provider: The RAG provider to use
        queries: List of queries to process
        llm_provider: Optional LLM provider for result enhancement

    Returns:
        Dictionary mapping queries to their results
    """
    logger.info(f"Processing {len(queries)} queries...")
    results = {}

    for query_text in queries:
        # Create query with filters and parameters
        query = Query(
            text=query_text,
            filters={"type": ["technical", "research"]},  # Only technical/research docs
            k=2,  # Get top 2 results
            score_threshold=0.5,  # Minimum relevance score
        )

        # Get results
        result = await provider.query(query)

        # Enhance with LLM if available
        if llm_provider and result.documents:
            context = "\n\n".join(doc.content for doc in result.documents)
            messages: List[Message] = [
                {
                    "role": "user",
                    "content": f"""Based on the following context, answer the question: {query_text}

                Context:
                {context}

                Answer:""",
                }
            ]

            enhanced_result = await llm_provider.generate(
                messages=messages,
                max_tokens=200,
            )

            # Store the generated response in result metadata
            if enhanced_result:
                result.metadata = result.metadata or {}
                result.metadata["enhanced_answer"] = enhanced_result.content

        results[query_text] = result
        logger.info(f"Processed query: {query_text}")

    return results


async def main() -> None:
    """Run the RAG example."""
    try:
        # Create and setup providers
        rag_provider = await setup_rag_provider()
        llm_provider = OpenAIProvider(api_key="your-api-key")  # Replace with your key

        # Create and index documents
    documents = create_sample_documents()
        await index_documents(rag_provider, documents)

        # Perform sample queries
        queries = [
            "What are the main types of machine learning?",
            "What are recent advances in NLP?",
            "How is AI being used in healthcare?",
        ]

        results = await perform_queries(
            provider=rag_provider,
            queries=queries,
            llm_provider=llm_provider,
        )

        # Display results
        print("\nQuery Results:")
        print("=============")

        for query, result in results.items():
            print(f"\nQuery: {query}")
            print("Relevant documents:")

            for doc, score in zip(result.documents, result.scores):
                print(f"\n- Document (score: {score:.2f}):")
                if doc.metadata:
                    print(f"  Title: {doc.metadata.get('title', 'Untitled')}")
                    print(f"  Type: {doc.metadata.get('type', 'Unknown')}")
                print(f"  Preview: {doc.content[:100]}...")

            if result.metadata and "enhanced_answer" in result.metadata:
                print("\nEnhanced answer:")
                print(result.metadata["enhanced_answer"])

    except Exception as e:
        logger.error(f"Error in RAG example: {e}")
        raise
    finally:
        # Cleanup
        await rag_provider.cleanup()
        if llm_provider:
            await llm_provider.cleanup()


if __name__ == "__main__":
    print("PepperPy RAG Example")
    print("===================")
    print("This example demonstrates the RAG capabilities of PepperPy,")
    print("including document indexing, retrieval, and LLM enhancement.\n")

    asyncio.run(main())
