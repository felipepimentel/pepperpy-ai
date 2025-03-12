"""
Query planning and optimization layer for the RAG module.

This module provides components for query decomposition, optimization, and execution planning
to improve retrieval quality and efficiency in RAG systems. It includes:

1. Query decomposition: Breaking complex queries into simpler sub-queries
2. Query optimization: Rewriting and enhancing queries for better retrieval
3. Query execution planning: Determining the optimal retrieval strategy
"""

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Callable, Dict, List, Optional, Tuple, Union, cast, overload


class QueryType(Enum):
    """Types of queries that can be processed by the query planner."""

    FACTUAL = auto()  # Queries seeking factual information
    ANALYTICAL = auto()  # Queries requiring analysis or synthesis
    PROCEDURAL = auto()  # Queries about how to do something
    COMPARATIVE = auto()  # Queries comparing multiple items
    EXPLORATORY = auto()  # Open-ended, exploratory queries
    CLARIFICATION = auto()  # Queries seeking clarification on a topic
    HYPOTHETICAL = auto()  # Queries about hypothetical scenarios


@dataclass
class SubQuery:
    """Represents a decomposed part of a complex query."""

    text: str
    query_type: QueryType
    weight: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    parent_query: Optional[str] = None


@dataclass
class QueryPlan:
    """Represents a plan for executing a query or set of sub-queries."""

    original_query: str
    sub_queries: List[SubQuery] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def add_sub_query(self, sub_query: SubQuery) -> None:
        """Add a sub-query to the plan."""
        self.sub_queries.append(sub_query)

    @property
    def is_decomposed(self) -> bool:
        """Check if the query has been decomposed into sub-queries."""
        return len(self.sub_queries) > 0


class QueryDecomposer:
    """Decomposes complex queries into simpler sub-queries."""

    def __init__(
        self,
        decomposition_strategy: Optional[Callable[[str], List[SubQuery]]] = None,
        max_sub_queries: int = 5,
    ):
        """
        Initialize the query decomposer.

        Args:
            decomposition_strategy: Custom function for decomposing queries
            max_sub_queries: Maximum number of sub-queries to generate
        """
        self.decomposition_strategy = decomposition_strategy
        self.max_sub_queries = max_sub_queries

    def decompose(self, query: str) -> QueryPlan:
        """
        Decompose a complex query into sub-queries.

        Args:
            query: The original query to decompose

        Returns:
            A QueryPlan containing the original query and its sub-queries
        """
        plan = QueryPlan(original_query=query)

        if self.decomposition_strategy:
            sub_queries = self.decomposition_strategy(query)
            for sq in sub_queries[: self.max_sub_queries]:
                plan.add_sub_query(sq)
        else:
            # Default decomposition strategy (simple keyword extraction)
            # In a real implementation, this would use more sophisticated NLP
            keywords = self._extract_keywords(query)
            for keyword in keywords[: self.max_sub_queries]:
                sub_query = SubQuery(
                    text=f"{keyword}", query_type=QueryType.FACTUAL, parent_query=query
                )
                plan.add_sub_query(sub_query)

        return plan

    def _extract_keywords(self, query: str) -> List[str]:
        """
        Extract keywords from a query.

        Args:
            query: The query to extract keywords from

        Returns:
            A list of keywords
        """
        # Simple keyword extraction (in a real implementation, use NLP)
        words = query.lower().split()
        # Remove common stop words (very simplified)
        stop_words = {"the", "a", "an", "in", "on", "at", "to", "for", "with", "by"}
        keywords = [word for word in words if word not in stop_words and len(word) > 3]
        return keywords


class QueryOptimizer:
    """Optimizes queries for better retrieval performance."""

    def __init__(
        self,
        expansion_terms: Optional[Dict[str, List[str]]] = None,
        rewriting_rules: Optional[List[Tuple[str, str]]] = None,
    ):
        """
        Initialize the query optimizer.

        Args:
            expansion_terms: Dictionary mapping terms to their expansions
            rewriting_rules: List of (pattern, replacement) tuples for query rewriting
        """
        self.expansion_terms = expansion_terms or {}
        self.rewriting_rules = rewriting_rules or []

    @overload
    def optimize(self, query: str) -> str: ...

    @overload
    def optimize(self, query: SubQuery) -> SubQuery: ...

    @overload
    def optimize(self, query: QueryPlan) -> QueryPlan: ...

    def optimize(
        self, query: Union[str, SubQuery, QueryPlan]
    ) -> Union[str, SubQuery, QueryPlan]:
        """
        Optimize a query for better retrieval.

        Args:
            query: The query to optimize (string, SubQuery, or QueryPlan)

        Returns:
            The optimized query in the same format as the input
        """
        if isinstance(query, str):
            return self._optimize_string_query(query)
        elif isinstance(query, SubQuery):
            optimized_text = self._optimize_string_query(query.text)
            query.text = optimized_text
            return query
        elif isinstance(query, QueryPlan):
            # Optimize the original query
            query.original_query = self._optimize_string_query(query.original_query)
            # Optimize each sub-query
            for i, sub_query in enumerate(query.sub_queries):
                query.sub_queries[i] = cast(SubQuery, self.optimize(sub_query))
            return query
        else:
            raise TypeError(f"Unsupported query type: {type(query)}")

    def _optimize_string_query(self, query: str) -> str:
        """
        Optimize a string query.

        Args:
            query: The string query to optimize

        Returns:
            The optimized string query
        """
        # Apply query expansion
        expanded_query = self._expand_query(query)

        # Apply rewriting rules
        rewritten_query = self._rewrite_query(expanded_query)

        return rewritten_query

    def _expand_query(self, query: str) -> str:
        """
        Expand a query with additional terms.

        Args:
            query: The query to expand

        Returns:
            The expanded query
        """
        words = query.split()
        expanded_words = []

        for word in words:
            expanded_words.append(word)
            if word.lower() in self.expansion_terms:
                for expansion in self.expansion_terms[word.lower()]:
                    if expansion not in expanded_words:
                        expanded_words.append(expansion)

        return " ".join(expanded_words)

    def _rewrite_query(self, query: str) -> str:
        """
        Rewrite a query using predefined rules.

        Args:
            query: The query to rewrite

        Returns:
            The rewritten query
        """
        rewritten = query
        for pattern, replacement in self.rewriting_rules:
            rewritten = rewritten.replace(pattern, replacement)

        return rewritten


class QueryExecutionPlanner:
    """Plans the execution of queries for optimal retrieval."""

    def __init__(
        self,
        retrieval_strategies: Optional[Dict[QueryType, Callable]] = None,
        default_strategy: Optional[Callable] = None,
    ):
        """
        Initialize the query execution planner.

        Args:
            retrieval_strategies: Mapping from query types to retrieval functions
            default_strategy: Default retrieval strategy to use
        """
        self.retrieval_strategies = retrieval_strategies or {}
        self.default_strategy = default_strategy

    def create_execution_plan(self, query_plan: QueryPlan) -> Dict[str, Any]:
        """
        Create an execution plan for a query plan.

        Args:
            query_plan: The query plan to create an execution plan for

        Returns:
            A dictionary containing the execution plan details
        """
        execution_plan = {
            "original_query": query_plan.original_query,
            "is_decomposed": query_plan.is_decomposed,
            "sub_query_strategies": [],
            "metadata": query_plan.metadata.copy(),
        }

        if query_plan.is_decomposed:
            for sub_query in query_plan.sub_queries:
                strategy = self._get_strategy_for_query_type(sub_query.query_type)
                execution_plan["sub_query_strategies"].append({
                    "sub_query": sub_query.text,
                    "query_type": sub_query.query_type.name,
                    "weight": sub_query.weight,
                    "strategy": strategy.__name__ if strategy else "default_strategy",
                })
        else:
            # If not decomposed, use a default strategy for the original query
            strategy = self.default_strategy
            execution_plan["strategy"] = (
                strategy.__name__ if strategy else "default_strategy"
            )

        return execution_plan

    def _get_strategy_for_query_type(self, query_type: QueryType) -> Optional[Callable]:
        """
        Get the retrieval strategy for a query type.

        Args:
            query_type: The type of query

        Returns:
            The retrieval strategy function, or None if not found
        """
        return self.retrieval_strategies.get(query_type, self.default_strategy)


class QueryPlanningPipeline:
    """Pipeline for query planning and optimization."""

    def __init__(
        self,
        decomposer: Optional[QueryDecomposer] = None,
        optimizer: Optional[QueryOptimizer] = None,
        planner: Optional[QueryExecutionPlanner] = None,
    ):
        """
        Initialize the query planning pipeline.

        Args:
            decomposer: Query decomposer component
            optimizer: Query optimizer component
            planner: Query execution planner component
        """
        self.decomposer = decomposer or QueryDecomposer()
        self.optimizer = optimizer or QueryOptimizer()
        self.planner = planner or QueryExecutionPlanner()

    def process_query(self, query: str) -> Dict[str, Any]:
        """
        Process a query through the planning pipeline.

        Args:
            query: The query to process

        Returns:
            A dictionary containing the execution plan
        """
        # Step 1: Decompose the query
        query_plan = self.decomposer.decompose(query)

        # Step 2: Optimize the query plan
        optimized_plan = cast(QueryPlan, self.optimizer.optimize(query_plan))

        # Step 3: Create an execution plan
        execution_plan = self.planner.create_execution_plan(optimized_plan)

        return execution_plan


def create_query_planning_pipeline(
    decomposition_strategy: Optional[Callable] = None,
    expansion_terms: Optional[Dict[str, List[str]]] = None,
    rewriting_rules: Optional[List[Tuple[str, str]]] = None,
    retrieval_strategies: Optional[Dict[QueryType, Callable]] = None,
    default_strategy: Optional[Callable] = None,
    max_sub_queries: int = 5,
) -> QueryPlanningPipeline:
    """
    Create a query planning pipeline with the specified components.

    Args:
        decomposition_strategy: Custom function for decomposing queries
        expansion_terms: Dictionary mapping terms to their expansions
        rewriting_rules: List of (pattern, replacement) tuples for query rewriting
        retrieval_strategies: Mapping from query types to retrieval functions
        default_strategy: Default retrieval strategy to use
        max_sub_queries: Maximum number of sub-queries to generate

    Returns:
        A configured QueryPlanningPipeline
    """
    decomposer = QueryDecomposer(
        decomposition_strategy=decomposition_strategy, max_sub_queries=max_sub_queries
    )

    optimizer = QueryOptimizer(
        expansion_terms=expansion_terms, rewriting_rules=rewriting_rules
    )

    planner = QueryExecutionPlanner(
        retrieval_strategies=retrieval_strategies, default_strategy=default_strategy
    )

    return QueryPlanningPipeline(
        decomposer=decomposer, optimizer=optimizer, planner=planner
    )
