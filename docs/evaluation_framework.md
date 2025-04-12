# Evaluation Framework

The PepperPy Evaluation Framework provides a systematic way to measure, analyze, and compare the performance of AI agents, topologies, and responses. It enables objective assessment of AI systems across multiple dimensions.

## Key Concepts

### Metrics and Results

The framework is built around these core elements:

- **EvaluationMetric**: An individual measurement of a specific quality or performance aspect
- **EvaluationResult**: A collection of metrics for a single evaluation run
- **EvaluationSuite**: A group of evaluation results, typically comparing different configurations

### Evaluator Types

The framework includes specialized evaluators for different aspects of AI systems:

- **AgentEvaluator**: Measures performance of individual agents
- **TopologyEvaluator**: Evaluates agent topology effectiveness
- **ResponseEvaluator**: Assesses quality of specific responses
- **BenchmarkEvaluator**: Runs standardized performance tests

## Using the Framework

### Basic Usage Pattern

```python
from pepperpy.evaluation import create_evaluator

# Create an evaluator
evaluator = create_evaluator(
    "agent",  # or "topology", "response", etc.
    metrics=["accuracy", "response_time", "completeness"],
    judge_config={"provider": "openai", "model": "gpt-4"}
)

# Initialize resources
await evaluator.initialize()

try:
    # Run single evaluation
    result = await evaluator.evaluate({
        "evaluation_name": "My Test",
        "agent": agent_instance,  # or topology, response, etc.
        "tasks": [...]
    })
    
    # Or run a suite of evaluations
    suite = await evaluator.run_suite([
        {"evaluation_name": "Config 1", ...},
        {"evaluation_name": "Config 2", ...},
    ], suite_name="Comparison Suite")
    
    # Access results
    print(f"Overall score: {result.score}")
    for metric in result.metrics:
        print(f"{metric.name}: {metric.value}")
        
    # Save results
    with open("results.json", "w") as f:
        f.write(suite.to_json(pretty=True))
        
finally:
    # Clean up resources
    await evaluator.cleanup()
```

## Agent Evaluation

The `AgentEvaluator` measures performance of individual agents across various metrics.

### Available Metrics

- **response_quality**: Overall quality of agent responses (requires LLM judge)
- **response_time**: Time taken to generate responses
- **accuracy**: Correctness compared to ground truth
- **completeness**: How fully the agent addresses questions
- **hallucination**: Detection of made-up information

### Configuration

```python
evaluator = create_evaluator(
    "agent",
    name="Agent Performance Evaluator",
    metrics=["response_quality", "response_time", "accuracy"],
    judge_config={
        "provider": "openai",
        "model": "gpt-4"
    },
    ground_truth={...}  # Optional reference answers
)
```

### Evaluation Input

```python
result = await evaluator.evaluate({
    "evaluation_name": "Test Agent",
    "agent": {  # Or pass a direct agent instance
        "agent_type": "assistant",
        "system_prompt": "You are a helpful assistant..."
    },
    "tasks": [
        {
            "name": "Task 1",
            "input": "What is the capital of France?",
            "expected_output": "The capital of France is Paris."
        },
        # More tasks...
    ]
})
```

## Topology Evaluation

The `TopologyEvaluator` measures performance of agent topologies and how effectively they coordinate multiple agents.

### Available Metrics

- **execution_time**: Time taken to process tasks
- **task_success_rate**: Percentage of tasks successfully completed
- **agent_utilization**: How effectively agents are utilized
- **resource_efficiency**: Efficiency of resource usage
- **result_quality**: Quality of outputs

### Configuration

```python
evaluator = create_evaluator(
    "topology",
    name="Topology Performance Evaluator",
    metrics=["execution_time", "task_success_rate", "result_quality"],
    judge_config={
        "provider": "openai",
        "model": "gpt-4"
    }
)
```

### Evaluation Input

```python
# With PepperPy instance
result = await evaluator.evaluate({
    "evaluation_name": "Orchestrator Topology Test",
    "pepperpy_instance": pepperpy,  # With topology already configured
    "tasks": [
        {
            "name": "Research Task",
            "input": {"task": "Research renewable energy sources."}
        },
        # More tasks...
    ]
})

# Or with topology config
result = await evaluator.evaluate({
    "evaluation_name": "Mesh Topology Test",
    "topology": {
        "topology_type": "mesh",
        # Configuration...
    },
    "tasks": [...]
})
```

## Response Evaluation

The `ResponseEvaluator` evaluates the quality of specific responses without considering the agent or topology that generated them.

### Available Metrics

- **relevance**: How relevant the response is to the prompt
- **accuracy**: Factual correctness compared to reference
- **coherence**: Logical flow and clarity
- **completeness**: How fully the response addresses the prompt
- **conciseness**: Brevity and focus
- **hallucination**: Detection of made-up information

### Configuration

```python
evaluator = create_evaluator(
    "response",
    name="Response Quality Evaluator",
    metrics=["relevance", "accuracy", "coherence", "completeness"],
    criteria_weights={
        "relevance": 1.5,
        "accuracy": 2.0,
        "coherence": 1.0,
        "completeness": 1.0
    },
    evaluation_llm={
        "provider": "openai",
        "model": "gpt-4"
    }
)
```

### Evaluation Input

```python
result = await evaluator.evaluate({
    "evaluation_name": "Test Response",
    "prompt": "Explain how neural networks learn.",
    "response": "Neural networks learn through a process called backpropagation...",
    "reference": "Reference information...",  # Optional ground truth
})
```

## Custom Evaluation Criteria

You can define and use custom evaluation criteria beyond the standard metrics:

```python
evaluator = create_evaluator(
    "response",
    metrics=["relevance", "accuracy"],
    criteria={
        "technical_accuracy": "Correctness of technical information and terminology",
        "empathy": "Expression of understanding and compassion",
        "actionability": "Providing concrete, implementable actions"
    },
    criteria_weights={
        "technical_accuracy": 2.0,
        "empathy": 1.5,
        "actionability": 1.8
    },
    evaluation_prompts={
        "technical_accuracy": """
        Evaluate the technical accuracy of the following response...
        [Custom prompt for this specific criterion]
        """
    }
)
```

## LLM-as-Judge Evaluation

The framework uses an LLM-as-judge approach for subjective metrics. The judge LLM evaluates responses based on criteria and provides numerical scores.

### Judge Configuration

```python
judge_config = {
    "provider": "openai",
    "model": "gpt-4",
    "config": {
        "temperature": 0.2,  # Lower temperature for more consistent judgments
        "max_tokens": 100
    }
}
```

### Creating Custom Prompts

You can customize the evaluation prompts for each metric:

```python
evaluation_prompts = {
    "accuracy": """
    Evaluate the factual accuracy of the following response...
    [Custom prompt for accuracy evaluation]
    """,
    "relevance": """
    Evaluate how relevant this response is to the prompt...
    [Custom prompt for relevance evaluation]
    """
}
```

## Benchmark Suite

The framework includes a benchmark suite with standardized tests:

```python
from pepperpy.evaluation.benchmark import run_benchmark

benchmark_results = await run_benchmark(
    agent,  # or topology
    benchmark_name="question_answering",  # or "problem_solving", "creativity", etc.
    difficulty="medium"  # or "easy", "hard"
)
```

## Practical Example

Here's a complete example that compares different agent configurations:

```python
import asyncio
from pepperpy.evaluation import create_evaluator

async def compare_agents():
    # Create evaluator
    evaluator = create_evaluator(
        "agent",
        metrics=["response_quality", "response_time", "accuracy"],
        judge_config={"provider": "openai", "model": "gpt-4"}
    )
    
    await evaluator.initialize()
    
    # Define tasks
    tasks = [
        {
            "name": "Factual Question",
            "input": "What causes the seasons on Earth?",
            "expected_output": "Seasons are caused by Earth's tilted axis..."
        },
        # More tasks...
    ]
    
    # Define agent configurations to test
    configs = [
        {
            "evaluation_name": "General Assistant",
            "agent": {
                "agent_type": "assistant",
                "system_prompt": "You are a helpful assistant."
            },
            "tasks": tasks
        },
        {
            "evaluation_name": "Science Expert",
            "agent": {
                "agent_type": "assistant",
                "system_prompt": "You are an expert in science and astronomy."
            },
            "tasks": tasks
        }
    ]
    
    # Run the evaluation suite
    suite = await evaluator.run_suite(
        configs,
        suite_name="Agent Comparison",
        description="Comparing different agent configurations"
    )
    
    # Output and save results
    print(f"Overall average: {suite.get_average_score()}")
    for eval_result in suite.evaluations:
        print(f"{eval_result.name}: {eval_result.score}")
    
    with open("results.json", "w") as f:
        f.write(suite.to_json(pretty=True))
        
    await evaluator.cleanup()

if __name__ == "__main__":
    asyncio.run(compare_agents())
```

## See Also

Check out [examples/evaluation_framework.py](../examples/evaluation_framework.py) for complete working examples of the evaluation framework. 