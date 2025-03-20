#!/usr/bin/env python
"""
Example demonstrating the hybrid search capabilities of the RAG module.

This example shows how to:
1. Create and configure keyword search
2. Create and configure semantic search
3. Create and configure hybrid search with different fusion methods
4. Compare results from different search approaches
5. Customize search parameters for specific use cases
"""

import logging
import random
import sys
from pathlib import Path
from typing import List

# Add the parent directory to the path so we can import the pepperpy package
sys.path.append(str(Path(__file__).parent.parent))

from pepperpy.rag.hybrid_search import (
    HybridSearchConfig,
    KeywordSearch,
    KeywordSearchConfig,
    SearchResults,
    SemanticSearch,
    SemanticSearchConfig,
    create_hybrid_search,
)
from pepperpy.types.common import Document, Metadata

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def create_sample_documents() -> List[Document]:
    """
    Create a sample document collection for search testing.

    Returns:
        A list of sample documents
    """
    documents = []

    # Document 1: Python programming
    documents.append(
        Document(
            id="doc1",
            content="""
        Python is a high-level, interpreted programming language known for its readability and simplicity.
        It supports multiple programming paradigms, including procedural, object-oriented, and functional programming.
        Python has a large standard library and a vibrant ecosystem of third-party packages.
        Popular Python frameworks include Django and Flask for web development, and NumPy and Pandas for data analysis.
        """,
            metadata=Metadata.from_dict({
                "title": "Introduction to Python",
                "category": "Programming",
                "tags": ["python", "programming", "language"],
            }),
        )
    )

    # Document 2: Machine learning
    documents.append(
        Document(
            id="doc2",
            content="""
        Machine learning is a subset of artificial intelligence that focuses on developing systems that can learn from data.
        Common machine learning algorithms include linear regression, decision trees, and neural networks.
        Python is widely used in machine learning, with libraries such as scikit-learn, TensorFlow, and PyTorch.
        Deep learning is a subset of machine learning that uses neural networks with many layers.
        """,
            metadata=Metadata.from_dict({
                "title": "Introduction to Machine Learning",
                "category": "Data Science",
                "tags": ["machine learning", "AI", "data science"],
            }),
        )
    )

    # Document 3: Database systems
    documents.append(
        Document(
            id="doc3",
            content="""
        Database systems are software applications that store, retrieve, and manage data.
        SQL (Structured Query Language) is used to interact with relational databases like MySQL, PostgreSQL, and SQLite.
        NoSQL databases like MongoDB and Cassandra are designed for specific data models and have flexible schemas.
        Database optimization techniques include indexing, query optimization, and denormalization.
        """,
            metadata=Metadata.from_dict({
                "title": "Database Systems Overview",
                "category": "Databases",
                "tags": ["database", "SQL", "NoSQL"],
            }),
        )
    )

    # Document 4: Web development
    documents.append(
        Document(
            id="doc4",
            content="""
        Web development involves creating websites and web applications.
        Frontend development focuses on the user interface using HTML, CSS, and JavaScript.
        Backend development involves server-side logic, databases, and APIs.
        Full-stack developers work on both frontend and backend components.
        Python frameworks like Django and Flask are popular for backend web development.
        """,
            metadata=Metadata.from_dict({
                "title": "Web Development Fundamentals",
                "category": "Web Development",
                "tags": ["web", "frontend", "backend", "python"],
            }),
        )
    )

    # Document 5: Cloud computing
    documents.append(
        Document(
            id="doc5",
            content="""
        Cloud computing provides on-demand computing resources over the internet.
        Major cloud providers include AWS, Microsoft Azure, and Google Cloud Platform.
        Cloud service models include Infrastructure as a Service (IaaS), Platform as a Service (PaaS), and Software as a Service (SaaS).
        Serverless computing allows developers to build applications without managing servers.
        """,
            metadata=Metadata.from_dict({
                "title": "Introduction to Cloud Computing",
                "category": "Cloud",
                "tags": ["cloud", "AWS", "Azure", "GCP"],
            }),
        )
    )

    # Document 6: Data analysis
    documents.append(
        Document(
            id="doc6",
            content="""
        Data analysis is the process of inspecting, cleaning, transforming, and modeling data to discover useful information.
        Python libraries like Pandas and NumPy are commonly used for data manipulation and analysis.
        Exploratory data analysis (EDA) involves summarizing data and creating visualizations.
        Statistical methods are used to identify patterns and relationships in data.
        """,
            metadata=Metadata.from_dict({
                "title": "Data Analysis Techniques",
                "category": "Data Science",
                "tags": ["data analysis", "statistics", "python"],
            }),
        )
    )

    # Document 7: Software engineering
    documents.append(
        Document(
            id="doc7",
            content="""
        Software engineering is the systematic application of engineering principles to software development.
        Software development life cycle (SDLC) includes planning, design, implementation, testing, and maintenance.
        Agile methodologies like Scrum and Kanban emphasize iterative development and collaboration.
        Version control systems like Git help manage changes to source code over time.
        """,
            metadata=Metadata.from_dict({
                "title": "Software Engineering Principles",
                "category": "Software Engineering",
                "tags": ["software engineering", "SDLC", "agile"],
            }),
        )
    )

    # Document 8: Artificial intelligence
    documents.append(
        Document(
            id="doc8",
            content="""
        Artificial intelligence (AI) is the simulation of human intelligence in machines.
        AI encompasses machine learning, natural language processing, computer vision, and robotics.
        Natural language processing (NLP) enables computers to understand and generate human language.
        Computer vision allows machines to interpret and make decisions based on visual data.
        """,
            metadata=Metadata.from_dict({
                "title": "Introduction to Artificial Intelligence",
                "category": "AI",
                "tags": ["AI", "NLP", "computer vision"],
            }),
        )
    )

    # Document 9: DevOps
    documents.append(
        Document(
            id="doc9",
            content="""
        DevOps is a set of practices that combines software development (Dev) and IT operations (Ops).
        Continuous Integration (CI) involves automatically integrating code changes into a shared repository.
        Continuous Deployment (CD) automates the delivery of applications to production environments.
        Infrastructure as Code (IaC) manages infrastructure using configuration files rather than manual setup.
        """,
            metadata=Metadata.from_dict({
                "title": "DevOps Practices",
                "category": "DevOps",
                "tags": ["DevOps", "CI/CD", "automation"],
            }),
        )
    )

    # Document 10: Cybersecurity
    documents.append(
        Document(
            id="doc10",
            content="""
        Cybersecurity involves protecting systems, networks, and programs from digital attacks.
        Common security threats include malware, phishing, and denial-of-service attacks.
        Encryption is used to secure data by converting it into a code that can only be accessed with a key.
        Authentication and authorization control access to systems and resources.
        """,
            metadata=Metadata.from_dict({
                "title": "Cybersecurity Fundamentals",
                "category": "Security",
                "tags": ["cybersecurity", "encryption", "security"],
            }),
        )
    )

    return documents


def print_search_results(results: SearchResults, max_results: int = 5) -> None:
    """
    Print search results in a readable format.

    Args:
        results: The search results to print
        max_results: Maximum number of results to print
    """
    logger.info(f"Search type: {results.search_type.name}")
    logger.info(f"Query: '{results.query}'")
    logger.info(f"Total results: {len(results)}")

    if results.metadata:
        logger.info("Metadata:")
        for key, value in results.metadata.items():
            logger.info(f"  {key}: {value}")

    logger.info("Results:")
    for i, result in enumerate(results.results[:max_results]):
        logger.info(f"  {i + 1}. Document: {result.document.id}")
        logger.info(f"     Title: {result.document.metadata.get('title', 'No title')}")
        logger.info(f"     Score: {result.score:.4f}")
        if result.normalized_score is not None:
            logger.info(f"     Normalized score: {result.normalized_score:.4f}")
        if result.combined_score is not None:
            logger.info(f"     Combined score: {result.combined_score:.4f}")
        logger.info(f"     Type: {result.search_type.name}")

        # Print a snippet of the content
        content = result.document.content.strip()
        snippet = content[:150] + "..." if len(content) > 150 else content
        logger.info(f"     Snippet: {snippet}")

        # Print highlights if available
        if result.highlights:
            logger.info("     Highlights:")
            for j, highlight in enumerate(result.highlights[:2]):
                logger.info(f"       {j + 1}. {highlight}")

        logger.info("")

    logger.info("-" * 80)


def demonstrate_keyword_search(documents: List[Document]) -> None:
    """
    Demonstrate keyword search with different configurations.

    Args:
        documents: The documents to search
    """
    logger.info("=== Demonstrating Keyword Search ===")

    # Create a keyword search with default configuration
    default_keyword_search = KeywordSearch()

    # Create a keyword search with custom configuration
    custom_config = KeywordSearchConfig(
        algorithm="BM25",
        min_score=0.01,
        max_results=5,
        highlight=True,
        highlight_tag="<em>",
    )
    custom_keyword_search = KeywordSearch(config=custom_config)

    # Sample queries
    queries = [
        "Python programming language",
        "machine learning and artificial intelligence",
        "database systems SQL NoSQL",
        "web development with Python",
    ]

    for query in queries:
        logger.info(f"\nPerforming keyword search for: '{query}'")

        # Search with default configuration
        default_results = default_keyword_search.search(query, documents)
        logger.info("Default keyword search results:")
        print_search_results(default_results)

        # Search with custom configuration
        custom_results = custom_keyword_search.search(query, documents)
        logger.info("Custom keyword search results:")
        print_search_results(custom_results)


def demonstrate_semantic_search(documents: List[Document]) -> None:
    """
    Demonstrate semantic search with different configurations.

    Args:
        documents: The documents to search
    """
    logger.info("\n=== Demonstrating Semantic Search ===")

    # Create a semantic search with default configuration
    default_semantic_search = SemanticSearch()

    # Create a semantic search with custom configuration
    custom_config = SemanticSearchConfig(
        model_name="simulated-model",
        min_score=0.5,
        max_results=5,
        normalize_scores=True,
    )
    custom_semantic_search = SemanticSearch(config=custom_config)

    # Sample queries
    queries = [
        "How does Python support different programming paradigms?",
        "What are the applications of machine learning?",
        "Compare SQL and NoSQL databases",
        "What is the role of Python in web development?",
    ]

    for query in queries:
        logger.info(f"\nPerforming semantic search for: '{query}'")

        # Search with default configuration
        default_results = default_semantic_search.search(query, documents)
        logger.info("Default semantic search results:")
        print_search_results(default_results)

        # Search with custom configuration
        custom_results = custom_semantic_search.search(query, documents)
        logger.info("Custom semantic search results:")
        print_search_results(custom_results)


def demonstrate_hybrid_search(documents: List[Document]) -> None:
    """
    Demonstrate hybrid search with different configurations.

    Args:
        documents: The documents to search
    """
    logger.info("\n=== Demonstrating Hybrid Search ===")

    # Create hybrid search with linear combination fusion
    linear_config = HybridSearchConfig(
        keyword_weight=0.4,
        semantic_weight=0.6,
        fusion_method="linear_combination",
        max_results=5,
        deduplicate=True,
        rerank=False,
    )
    linear_hybrid_search = create_hybrid_search(hybrid_config=linear_config)

    # Create hybrid search with reciprocal rank fusion
    rrf_config = HybridSearchConfig(
        keyword_weight=0.5,
        semantic_weight=0.5,
        fusion_method="reciprocal_rank_fusion",
        max_results=5,
        deduplicate=True,
        rerank=True,
    )
    rrf_hybrid_search = create_hybrid_search(hybrid_config=rrf_config)

    # Sample queries
    queries = [
        "Python for data analysis and machine learning",
        "Cloud computing security best practices",
        "DevOps practices for web application deployment",
        "Artificial intelligence and natural language processing",
    ]

    for query in queries:
        logger.info(f"\nPerforming hybrid search for: '{query}'")

        # Search with linear combination fusion
        linear_results = linear_hybrid_search.search(query, documents)
        logger.info("Linear combination fusion results:")
        print_search_results(linear_results)

        # Search with reciprocal rank fusion
        rrf_results = rrf_hybrid_search.search(query, documents)
        logger.info("Reciprocal rank fusion results:")
        print_search_results(rrf_results)


def compare_search_approaches(documents: List[Document]) -> None:
    """
    Compare different search approaches on the same queries.

    Args:
        documents: The documents to search
    """
    logger.info("\n=== Comparing Search Approaches ===")

    # Create search instances
    keyword_search = KeywordSearch()
    semantic_search = SemanticSearch()
    hybrid_search = create_hybrid_search()

    # Sample queries
    queries = [
        "Python programming techniques",
        "Machine learning applications in data analysis",
        "Database optimization strategies",
        "Web development frameworks and tools",
    ]

    for query in queries:
        logger.info(f"\nComparing search approaches for: '{query}'")

        # Perform searches
        keyword_results = keyword_search.search(query, documents)
        semantic_results = semantic_search.search(query, documents)
        hybrid_results = hybrid_search.search(query, documents)

        # Print results
        logger.info("Keyword search results:")
        print_search_results(keyword_results, max_results=3)

        logger.info("Semantic search results:")
        print_search_results(semantic_results, max_results=3)

        logger.info("Hybrid search results:")
        print_search_results(hybrid_results, max_results=3)

        # Compare result sets
        keyword_ids = {r.document.id for r in keyword_results}
        semantic_ids = {r.document.id for r in semantic_results}
        hybrid_ids = {r.document.id for r in hybrid_results}

        logger.info("Result set comparison:")
        logger.info(
            f"  Documents in keyword but not semantic: {keyword_ids - semantic_ids}"
        )
        logger.info(
            f"  Documents in semantic but not keyword: {semantic_ids - keyword_ids}"
        )
        logger.info(
            f"  Documents in hybrid but not keyword: {hybrid_ids - keyword_ids}"
        )
        logger.info(
            f"  Documents in hybrid but not semantic: {hybrid_ids - semantic_ids}"
        )
        logger.info(
            f"  Documents in all three approaches: {keyword_ids & semantic_ids & hybrid_ids}"
        )


def demonstrate_custom_use_case(documents: List[Document]) -> None:
    """
    Demonstrate a custom use case with specialized configuration.

    Args:
        documents: The documents to search
    """
    logger.info("\n=== Demonstrating Custom Use Case ===")

    # Create a specialized hybrid search for technical documentation
    keyword_config = KeywordSearchConfig(
        algorithm="BM25", min_score=0.05, max_results=10, highlight=True
    )

    semantic_config = SemanticSearchConfig(
        model_name="technical-docs-model",
        min_score=0.6,
        max_results=10,
        normalize_scores=True,
    )

    hybrid_config = HybridSearchConfig(
        keyword_weight=0.3,  # Lower weight for keywords
        semantic_weight=0.7,  # Higher weight for semantic understanding
        fusion_method="linear_combination",
        max_results=5,
        deduplicate=True,
        rerank=True,
    )

    technical_search = create_hybrid_search(
        keyword_config=keyword_config,
        semantic_config=semantic_config,
        hybrid_config=hybrid_config,
    )

    # Sample technical queries
    technical_queries = [
        "How to implement a REST API with Python?",
        "What are the best practices for securing cloud applications?",
        "How does continuous integration improve software quality?",
        "What techniques are used for natural language understanding?",
    ]

    for query in technical_queries:
        logger.info(f"\nPerforming technical documentation search for: '{query}'")

        # Perform search
        results = technical_search.search(query, documents)

        # Print results
        logger.info("Technical documentation search results:")
        print_search_results(results)


def main():
    """Run the hybrid search examples."""
    logger.info("Starting Hybrid Search Example")

    # Create sample documents
    documents = create_sample_documents()
    logger.info(f"Created {len(documents)} sample documents")

    # Set random seed for reproducibility
    random.seed(42)

    # Demonstrate each search approach
    demonstrate_keyword_search(documents)
    demonstrate_semantic_search(documents)
    demonstrate_hybrid_search(documents)

    # Compare search approaches
    compare_search_approaches(documents)

    # Demonstrate custom use case
    demonstrate_custom_use_case(documents)

    logger.info("\nHybrid Search Example Completed")


if __name__ == "__main__":
    main()
