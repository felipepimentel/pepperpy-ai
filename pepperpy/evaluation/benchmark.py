"""
Benchmark evaluator for PepperPy.

This module provides standardized benchmarks for evaluating AI agents and topologies.
"""

import json
import os
import statistics
from datetime import datetime
from pathlib import Path
from typing import Any

from .base import BaseEvaluator, EvaluationMetric, EvaluationResult, EvaluationSuite


class BenchmarkEvaluator(BaseEvaluator):
    """Evaluator for running standardized benchmarks."""

    def __init__(self, **kwargs):
        """Initialize benchmark evaluator.

        Args:
            **kwargs: Configuration options including:
                - benchmarks: List of benchmark names to run
                - difficulty: Difficulty level ("easy", "medium", "hard")
                - benchmark_path: Custom path to benchmark definitions
                - judge_config: Configuration for LLM judge
        """
        super().__init__(**kwargs)

        self.benchmarks = kwargs.get(
            "benchmarks",
            [
                "question_answering",
                "reasoning",
                "code_generation",
                "creative_writing",
                "summarization",
            ],
        )

        self.difficulty = kwargs.get("difficulty", "medium")
        self.benchmark_path = kwargs.get("benchmark_path")

        # LLM-as-judge configuration
        self.judge_config = kwargs.get("judge_config", {})
        self.judge_llm = None

        # Loaded benchmark data
        self.benchmark_data = {}

    async def initialize(self) -> None:
        """Initialize the evaluator."""
        if self.initialized:
            return

        await super().initialize()

        # Set up LLM for judging if needed
        if self.judge_config and not self.judge_llm:
            from pepperpy.llm import create_provider

            judge_type = self.judge_config.get("provider", "openai")
            judge_model = self.judge_config.get("model", "gpt-4")

            self.judge_llm = create_provider(
                judge_type, model=judge_model, **self.judge_config.get("config", {})
            )

            await self.judge_llm.initialize()
            self.logger.debug(f"Initialized judge LLM: {judge_type}/{judge_model}")

        # Load benchmark data
        await self._load_benchmark_data()

    async def _load_benchmark_data(self) -> None:
        """Load benchmark data from files."""
        # Determine benchmark directory
        if self.benchmark_path:
            benchmark_dir = Path(self.benchmark_path)
        else:
            # Use default path within the package
            module_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            benchmark_dir = Path(module_dir) / "data" / "benchmarks"

            # If not found in package, try to download
            if not benchmark_dir.exists():
                # Create directory if it doesn't exist
                os.makedirs(benchmark_dir, exist_ok=True)
                await self._download_benchmark_data(benchmark_dir)

        # Load benchmark data from files
        for benchmark in self.benchmarks:
            benchmark_file = benchmark_dir / f"{benchmark}_{self.difficulty}.json"

            if benchmark_file.exists():
                with open(benchmark_file) as f:
                    self.benchmark_data[benchmark] = json.load(f)
                self.logger.debug(f"Loaded benchmark: {benchmark} ({self.difficulty})")
            else:
                self.logger.warning(f"Benchmark file not found: {benchmark_file}")

    async def _download_benchmark_data(self, benchmark_dir: Path) -> None:
        """Download benchmark data if not available locally."""
        self.logger.info("Downloading benchmark data...")

        # Basic benchmarks to generate if downloads fail
        basic_benchmarks = {
            "question_answering": [
                {
                    "name": "Basic Facts",
                    "input": "What is the capital of France?",
                    "expected_output": "The capital of France is Paris.",
                    "category": "geography",
                },
                {
                    "name": "Scientific Knowledge",
                    "input": "Explain how photosynthesis works in plants.",
                    "expected_output": "Photosynthesis is the process by which plants convert light energy into chemical energy. Plants use sunlight, water, and carbon dioxide to create oxygen and energy in the form of sugar (glucose).",
                    "category": "science",
                },
            ],
            "reasoning": [
                {
                    "name": "Logical Deduction",
                    "input": "If all cats have tails, and Fluffy is a cat, what can you conclude about Fluffy?",
                    "expected_output": "Fluffy has a tail.",
                    "category": "deduction",
                }
            ],
            "code_generation": [
                {
                    "name": "Simple Function",
                    "input": "Write a Python function to calculate the factorial of a number.",
                    "category": "python",
                }
            ],
            "creative_writing": [
                {
                    "name": "Short Story",
                    "input": "Write a short story about a robot discovering emotions.",
                    "category": "fiction",
                }
            ],
            "summarization": [
                {
                    "name": "Article Summary",
                    "input": "Summarize the following article in 2-3 sentences: [text of an article about climate change]",
                    "category": "news",
                }
            ],
        }

        # Try to download from GitHub or other source
        try:
            import requests

            base_url = "https://raw.githubusercontent.com/pepperpy/benchmarks/main"

            for benchmark in self.benchmarks:
                url = f"{base_url}/{benchmark}_{self.difficulty}.json"
                response = requests.get(url, timeout=10)

                if response.status_code == 200:
                    benchmark_file = (
                        benchmark_dir / f"{benchmark}_{self.difficulty}.json"
                    )
                    with open(benchmark_file, "w") as f:
                        f.write(response.text)
                    self.logger.debug(f"Downloaded benchmark: {benchmark}")
                # Fall back to basic benchmarks
                elif benchmark in basic_benchmarks:
                    benchmark_file = (
                        benchmark_dir / f"{benchmark}_{self.difficulty}.json"
                    )
                    with open(benchmark_file, "w") as f:
                        json.dump(basic_benchmarks[benchmark], f, indent=2)
                    self.logger.debug(f"Created basic benchmark: {benchmark}")

        except Exception as e:
            self.logger.error(f"Error downloading benchmarks: {e}")

            # Fall back to basic benchmarks
            for benchmark, tasks in basic_benchmarks.items():
                if benchmark in self.benchmarks:
                    benchmark_file = (
                        benchmark_dir / f"{benchmark}_{self.difficulty}.json"
                    )
                    with open(benchmark_file, "w") as f:
                        json.dump(tasks, f, indent=2)
                    self.logger.debug(f"Created basic benchmark: {benchmark}")

    async def cleanup(self) -> None:
        """Clean up resources."""
        if not self.initialized:
            return

        # Clean up judge LLM if present
        if self.judge_llm:
            await self.judge_llm.cleanup()
            self.judge_llm = None

        await super().cleanup()

    async def evaluate(self, input_data: dict[str, Any]) -> EvaluationResult:
        """Evaluate using benchmark tasks.

        Args:
            input_data: Input data including:
                - target: Agent or topology to evaluate
                - benchmark: Benchmark name or list of benchmarks
                - evaluation_name: Name for this evaluation
                - difficulty: Optional difficulty override

        Returns:
            Evaluation result with metrics
        """
        if not self.initialized:
            await self.initialize()

        eval_name = input_data.get("evaluation_name", "Benchmark Evaluation")
        target = input_data.get("target")
        benchmark_name = input_data.get("benchmark")
        difficulty = input_data.get("difficulty", self.difficulty)

        # If benchmark is specified, use only that one
        if benchmark_name:
            if isinstance(benchmark_name, str):
                benchmarks = [benchmark_name]
            else:
                benchmarks = benchmark_name
        else:
            benchmarks = self.benchmarks

        # Create evaluation result
        result = EvaluationResult(
            name=eval_name,
            metadata={
                "benchmark": benchmarks,
                "difficulty": difficulty,
                "timestamp": datetime.now().isoformat(),
            },
        )

        # Determine target type (agent or topology)
        from pepperpy.agent.base import BaseAgentProvider
        from pepperpy.agent.topology.base import AgentTopologyProvider

        if isinstance(target, BaseAgentProvider):
            target_type = "agent"
        elif isinstance(target, AgentTopologyProvider):
            target_type = "topology"
        else:
            # Try to determine from input_data
            target_type = input_data.get("target_type", "agent")

        try:
            # Track metrics across benchmarks
            combined_metrics = {}
            benchmark_results = {}

            # Run each benchmark
            for benchmark in benchmarks:
                if benchmark not in self.benchmark_data:
                    self.logger.warning(f"Benchmark {benchmark} not found. Skipping.")
                    continue

                benchmark_tasks = self.benchmark_data[benchmark]

                # Run the benchmark based on target type
                if target_type == "agent":
                    benchmark_result = await self._run_agent_benchmark(
                        target, benchmark, benchmark_tasks
                    )
                else:
                    benchmark_result = await self._run_topology_benchmark(
                        target, benchmark, benchmark_tasks
                    )

                # Store benchmark result
                benchmark_results[benchmark] = benchmark_result.to_dict()

                # Combine metrics from this benchmark
                for metric in benchmark_result.metrics:
                    if metric.name not in combined_metrics:
                        combined_metrics[metric.name] = []
                    combined_metrics[metric.name].append(metric.value)

            # Create aggregated metrics
            for name, values in combined_metrics.items():
                if values:
                    avg_value = statistics.mean(values)
                    result.add_metric(
                        EvaluationMetric(
                            name=f"avg_{name}",
                            value=avg_value,
                            description=f"Average {name} across all benchmarks",
                            category="benchmark",
                        )
                    )

            # Add number of completed benchmarks metric
            result.add_metric(
                EvaluationMetric(
                    name="benchmarks_completed",
                    value=len(benchmark_results),
                    description="Number of benchmarks successfully completed",
                    category="benchmark",
                )
            )

            # Store raw benchmark results
            result.raw_data = {
                "benchmark_results": benchmark_results,
                "target_type": target_type,
                "difficulty": difficulty,
            }

            # Calculate overall score
            result.calculate_score()

        except Exception as e:
            self.logger.error(f"Error during benchmark evaluation: {e}")
            result.success = False
            result.metadata["error"] = str(e)

        return result

    async def _run_agent_benchmark(
        self, agent: Any, benchmark_name: str, tasks: list[dict[str, Any]]
    ) -> EvaluationResult:
        """Run benchmark for an agent.

        Args:
            agent: Agent to evaluate
            benchmark_name: Name of the benchmark
            tasks: List of benchmark tasks

        Returns:
            Benchmark result
        """
        # Create agent evaluator
        from .agent import AgentEvaluator

        agent_evaluator = AgentEvaluator(
            name=f"{benchmark_name.capitalize()} Benchmark",
            judge_config=self.judge_config,
        )

        await agent_evaluator.initialize()

        try:
            # Prepare tasks for agent format
            agent_tasks = [
                {
                    "name": task.get("name", f"Task {i + 1}"),
                    "input": task["input"],
                    "expected_output": task.get("expected_output"),
                }
                for i, task in enumerate(tasks)
            ]

            # Run agent evaluation
            result = await agent_evaluator.evaluate({
                "evaluation_name": f"{benchmark_name.capitalize()} Benchmark",
                "agent": agent,
                "tasks": agent_tasks,
            })

            # Add benchmark-specific metadata
            result.metadata["benchmark"] = benchmark_name

        finally:
            await agent_evaluator.cleanup()

        return result

    async def _run_topology_benchmark(
        self, topology: Any, benchmark_name: str, tasks: list[dict[str, Any]]
    ) -> EvaluationResult:
        """Run benchmark for a topology.

        Args:
            topology: Topology to evaluate
            benchmark_name: Name of the benchmark
            tasks: List of benchmark tasks

        Returns:
            Benchmark result
        """
        # Create topology evaluator
        from .topology import TopologyEvaluator

        topology_evaluator = TopologyEvaluator(
            name=f"{benchmark_name.capitalize()} Benchmark",
            judge_config=self.judge_config,
        )

        await topology_evaluator.initialize()

        try:
            # Prepare tasks for topology format
            topology_tasks = [
                {
                    "name": task.get("name", f"Task {i + 1}"),
                    "input": {"task": task["input"]},
                    "expected_output": task.get("expected_output"),
                }
                for i, task in enumerate(tasks)
            ]

            # Run topology evaluation
            result = await topology_evaluator.evaluate({
                "evaluation_name": f"{benchmark_name.capitalize()} Benchmark",
                "topology": topology,
                "tasks": topology_tasks,
            })

            # Add benchmark-specific metadata
            result.metadata["benchmark"] = benchmark_name

        finally:
            await topology_evaluator.cleanup()

        return result

    async def run_suite(
        self,
        inputs: list[dict[str, Any]],
        suite_name: str = "Benchmark Suite",
        description: str = "",
    ) -> EvaluationSuite:
        """Run a suite of benchmark evaluations.

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

        # Run each evaluation
        for input_data in inputs:
            try:
                result = await self.evaluate(input_data)
                suite.add_evaluation(result)
            except Exception as e:
                self.logger.error(
                    f"Error in benchmark {input_data.get('benchmark')}: {e}"
                )
                # Add failed evaluation
                failed_result = EvaluationResult(
                    name=input_data.get("evaluation_name", "Failed Benchmark"),
                    success=False,
                    metadata={"error": str(e)},
                )
                suite.add_evaluation(failed_result)

        return suite


async def run_benchmark(
    target: Any, benchmark_name: str | None = None, difficulty: str = "medium", **kwargs
) -> EvaluationResult:
    """Run a benchmark evaluation on an agent or topology.

    Args:
        target: Agent or topology to evaluate
        benchmark_name: Name of the benchmark to run (None for all)
        difficulty: Difficulty level ("easy", "medium", "hard")
        **kwargs: Additional configuration options

    Returns:
        Benchmark evaluation result
    """
    # Create benchmark evaluator
    evaluator = BenchmarkEvaluator(difficulty=difficulty, **kwargs)

    await evaluator.initialize()

    try:
        # Run evaluation
        result = await evaluator.evaluate({
            "target": target,
            "benchmark": benchmark_name,
            "difficulty": difficulty,
            "evaluation_name": kwargs.get("evaluation_name", "Benchmark Evaluation"),
        })

        return result
    finally:
        await evaluator.cleanup()


async def compare_benchmarks(
    targets: dict[str, Any],
    benchmark_name: str | None = None,
    difficulty: str = "medium",
    **kwargs,
) -> EvaluationSuite:
    """Compare multiple agents or topologies on the same benchmark.

    Args:
        targets: Dict of {name: target} to evaluate
        benchmark_name: Name of the benchmark to run (None for all)
        difficulty: Difficulty level ("easy", "medium", "hard")
        **kwargs: Additional configuration options

    Returns:
        Benchmark comparison suite
    """
    # Create benchmark evaluator
    evaluator = BenchmarkEvaluator(difficulty=difficulty, **kwargs)

    await evaluator.initialize()

    try:
        # Prepare inputs
        inputs = [
            {
                "target": target,
                "benchmark": benchmark_name,
                "difficulty": difficulty,
                "evaluation_name": name,
            }
            for name, target in targets.items()
        ]

        # Run evaluation suite
        suite = await evaluator.run_suite(
            inputs,
            suite_name=kwargs.get("suite_name", "Benchmark Comparison"),
            description=kwargs.get(
                "description", "Comparing performance on benchmarks"
            ),
        )

        return suite
    finally:
        await evaluator.cleanup()
