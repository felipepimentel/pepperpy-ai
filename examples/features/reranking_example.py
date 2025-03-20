#!/usr/bin/env python
"""
Example demonstrating the reranking strategies of the RAG module.

Purpose:
    Demonstrate how to use different reranking strategies to improve search results:
    - Cross-encoder reranking for scoring query-document pairs
    - Feature-based reranking using multiple features
    - Ensemble reranking combining multiple strategies
    - Custom reranking with user-defined functions

Requirements:
    - Python 3.9+
    - Pepperpy library

Usage:
    1. Install dependencies:
       poetry install

    2. Run the example:
       poetry run python examples/reranking_example.py
"""

import logging
import sys
from pathlib import Path
from typing import List, Optional

# Add the parent directory to the path so we can import the pepperpy package
sys.path.append(str(Path(__file__).parent.parent))

from pepperpy.rag.reranking import (
    CrossEncoderConfig,
    CrossEncoderReranker,
    EnsembleConfig,
    Feature,
    FeatureBasedConfig,
    FeatureBasedReranker,
    SearchResult,
    SearchResults,
    create_cross_encoder_reranker,
    create_ensemble_reranker,
    create_feature_based_reranker,
)
from pepperpy.types.common import Document, Metadata

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def create_sample_documents() -> List[Document]:
    """
    Create a sample document collection for reranking testing.

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
                "relevance": 0.85,
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
                "relevance": 0.92,
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
                "relevance": 0.78,
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
                "relevance": 0.81,
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
                "relevance": 0.75,
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
                "relevance": 0.88,
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
                "relevance": 0.79,
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
                "relevance": 0.90,
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
                "relevance": 0.82,
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
                "relevance": 0.84,
            }),
        )
    )

    return documents


def create_sample_search_results(
    query: str, documents: List[Document], scores: Optional[List[float]] = None
) -> SearchResults:
    """
    Create sample search results for reranking.

    Args:
        query: The search query
        documents: The documents to include in the results
        scores: Optional scores for each document (if None, random scores will be assigned)

    Returns:
        A SearchResults object containing the documents
    """
    if scores is None:
        # Use metadata relevance as scores if available
        scores = []
        for doc in documents:
            relevance = doc.metadata.get("relevance")
            if relevance is not None:
                scores.append(float(relevance))
            else:
                # Fallback to a default score
                scores.append(0.75)

    search_results = []
    for i, (doc, score) in enumerate(zip(documents, scores)):
        # Create highlights based on query terms
        highlights = []
        for term in query.lower().split():
            if term in doc.content.lower():
                # Find a sentence containing the term
                sentences = doc.content.split(".")
                for sentence in sentences:
                    if term in sentence.lower():
                        highlights.append(f"{sentence.strip()}.")
                        break

        # Limit to 2 highlights
        highlights = highlights[:2]

        # Create search result
        result = SearchResult(
            document=doc,
            score=score,
            rank=i + 1,
            highlights=highlights,
            metadata={"original_score": score},
        )
        search_results.append(result)

    return SearchResults(results=search_results, query=query)


def print_search_results(results: SearchResults, title: str = "Search Results") -> None:
    """
    Print search results in a readable format.

    Args:
        results: The search results to print
        title: Title for the results section
    """
    logger.info(f"\n{title}")
    logger.info(f"Query: '{results.query}'")
    logger.info(f"Total results: {len(results)}")

    if results.metadata:
        logger.info("Metadata:")
        for key, value in results.metadata.items():
            logger.info(f"  {key}: {value}")

    logger.info("Results:")
    for i, result in enumerate(results):
        logger.info(f"  {i + 1}. Document: {result.document.id}")
        logger.info(f"     Title: {result.document.metadata.get('title', 'No title')}")
        logger.info(f"     Score: {result.score:.4f}")
        logger.info(f"     Rank: {result.rank if result.rank is not None else 'N/A'}")

        # Print metadata if available
        if result.metadata:
            logger.info("     Metadata:")
            for key, value in result.metadata.items():
                logger.info(f"       {key}: {value}")

        # Print highlights if available
        if result.highlights:
            logger.info("     Highlights:")
            for j, highlight in enumerate(result.highlights[:2]):
                logger.info(f"       {j + 1}. {highlight}")

        logger.info("")

    logger.info("-" * 80)


def demonstrate_cross_encoder_reranking(documents: List[Document]) -> None:
    """
    Demonstrate cross-encoder reranking.

    Args:
        documents: The documents to search
    """
    logger.info("=== Demonstrating Cross-Encoder Reranking ===")

    # Create sample queries
    queries = [
        "Python programming for data analysis",
        "Machine learning and artificial intelligence applications",
        "Cloud security best practices",
        "Web development with Python frameworks",
    ]

    for query in queries:
        logger.info(f"\nReranking results for query: '{query}'")

        # Create initial search results
        initial_results = create_sample_search_results(query, documents)
        print_search_results(initial_results, "Initial Search Results")

        # Create cross-encoder reranker with default configuration
        default_reranker = create_cross_encoder_reranker()

        # Rerank the results
        reranked_results = default_reranker.rerank(initial_results)
        print_search_results(reranked_results, "Cross-Encoder Reranked Results")

        # Create cross-encoder reranker with custom configuration
        custom_config = CrossEncoderConfig(
            model_name="custom-model",
            max_length=256,
            batch_size=8,
            normalize_scores=True,
        )
        custom_reranker = CrossEncoderReranker(config=custom_config)

        # Rerank the results with custom configuration
        custom_reranked_results = custom_reranker.rerank(initial_results)
        print_search_results(
            custom_reranked_results, "Custom Cross-Encoder Reranked Results"
        )


def demonstrate_feature_based_reranking(documents: List[Document]) -> None:
    """
    Demonstrate feature-based reranking.

    Args:
        documents: The documents to search
    """
    logger.info("\n=== Demonstrating Feature-Based Reranking ===")

    # Create sample queries
    queries = [
        "Database systems and optimization techniques",
        "Software engineering and agile methodologies",
        "DevOps practices and continuous integration",
        "Cybersecurity and encryption methods",
    ]

    for query in queries:
        logger.info(f"\nReranking results for query: '{query}'")

        # Create initial search results
        initial_results = create_sample_search_results(query, documents)
        print_search_results(initial_results, "Initial Search Results")

        # Create feature-based reranker with default features
        default_reranker = create_feature_based_reranker()

        # Rerank the results
        reranked_results = default_reranker.rerank(initial_results)
        print_search_results(reranked_results, "Feature-Based Reranked Results")

        # Create custom features
        custom_features = [
            Feature(
                name="exact_phrase_match",
                weight=2.0,
                extractor=lambda q, doc: 1.0
                if q.lower() in doc.content.lower()
                else 0.0,
            ),
            Feature(
                name="title_match",
                weight=1.5,
                extractor=lambda q, doc: sum(
                    1.0
                    for term in q.lower().split()
                    if term in doc.metadata.get("title", "").lower()
                )
                / max(1, len(q.split())),
            ),
            Feature(
                name="category_relevance",
                weight=1.0,
                extractor=lambda q, doc: 1.0
                if any(
                    category.lower() in q.lower()
                    for category in [doc.metadata.get("category", "")]
                )
                else 0.5,
            ),
        ]

        # Create feature-based reranker with custom features
        custom_config = FeatureBasedConfig(features=custom_features)
        custom_reranker = FeatureBasedReranker(config=custom_config)

        # Rerank the results with custom features
        custom_reranked_results = custom_reranker.rerank(initial_results)
        print_search_results(
            custom_reranked_results, "Custom Feature-Based Reranked Results"
        )


def demonstrate_ensemble_reranking(documents: List[Document]) -> None:
    """
    Demonstrate ensemble reranking.

    Args:
        documents: The documents to search
    """
    logger.info("\n=== Demonstrating Ensemble Reranking ===")

    # Create sample queries
    queries = [
        "Python libraries for data analysis and visualization",
        "Artificial intelligence and natural language processing",
        "Web development frameworks and backend technologies",
        "Cloud computing platforms and serverless architecture",
    ]

    for query in queries:
        logger.info(f"\nReranking results for query: '{query}'")

        # Create initial search results
        initial_results = create_sample_search_results(query, documents)
        print_search_results(initial_results, "Initial Search Results")

        # Create individual rerankers for the ensemble
        cross_encoder_reranker = create_cross_encoder_reranker()
        feature_based_reranker = create_feature_based_reranker()

        # Create ensemble reranker
        ensemble_reranker = create_ensemble_reranker(
            rerankers=[
                (cross_encoder_reranker, 0.7),  # 70% weight for cross-encoder
                (feature_based_reranker, 0.3),  # 30% weight for feature-based
            ]
        )

        # Rerank the results with the ensemble
        ensemble_results = ensemble_reranker.rerank(initial_results)
        print_search_results(ensemble_results, "Ensemble Reranked Results")

        # Create a more complex ensemble with custom weights
        complex_ensemble_config = EnsembleConfig(
            rerankers=[
                (cross_encoder_reranker, 0.5),  # 50% weight for cross-encoder
                (feature_based_reranker, 0.5),  # 50% weight for feature-based
            ],
            normalize_scores=True,
        )
        complex_ensemble_reranker = create_ensemble_reranker(
            rerankers=[
                (cross_encoder_reranker, 0.5),
                (feature_based_reranker, 0.5),
            ],
            normalize_scores=True,
        )

        # Rerank the results with the complex ensemble
        complex_ensemble_results = complex_ensemble_reranker.rerank(initial_results)
        print_search_results(
            complex_ensemble_results, "Complex Ensemble Reranked Results"
        )


def demonstrate_custom_reranking(documents: List[Document]) -> None:
    """
    Demonstrate custom reranking with user-defined functions.

    Args:
        documents: The documents to search
    """
    logger.info("\n=== Demonstrating Custom Reranking ===")

    # Create sample queries
    queries = [
        "Python programming best practices",
        "Machine learning model evaluation techniques",
        "Database performance optimization strategies",
        "Web application security measures",
    ]

    for query in queries:
        logger.info(f"\nReranking results for query: '{query}'")

        # Create initial search results
        initial_results = create_sample_search_results(query, documents)
        print_search_results(initial_results, "Initial Search Results")

        # Define a custom reranking function that boosts documents with specific tags
        def custom_tag_boosting_reranker(results: SearchResults) -> SearchResults:
            """Custom reranker that boosts documents with specific tags."""
            # Define important tags for the query
            important_tags = set()
            if "python" in query.lower():
                important_tags.update(["python", "programming"])
            if "machine learning" in query.lower() or "ml" in query.lower():
                important_tags.update(["machine learning", "AI", "data science"])
            if "database" in query.lower() or "sql" in query.lower():
                important_tags.update(["database", "SQL", "NoSQL"])
            if "web" in query.lower():
                important_tags.update(["web", "frontend", "backend"])
            if "security" in query.lower():
                important_tags.update(["security", "cybersecurity", "encryption"])

            # Create new results with boosted scores
            new_results = []
            for result in results:
                # Get document tags
                doc_tags = set(result.document.metadata.get("tags", []))

                # Calculate tag overlap
                tag_overlap = len(important_tags.intersection(doc_tags))

                # Boost score based on tag overlap
                boost_factor = 1.0 + (tag_overlap * 0.1)  # 10% boost per matching tag
                new_score = result.score * boost_factor

                # Create new result with boosted score
                new_result = SearchResult(
                    document=result.document,
                    score=new_score,
                    rank=None,  # Will be recalculated
                    highlights=result.highlights,
                    metadata={
                        "original_score": result.score,
                        "boost_factor": boost_factor,
                        "matching_tags": tag_overlap,
                    },
                )
                new_results.append(new_result)

            # Create new SearchResults with boosted scores
            new_search_results = SearchResults(
                results=new_results,
                query=results.query,
                metadata={
                    "reranking_method": "custom_tag_boosting",
                    "important_tags": list(important_tags),
                },
            )

            # Sort by score
            return new_search_results.sort_by_score()

        # Apply custom reranking
        custom_reranked_results = custom_tag_boosting_reranker(initial_results)
        print_search_results(custom_reranked_results, "Custom Tag-Boosted Results")

        # Define another custom reranker that combines original score with metadata relevance
        def relevance_weighted_reranker(results: SearchResults) -> SearchResults:
            """Custom reranker that weights original score with metadata relevance."""
            new_results = []
            for result in results:
                # Get relevance from metadata
                relevance = result.document.metadata.get("relevance", 0.5)

                # Combine original score with relevance (50% each)
                combined_score = (result.score * 0.5) + (relevance * 0.5)

                # Create new result with combined score
                new_result = SearchResult(
                    document=result.document,
                    score=combined_score,
                    rank=None,  # Will be recalculated
                    highlights=result.highlights,
                    metadata={
                        "original_score": result.score,
                        "relevance": relevance,
                        "weight_formula": "0.5 * original_score + 0.5 * relevance",
                    },
                )
                new_results.append(new_result)

            # Create new SearchResults with combined scores
            new_search_results = SearchResults(
                results=new_results,
                query=results.query,
                metadata={"reranking_method": "relevance_weighted"},
            )

            # Sort by score
            return new_search_results.sort_by_score()

        # Apply relevance-weighted reranking
        relevance_reranked_results = relevance_weighted_reranker(initial_results)
        print_search_results(
            relevance_reranked_results, "Relevance-Weighted Reranked Results"
        )


def compare_reranking_strategies(documents: List[Document]) -> None:
    """
    Compare different reranking strategies on the same query.

    Args:
        documents: The documents to search
    """
    logger.info("\n=== Comparing Reranking Strategies ===")

    # Create a complex query that touches multiple topics
    query = (
        "Python frameworks for machine learning and data analysis in cloud environments"
    )
    logger.info(f"\nComparing reranking strategies for query: '{query}'")

    # Create initial search results
    initial_results = create_sample_search_results(query, documents)
    print_search_results(initial_results, "Initial Search Results")

    # Create rerankers
    cross_encoder_reranker = create_cross_encoder_reranker()
    feature_based_reranker = create_feature_based_reranker()
    ensemble_reranker = create_ensemble_reranker(
        rerankers=[
            (cross_encoder_reranker, 0.6),
            (feature_based_reranker, 0.4),
        ]
    )

    # Apply each reranking strategy
    cross_encoder_results = cross_encoder_reranker.rerank(initial_results)
    feature_based_results = feature_based_reranker.rerank(initial_results)
    ensemble_results = ensemble_reranker.rerank(initial_results)

    # Print results from each strategy
    print_search_results(cross_encoder_results, "Cross-Encoder Reranked Results")
    print_search_results(feature_based_results, "Feature-Based Reranked Results")
    print_search_results(ensemble_results, "Ensemble Reranked Results")

    # Compare top 3 documents from each strategy
    logger.info("\nTop 3 Documents Comparison:")

    def get_top_ids(results: SearchResults, k: int = 3) -> List[str]:
        """Get IDs of top k documents in results."""
        return [result.document.id for result in results.top_k(k)]

    initial_top_ids = get_top_ids(initial_results)
    cross_encoder_top_ids = get_top_ids(cross_encoder_results)
    feature_based_top_ids = get_top_ids(feature_based_results)
    ensemble_top_ids = get_top_ids(ensemble_results)

    logger.info(f"Initial top 3: {initial_top_ids}")
    logger.info(f"Cross-encoder top 3: {cross_encoder_top_ids}")
    logger.info(f"Feature-based top 3: {feature_based_top_ids}")
    logger.info(f"Ensemble top 3: {ensemble_top_ids}")

    # Calculate overlap between strategies
    logger.info("\nStrategy Overlap (Jaccard similarity):")

    def jaccard_similarity(list1: List[str], list2: List[str]) -> float:
        """Calculate Jaccard similarity between two lists."""
        set1 = set(list1)
        set2 = set(list2)
        return len(set1.intersection(set2)) / len(set1.union(set2))

    logger.info(
        f"Initial vs Cross-encoder: {jaccard_similarity(initial_top_ids, cross_encoder_top_ids):.2f}"
    )
    logger.info(
        f"Initial vs Feature-based: {jaccard_similarity(initial_top_ids, feature_based_top_ids):.2f}"
    )
    logger.info(
        f"Initial vs Ensemble: {jaccard_similarity(initial_top_ids, ensemble_top_ids):.2f}"
    )
    logger.info(
        f"Cross-encoder vs Feature-based: {jaccard_similarity(cross_encoder_top_ids, feature_based_top_ids):.2f}"
    )
    logger.info(
        f"Cross-encoder vs Ensemble: {jaccard_similarity(cross_encoder_top_ids, ensemble_top_ids):.2f}"
    )
    logger.info(
        f"Feature-based vs Ensemble: {jaccard_similarity(feature_based_top_ids, ensemble_top_ids):.2f}"
    )


def main() -> None:
    """Run the reranking examples."""
    logger.info("Starting Reranking Example")

    # Create sample documents
    documents = create_sample_documents()
    logger.info(f"Created {len(documents)} sample documents")

    # Demonstrate each reranking strategy
    demonstrate_cross_encoder_reranking(documents)
    demonstrate_feature_based_reranking(documents)
    demonstrate_ensemble_reranking(documents)
    demonstrate_custom_reranking(documents)

    # Compare reranking strategies
    compare_reranking_strategies(documents)

    logger.info("\nReranking Example Completed")


if __name__ == "__main__":
    main()
