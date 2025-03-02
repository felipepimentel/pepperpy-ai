"""Module for standardized agent evaluation benchmarks."""

import asyncio
import json
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional


class BenchmarkType(Enum):
    """Types of evaluation benchmarks."""

    TASK_COMPLETION = "task_completion"
    REASONING = "reasoning"
    KNOWLEDGE = "knowledge"
    INTERACTION = "interaction"
    ROBUSTNESS = "robustness"
    SAFETY = "safety"


@dataclass
class BenchmarkCase:
    """Individual test case in a benchmark."""

    id: str
    type: BenchmarkType
    input: Any
    expected_output: Any
    constraints: Optional[Dict[str, Any]] = None
    metadata: Optional[dict] = None


@dataclass
class BenchmarkResult:
    """Result of a benchmark evaluation."""

    case_id: str
    success: bool
    output: Any
    score: float
    duration_ms: float
    error: Optional[str] = None
    metadata: Optional[dict] = None


class BaseBenchmark:
    """Base class for benchmarks."""

    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.cases: List[BenchmarkCase] = []

    def add_case(self, case: BenchmarkCase):
        """Add a test case to the benchmark."""
        self.cases.append(case)

    def load_cases_from_json(self, json_path: str):
        """Load test cases from a JSON file."""
        with open(json_path, "r") as f:
            data = json.load(f)
            for case_data in data.get("cases", []):
                case = BenchmarkCase(
                    id=case_data["id"],
                    type=BenchmarkType(case_data["type"]),
                    input=case_data["input"],
                    expected_output=case_data["expected_output"],
                    constraints=case_data.get("constraints"),
                    metadata=case_data.get("metadata"),
                )
                self.add_case(case)

    async def evaluate(self, agent: Any) -> List[BenchmarkResult]:
        """Evaluate an agent against all test cases."""
        results = []
        for case in self.cases:
            try:
                result = await self.evaluate_case(agent, case)
                results.append(result)
            except Exception as e:
                results.append(
                    BenchmarkResult(
                        case_id=case.id,
                        success=False,
                        output=None,
                        score=0.0,
                        duration_ms=0.0,
                        error=str(e),
                    )
                )
        return results

    async def evaluate_case(self, agent: Any, case: BenchmarkCase) -> BenchmarkResult:
        """Evaluate an agent against a single test case."""
        raise NotImplementedError


class TaskCompletionBenchmark(BaseBenchmark):
    """Evaluates task completion capabilities."""

    async def evaluate_case(self, agent: Any, case: BenchmarkCase) -> BenchmarkResult:
        """Evaluate task completion for a single case."""
        start_time = asyncio.get_event_loop().time()

        try:
            output = await agent.execute_task(case.input)
            success = self._check_output(output, case.expected_output)
            score = 1.0 if success else 0.0

            if case.constraints:
                # Apply penalties based on constraint violations
                penalties = self._check_constraints(output, case.constraints)
                score = max(0.0, score - sum(penalties))

        except Exception as e:
            return BenchmarkResult(
                case_id=case.id,
                success=False,
                output=None,
                score=0.0,
                duration_ms=(asyncio.get_event_loop().time() - start_time) * 1000,
                error=str(e),
            )

        return BenchmarkResult(
            case_id=case.id,
            success=success,
            output=output,
            score=score,
            duration_ms=(asyncio.get_event_loop().time() - start_time) * 1000,
        )

    def _check_output(self, output: Any, expected: Any) -> bool:
        """Check if output matches expected result."""
        if isinstance(expected, dict) and isinstance(output, dict):
            return all(k in output and output[k] == v for k, v in expected.items())
        return output == expected

    def _check_constraints(
        self, output: Any, constraints: Dict[str, Any]
    ) -> List[float]:
        """Check constraint violations and return penalties."""
        penalties = []

        if "max_time" in constraints and constraints["max_time"] < output.get(
            "time", 0
        ):
            penalties.append(0.2)

        if "required_fields" in constraints:
            missing = [f for f in constraints["required_fields"] if f not in output]
            if missing:
                penalties.append(0.1 * len(missing))

        return penalties


class ReasoningBenchmark(BaseBenchmark):
    """Evaluates reasoning and problem-solving capabilities."""

    async def evaluate_case(self, agent: Any, case: BenchmarkCase) -> BenchmarkResult:
        """Evaluate reasoning for a single case."""
        start_time = asyncio.get_event_loop().time()

        try:
            reasoning_steps = await agent.solve_problem(case.input)
            output = reasoning_steps[-1] if reasoning_steps else None

            # Evaluate both final answer and reasoning process
            answer_score = self._check_answer(output, case.expected_output)
            process_score = self._evaluate_reasoning_process(reasoning_steps)

            score = 0.7 * answer_score + 0.3 * process_score
            success = score >= 0.8  # Consider successful if score is at least 80%

        except Exception as e:
            return BenchmarkResult(
                case_id=case.id,
                success=False,
                output=None,
                score=0.0,
                duration_ms=(asyncio.get_event_loop().time() - start_time) * 1000,
                error=str(e),
            )

        return BenchmarkResult(
            case_id=case.id,
            success=success,
            output={"answer": output, "steps": reasoning_steps},
            score=score,
            duration_ms=(asyncio.get_event_loop().time() - start_time) * 1000,
        )

    def _check_answer(self, output: Any, expected: Any) -> float:
        """Check correctness of final answer."""
        if output == expected:
            return 1.0
        return 0.0

    def _evaluate_reasoning_process(self, steps: List[Any]) -> float:
        """Evaluate the quality of reasoning steps."""
        if not steps:
            return 0.0

        # Example criteria:
        # - Each step follows logically from previous steps
        # - Steps are clear and well-explained
        # - No logical fallacies
        # Implementation would depend on specific requirements

        return 1.0  # Placeholder


class BenchmarkSuite:
    """Collection of benchmarks for comprehensive evaluation."""

    def __init__(self):
        self.benchmarks: Dict[str, BaseBenchmark] = {}

    def add_benchmark(self, benchmark: BaseBenchmark):
        """Add a benchmark to the suite."""
        self.benchmarks[benchmark.name] = benchmark

    async def run_all(self, agent: Any) -> Dict[str, List[BenchmarkResult]]:
        """Run all benchmarks against an agent."""
        results = {}
        for name, benchmark in self.benchmarks.items():
            results[name] = await benchmark.evaluate(agent)
        return results

    def get_summary(self, results: Dict[str, List[BenchmarkResult]]) -> Dict[str, Any]:
        """Generate summary statistics for benchmark results."""
        summary = {
            "overall": {"total_cases": 0, "successful": 0, "average_score": 0.0},
            "benchmarks": {},
        }

        total_score = 0.0
        total_cases = 0

        for benchmark_name, benchmark_results in results.items():
            successful = sum(1 for r in benchmark_results if r.success)
            avg_score = sum(r.score for r in benchmark_results) / len(benchmark_results)

            summary["benchmarks"][benchmark_name] = {
                "total_cases": len(benchmark_results),
                "successful": successful,
                "success_rate": successful / len(benchmark_results),
                "average_score": avg_score,
                "average_duration": sum(r.duration_ms for r in benchmark_results)
                / len(benchmark_results),
            }

            total_score += avg_score * len(benchmark_results)
            total_cases += len(benchmark_results)
            summary["overall"]["successful"] += successful
            summary["overall"]["total_cases"] += len(benchmark_results)

        summary["overall"]["average_score"] = (
            total_score / total_cases if total_cases > 0 else 0.0
        )
        summary["overall"]["success_rate"] = (
            summary["overall"]["successful"] / summary["overall"]["total_cases"]
            if summary["overall"]["total_cases"] > 0
            else 0.0
        )

        return summary
