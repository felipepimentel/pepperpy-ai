#!/usr/bin/env python
"""
Example demonstrating the query planning and optimization layer of the RAG module.

This example shows how to:
1. Create and configure a query planning pipeline
2. Decompose complex queries into sub-queries
3. Optimize queries for better retrieval
4. Create execution plans for different query types
5. Process queries through the complete pipeline
"""

import logging
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple, cast

# Add the parent directory to the path so we can import the pepperpy package
sys.path.append(str(Path(__file__).parent.parent))

from pepperpy.rag.query_planning import (
    QueryDecomposer,
    QueryExecutionPlanner,
    QueryOptimizer,
    QueryPlan,
    QueryType,
    SubQuery,
    create_query_planning_pipeline,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def custom_decomposition_strategy(query: str) -> List[SubQuery]:
    """
    A custom decomposition strategy that breaks down queries based on predefined patterns.

    Args:
        query: The query to decompose

    Returns:
        A list of SubQuery objects
    """
    sub_queries = []

    # Check for comparison patterns
    if "compare" in query.lower() or "difference between" in query.lower():
        parts = query.split(" and ")
        if len(parts) > 1:
            for i, part in enumerate(parts):
                sub_queries.append(
                    SubQuery(
                        text=part.strip(),
                        query_type=QueryType.COMPARATIVE,
                        weight=1.0,
                        parent_query=query,
                    )
                )

    # Check for procedural patterns
    elif "how to" in query.lower() or "steps to" in query.lower():
        sub_queries.append(
            SubQuery(
                text=query,
                query_type=QueryType.PROCEDURAL,
                weight=1.0,
                parent_query=query,
            )
        )

        # Add a sub-query for prerequisites
        sub_queries.append(
            SubQuery(
                text=f"prerequisites for {query.replace('how to ', '')}",
                query_type=QueryType.FACTUAL,
                weight=0.7,
                parent_query=query,
            )
        )

    # Default to factual for other queries
    else:
        sub_queries.append(
            SubQuery(
                text=query, query_type=QueryType.FACTUAL, weight=1.0, parent_query=query
            )
        )

    return sub_queries


def create_sample_expansion_terms() -> Dict[str, List[str]]:
    """
    Create a sample dictionary of term expansions for query optimization.

    Returns:
        A dictionary mapping terms to their expansions
    """
    return {
        "python": ["programming", "language", "code"],
        "database": ["sql", "storage", "data"],
        "machine learning": ["ml", "ai", "model", "training"],
        "api": ["interface", "endpoint", "service"],
        "cloud": ["aws", "azure", "gcp", "hosting"],
    }


def create_sample_rewriting_rules() -> List[Tuple[str, str]]:
    """
    Create a sample list of rewriting rules for query optimization.

    Returns:
        A list of (pattern, replacement) tuples
    """
    return [
        ("best way to", "optimal method for"),
        ("difference between", "comparison of"),
        ("example of", "sample implementation of"),
        ("how do i", "procedure for"),
    ]


def mock_factual_retrieval(query: str) -> Dict[str, Any]:
    """Mock retrieval function for factual queries."""
    return {"strategy": "vector_search", "top_k": 5}


def mock_procedural_retrieval(query: str) -> Dict[str, Any]:
    """Mock retrieval function for procedural queries."""
    return {"strategy": "hybrid_search", "top_k": 3, "filter": {"type": "tutorial"}}


def mock_comparative_retrieval(query: str) -> Dict[str, Any]:
    """Mock retrieval function for comparative queries."""
    return {"strategy": "multi_query", "top_k": 10, "rerank": True}


def demonstrate_query_decomposition():
    """Demonstrate query decomposition with different strategies."""
    logger.info("=== Demonstrating Query Decomposition ===")

    # Create a decomposer with the default strategy
    default_decomposer = QueryDecomposer(max_sub_queries=3)

    # Create a decomposer with a custom strategy
    custom_decomposer = QueryDecomposer(
        decomposition_strategy=custom_decomposition_strategy, max_sub_queries=5
    )

    # Sample queries
    queries = [
        "What is the difference between Python and JavaScript and how are they used?",
        "How to implement a REST API in Python?",
        "What are the best practices for database optimization?",
    ]

    for query in queries:
        logger.info(f"\nProcessing query: '{query}'")

        # Decompose with default strategy
        default_plan = default_decomposer.decompose(query)
        logger.info(
            f"Default decomposition - {len(default_plan.sub_queries)} sub-queries:"
        )
        for i, sq in enumerate(default_plan.sub_queries):
            logger.info(
                f"  {i + 1}. '{sq.text}' (Type: {sq.query_type.name}, Weight: {sq.weight})"
            )

        # Decompose with custom strategy
        custom_plan = custom_decomposer.decompose(query)
        logger.info(
            f"Custom decomposition - {len(custom_plan.sub_queries)} sub-queries:"
        )
        for i, sq in enumerate(custom_plan.sub_queries):
            logger.info(
                f"  {i + 1}. '{sq.text}' (Type: {sq.query_type.name}, Weight: {sq.weight})"
            )


def demonstrate_query_optimization():
    """Demonstrate query optimization with different configurations."""
    logger.info("\n=== Demonstrating Query Optimization ===")

    # Create an optimizer with sample expansion terms and rewriting rules
    optimizer = QueryOptimizer(
        expansion_terms=create_sample_expansion_terms(),
        rewriting_rules=create_sample_rewriting_rules(),
    )

    # Sample queries
    queries = [
        "best way to learn python",
        "difference between SQL and NoSQL database",
        "example of machine learning in cloud applications",
    ]

    for query in queries:
        logger.info(f"\nOriginal query: '{query}'")

        # Optimize as string
        optimized_string = cast(str, optimizer.optimize(query))
        logger.info(f"Optimized string: '{optimized_string}'")

        # Optimize as SubQuery
        sub_query = SubQuery(text=query, query_type=QueryType.FACTUAL)
        optimized_sub_query = cast(SubQuery, optimizer.optimize(sub_query))
        logger.info(f"Optimized SubQuery: '{optimized_sub_query.text}'")

        # Optimize as QueryPlan
        query_plan = QueryPlan(original_query=query)
        query_plan.add_sub_query(SubQuery(text=query, query_type=QueryType.FACTUAL))
        optimized_plan = cast(QueryPlan, optimizer.optimize(query_plan))
        logger.info(f"Optimized QueryPlan original: '{optimized_plan.original_query}'")
        logger.info(
            f"Optimized QueryPlan sub-query: '{optimized_plan.sub_queries[0].text}'"
        )


def demonstrate_execution_planning():
    """Demonstrate execution planning for different query types."""
    logger.info("\n=== Demonstrating Execution Planning ===")

    # Create a planner with mock retrieval strategies
    retrieval_strategies = {
        QueryType.FACTUAL: mock_factual_retrieval,
        QueryType.PROCEDURAL: mock_procedural_retrieval,
        QueryType.COMPARATIVE: mock_comparative_retrieval,
    }

    planner = QueryExecutionPlanner(
        retrieval_strategies=retrieval_strategies,
        default_strategy=mock_factual_retrieval,
    )

    # Create sample query plans
    query_plans = [
        # Factual query plan
        QueryPlan(
            original_query="What is Python?",
            sub_queries=[
                SubQuery(
                    text="Python programming language", query_type=QueryType.FACTUAL
                ),
                SubQuery(
                    text="Python history", query_type=QueryType.FACTUAL, weight=0.8
                ),
            ],
        ),
        # Procedural query plan
        QueryPlan(
            original_query="How to implement a REST API?",
            sub_queries=[
                SubQuery(
                    text="REST API implementation steps",
                    query_type=QueryType.PROCEDURAL,
                ),
                SubQuery(
                    text="REST API best practices",
                    query_type=QueryType.FACTUAL,
                    weight=0.7,
                ),
            ],
        ),
        # Comparative query plan
        QueryPlan(
            original_query="Compare SQL and NoSQL databases",
            sub_queries=[
                SubQuery(
                    text="SQL databases", query_type=QueryType.COMPARATIVE, weight=1.0
                ),
                SubQuery(
                    text="NoSQL databases", query_type=QueryType.COMPARATIVE, weight=1.0
                ),
                SubQuery(
                    text="SQL vs NoSQL performance",
                    query_type=QueryType.COMPARATIVE,
                    weight=0.9,
                ),
            ],
        ),
    ]

    for plan in query_plans:
        logger.info(f"\nCreating execution plan for: '{plan.original_query}'")
        execution_plan = planner.create_execution_plan(plan)

        logger.info("Execution plan details:")
        logger.info(f"  Original query: '{execution_plan['original_query']}'")
        logger.info(f"  Is decomposed: {execution_plan['is_decomposed']}")

        if execution_plan["is_decomposed"]:
            logger.info("  Sub-query strategies:")
            for i, strategy in enumerate(execution_plan["sub_query_strategies"]):
                logger.info(
                    f"    {i + 1}. '{strategy['sub_query']}' "
                    f"(Type: {strategy['query_type']}, "
                    f"Strategy: {strategy['strategy']}, "
                    f"Weight: {strategy['weight']})"
                )


def demonstrate_complete_pipeline():
    """Demonstrate the complete query planning pipeline."""
    logger.info("\n=== Demonstrating Complete Query Planning Pipeline ===")

    # Create a complete pipeline
    pipeline = create_query_planning_pipeline(
        decomposition_strategy=custom_decomposition_strategy,
        expansion_terms=create_sample_expansion_terms(),
        rewriting_rules=create_sample_rewriting_rules(),
        retrieval_strategies={
            QueryType.FACTUAL: mock_factual_retrieval,
            QueryType.PROCEDURAL: mock_procedural_retrieval,
            QueryType.COMPARATIVE: mock_comparative_retrieval,
        },
        default_strategy=mock_factual_retrieval,
        max_sub_queries=5,
    )

    # Sample complex queries
    queries = [
        "How to implement authentication in a Python web application?",
        "Compare MongoDB and PostgreSQL for storing user data",
        "What are the best practices for securing REST APIs?",
    ]

    for query in queries:
        logger.info(f"\nProcessing query through pipeline: '{query}'")
        execution_plan = pipeline.process_query(query)

        logger.info("Final execution plan:")
        logger.info(f"  Original query: '{execution_plan['original_query']}'")
        logger.info(f"  Is decomposed: {execution_plan['is_decomposed']}")

        if execution_plan["is_decomposed"]:
            logger.info("  Sub-query strategies:")
            for i, strategy in enumerate(execution_plan["sub_query_strategies"]):
                logger.info(
                    f"    {i + 1}. '{strategy['sub_query']}' "
                    f"(Type: {strategy['query_type']}, "
                    f"Strategy: {strategy['strategy']}, "
                    f"Weight: {strategy['weight']})"
                )


def main():
    """Run the query planning examples."""
    logger.info("Starting Query Planning Example")

    # Demonstrate each component
    demonstrate_query_decomposition()
    demonstrate_query_optimization()
    demonstrate_execution_planning()
    demonstrate_complete_pipeline()

    logger.info("\nQuery Planning Example Completed")


if __name__ == "__main__":
    main()
