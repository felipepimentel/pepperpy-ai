"""
Base evaluation module for PepperPy.

This module provides the core interfaces and base classes for evaluation.
"""

import json
import time
from dataclasses import dataclass, field
from typing import Any, Protocol

from pepperpy.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class EvaluationMetric:
    """A single evaluation metric."""

    name: str
    value: float | str | bool | int | dict[str, Any]
    weight: float = 1.0
    description: str = ""
    category: str = "general"
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class EvaluationResult:
    """Result of an evaluation."""

    name: str
    metrics: list[EvaluationMetric] = field(default_factory=list)
    score: float | None = None
    timestamp: float = field(default_factory=time.time)
    success: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)
    raw_data: dict[str, Any] = field(default_factory=dict)

    def add_metric(self, metric: EvaluationMetric) -> None:
        """Add a metric to the evaluation result."""
        self.metrics.append(metric)

    def calculate_score(self) -> float:
        """Calculate the overall score based on metrics."""
        if not self.metrics:
            return 0.0

        numeric_metrics = [
            m
            for m in self.metrics
            if isinstance(m.value, (int, float)) and m.weight > 0
        ]

        if not numeric_metrics:
            return 0.0

        total_weight = sum(m.weight for m in numeric_metrics)
        weighted_sum = sum(m.value * m.weight for m in numeric_metrics)

        if total_weight > 0:
            self.score = weighted_sum / total_weight
            return self.score
        return 0.0

    def get_metrics_by_category(self, category: str) -> list[EvaluationMetric]:
        """Get metrics by category."""
        return [m for m in self.metrics if m.category == category]

    def to_dict(self) -> dict[str, Any]:
        """Convert result to dictionary."""
        if self.score is None:
            self.calculate_score()

        return {
            "name": self.name,
            "score": self.score,
            "metrics": [
                {
                    "name": m.name,
                    "value": m.value,
                    "weight": m.weight,
                    "description": m.description,
                    "category": m.category,
                    "metadata": m.metadata,
                }
                for m in self.metrics
            ],
            "timestamp": self.timestamp,
            "success": self.success,
            "metadata": self.metadata,
        }

    def to_json(self, pretty: bool = False) -> str:
        """Convert result to JSON string."""
        if pretty:
            return json.dumps(self.to_dict(), indent=2)
        return json.dumps(self.to_dict())


@dataclass
class EvaluationSuite:
    """A suite of evaluations."""

    name: str
    description: str = ""
    evaluations: list[EvaluationResult] = field(default_factory=list)
    timestamp: float = field(default_factory=time.time)
    metadata: dict[str, Any] = field(default_factory=dict)

    def add_evaluation(self, evaluation: EvaluationResult) -> None:
        """Add an evaluation to the suite."""
        self.evaluations.append(evaluation)

    def get_average_score(self) -> float:
        """Get the average score across all evaluations."""
        if not self.evaluations:
            return 0.0

        scores = [
            e.score if e.score is not None else e.calculate_score()
            for e in self.evaluations
        ]
        if not scores:
            return 0.0

        return sum(scores) / len(scores)

    def to_dict(self) -> dict[str, Any]:
        """Convert suite to dictionary."""
        return {
            "name": self.name,
            "description": self.description,
            "average_score": self.get_average_score(),
            "evaluations": [e.to_dict() for e in self.evaluations],
            "timestamp": self.timestamp,
            "metadata": self.metadata,
        }

    def to_json(self, pretty: bool = False) -> str:
        """Convert suite to JSON string."""
        if pretty:
            return json.dumps(self.to_dict(), indent=2)
        return json.dumps(self.to_dict())


class Evaluator(Protocol):
    """Protocol for evaluators."""

    name: str

    async def initialize(self) -> None:
        """Initialize the evaluator."""
        ...

    async def cleanup(self) -> None:
        """Clean up resources."""
        ...

    async def evaluate(self, input_data: dict[str, Any]) -> EvaluationResult:
        """Evaluate something based on input data."""
        ...

    async def run_suite(
        self,
        inputs: list[dict[str, Any]],
        suite_name: str = "Evaluation Suite",
        description: str = "",
    ) -> EvaluationSuite:
        """Run a suite of evaluations."""
        ...


class BaseEvaluator:
    """Base class for evaluators."""

    def __init__(self, **kwargs) -> None:
        """Initialize with configuration."""
        self.config = kwargs
        self.name = kwargs.get("name", self.__class__.__name__)
        self.initialized = False
        self.logger = logger

    async def initialize(self) -> None:
        """Initialize the evaluator."""
        if self.initialized:
            return

        self.logger.debug(f"Initializing evaluator: {self.name}")
        self.initialized = True

    async def cleanup(self) -> None:
        """Clean up resources."""
        if not self.initialized:
            return

        self.logger.debug(f"Cleaning up evaluator: {self.name}")
        self.initialized = False

    async def evaluate(self, input_data: dict[str, Any]) -> EvaluationResult:
        """Evaluate something based on input data.

        Args:
            input_data: Input data for evaluation

        Returns:
            Evaluation result
        """
        if not self.initialized:
            await self.initialize()

        eval_name = input_data.get("evaluation_name", "Unnamed Evaluation")

        # Default implementation - should be overridden
        result = EvaluationResult(name=eval_name)
        result.add_metric(
            EvaluationMetric(
                name="default_metric",
                value=0.0,
                description="Default metric",
                category="default",
            )
        )

        return result

    async def run_suite(
        self,
        inputs: list[dict[str, Any]],
        suite_name: str = "Evaluation Suite",
        description: str = "",
    ) -> EvaluationSuite:
        """Run a suite of evaluations.

        Args:
            inputs: List of input data for evaluations
            suite_name: Name of the evaluation suite
            description: Description of the suite

        Returns:
            Evaluation suite result
        """
        if not self.initialized:
            await self.initialize()

        suite = EvaluationSuite(name=suite_name, description=description)

        for input_data in inputs:
            try:
                result = await self.evaluate(input_data)
                suite.add_evaluation(result)
            except Exception as e:
                self.logger.error(
                    f"Error evaluating {input_data.get('evaluation_name')}: {e}"
                )
                # Add failed evaluation
                failed_result = EvaluationResult(
                    name=input_data.get("evaluation_name", "Failed Evaluation"),
                    success=False,
                    metadata={"error": str(e)},
                )
                suite.add_evaluation(failed_result)

        return suite


def create_evaluator(evaluator_type: str = "default", **config) -> Evaluator:
    """Create an evaluator instance.

    Args:
        evaluator_type: Type of evaluator to create
        **config: Evaluator configuration

    Returns:
        Evaluator instance

    Raises:
        ValueError: If evaluator type is not recognized
    """
    if evaluator_type == "default" or evaluator_type == "base":
        return BaseEvaluator(**config)
    elif evaluator_type == "agent":
        from .agent import AgentEvaluator

        return AgentEvaluator(**config)
    elif evaluator_type == "topology":
        from .topology import TopologyEvaluator

        return TopologyEvaluator(**config)
    elif evaluator_type == "response":
        from .response import ResponseEvaluator

        return ResponseEvaluator(**config)
    elif evaluator_type == "benchmark":
        from .benchmark import BenchmarkEvaluator

        return BenchmarkEvaluator(**config)
    else:
        # Check for registered evaluator plugins
        try:
            from pepperpy.plugin.registry import plugin_registry

            plugins = plugin_registry.get_plugins(
                plugin_type="evaluation", category="evaluator"
            )

            for plugin in plugins:
                if plugin.provider_name == evaluator_type:
                    return plugin.get_provider(**config)
        except (ImportError, AttributeError):
            pass

        raise ValueError(f"Unknown evaluator type: {evaluator_type}")
