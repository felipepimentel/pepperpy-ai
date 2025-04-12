"""
Topology evaluator for PepperPy.

This module provides evaluators for measuring topology performance.
"""

from typing import Any, Dict, List, Optional, Union
import time
import statistics
import asyncio
from datetime import datetime

from pepperpy.agent.topology.base import AgentTopologyProvider
from .base import BaseEvaluator, EvaluationMetric, EvaluationResult


class TopologyEvaluator(BaseEvaluator):
    """Evaluator for topology performance."""
    
    def __init__(self, **kwargs):
        """Initialize topology evaluator.
        
        Args:
            **kwargs: Configuration options including:
                - metrics: List of metrics to include in evaluation
                - reference_topology: Optional reference topology to compare against
        """
        super().__init__(**kwargs)
        
        self.metrics = kwargs.get("metrics", [
            "execution_time",
            "task_success_rate",
            "agent_utilization",
            "resource_efficiency",
            "result_quality"
        ])
        
        self.reference_topology = kwargs.get("reference_topology")
        self.ground_truth = kwargs.get("ground_truth", {})
        
        # LLM-as-judge configuration
        self.judge_config = kwargs.get("judge_config", {})
        self.judge_llm = None
        
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
                judge_type,
                model=judge_model,
                **self.judge_config.get("config", {})
            )
            
            await self.judge_llm.initialize()
            self.logger.debug(f"Initialized judge LLM: {judge_type}/{judge_model}")
        
    async def cleanup(self) -> None:
        """Clean up resources."""
        if not self.initialized:
            return
            
        # Clean up judge LLM if present
        if self.judge_llm:
            await self.judge_llm.cleanup()
            self.judge_llm = None
            
        await super().cleanup()
            
    async def evaluate(self, input_data: Dict[str, Any]) -> EvaluationResult:
        """Evaluate topology performance.
        
        Args:
            input_data: Input data including:
                - topology: Topology to evaluate or config to create one
                - tasks: List of tasks to evaluate
                - evaluation_name: Name for this evaluation
                - ground_truth: Optional ground truth data for accuracy
                - metrics: Optional override of metrics to evaluate
                - pepperpy_instance: Optional PepperPy instance with topology
                
        Returns:
            Evaluation result with metrics
        """
        if not self.initialized:
            await self.initialize()
            
        eval_name = input_data.get("evaluation_name", "Topology Evaluation")
        topology = input_data.get("topology")
        pepperpy_instance = input_data.get("pepperpy_instance")
        tasks = input_data.get("tasks", [])
        ground_truth = input_data.get("ground_truth", self.ground_truth)
        metrics = input_data.get("metrics", self.metrics)
        
        # Determine how to get the topology
        if pepperpy_instance:
            # Get topology from PepperPy instance
            topology = pepperpy_instance.topology
            cleanup_topology = False
        elif not isinstance(topology, AgentTopologyProvider) and isinstance(topology, dict):
            # Create topology from config
            from pepperpy.agent.topology.base import create_topology
            
            topology_type = topology.get("topology_type", "orchestrator")
            topology = create_topology(topology_type, **topology)
            
            # Initialize the topology
            await topology.initialize()
            cleanup_topology = True
        else:
            # Direct topology instance provided
            cleanup_topology = False
            
        # Create evaluation result
        result = EvaluationResult(
            name=eval_name,
            metadata={
                "topology_type": topology.__class__.__name__,
                "task_count": len(tasks),
                "timestamp": datetime.now().isoformat()
            }
        )
        
        # Track metrics for each task
        execution_times = []
        result_qualities = []
        task_success = []
        agent_utilization_data = []
        task_results = []
        
        # Process each task
        try:
            for i, task in enumerate(tasks):
                # Get task details
                task_input = task.get("input")
                task_name = task.get("name", f"Task {i+1}")
                expected_output = task.get("expected_output")
                
                # Execute task and time it
                start_time = time.time()
                response = await topology.execute(task_input)
                end_time = time.time()
                execution_time = end_time - start_time
                
                # Record execution time
                execution_times.append(execution_time)
                
                # Determine success
                success = response.get("status") == "success"
                task_success.append(1.0 if success else 0.0)
                
                # Store task result
                task_result = {
                    "task_name": task_name,
                    "input": task_input,
                    "response": response,
                    "execution_time": execution_time,
                    "success": success
                }
                
                # Gather agent utilization if available
                if hasattr(topology, "get_agent_utilization"):
                    utilization = await topology.get_agent_utilization()
                    agent_utilization_data.append(utilization)
                    task_result["agent_utilization"] = utilization
                
                # Evaluate result quality if judge enabled
                if self.judge_llm and "result_quality" in metrics:
                    quality = await self._evaluate_result_quality(
                        task_input, response, expected_output, task_name
                    )
                    result_qualities.append(quality)
                    task_result["quality"] = quality
                
                task_results.append(task_result)
                
            # Create metrics from collected data
            if execution_times:
                result.add_metric(EvaluationMetric(
                    name="avg_execution_time",
                    value=statistics.mean(execution_times),
                    description="Average execution time in seconds",
                    category="performance"
                ))
                
                result.add_metric(EvaluationMetric(
                    name="max_execution_time",
                    value=max(execution_times),
                    description="Maximum execution time in seconds",
                    category="performance"
                ))
                
            if task_success:
                result.add_metric(EvaluationMetric(
                    name="task_success_rate",
                    value=statistics.mean(task_success) * 100,  # Convert to percentage
                    description="Percentage of tasks successfully completed",
                    category="reliability",
                    weight=2.0  # Give more weight to success rate
                ))
                
            if result_qualities:
                result.add_metric(EvaluationMetric(
                    name="avg_result_quality",
                    value=statistics.mean(result_qualities),
                    description="Average result quality (0-1)",
                    category="quality",
                    weight=2.0  # Give more weight to quality
                ))
                
            # Calculate agent utilization if available
            if agent_utilization_data:
                # Aggregate utilization across all tasks
                all_agents = set()
                for utilization in agent_utilization_data:
                    all_agents.update(utilization.keys())
                    
                # Calculate average utilization for each agent
                avg_utilization = {}
                for agent_id in all_agents:
                    values = [u.get(agent_id, 0) for u in agent_utilization_data if agent_id in u]
                    if values:
                        avg_utilization[agent_id] = statistics.mean(values)
                        
                # Overall average utilization
                if avg_utilization:
                    avg_overall = statistics.mean(avg_utilization.values())
                    result.add_metric(EvaluationMetric(
                        name="avg_agent_utilization",
                        value=avg_overall * 100,  # Convert to percentage
                        description="Average agent utilization percentage",
                        category="efficiency"
                    ))
                    
                    # Store detailed utilization
                    result.metadata["agent_utilization"] = avg_utilization
            
            # Add topology-specific metrics if available
            await self._add_topology_specific_metrics(topology, result)
                    
            # Save raw data
            result.raw_data = {
                "task_results": task_results,
                "topology_config": input_data.get("topology")
            }
            
            # Calculate overall score
            result.calculate_score()
            
        except Exception as e:
            self.logger.error(f"Error during topology evaluation: {e}")
            result.success = False
            result.metadata["error"] = str(e)
            
        finally:
            # Clean up topology if we created it
            if cleanup_topology:
                try:
                    await topology.cleanup()
                except Exception as e:
                    self.logger.error(f"Error cleaning up topology: {e}")
            
        return result
    
    async def _evaluate_result_quality(self, 
                                     task_input: Dict[str, Any], 
                                     response: Dict[str, Any],
                                     expected_output: Any,
                                     task_name: str) -> float:
        """Evaluate the quality of a topology result using a judge LLM.
        
        Args:
            task_input: Original task input
            response: Topology response
            expected_output: Expected output if available
            task_name: Name of the task
            
        Returns:
            Quality score (0.0 to 1.0)
        """
        if not self.judge_llm:
            return 0.5  # Default to middle when no judge available
            
        # Extract result from response
        result_text = ""
        if isinstance(response, dict):
            if "result" in response:
                result_text = str(response["result"])
            elif "response" in response:
                result_text = str(response["response"])
            else:
                # Use the entire response
                result_text = str(response)
        else:
            result_text = str(response)
            
        # Get task content
        task_text = ""
        if isinstance(task_input, dict):
            if "task" in task_input:
                task_text = str(task_input["task"])
            else:
                # Use the entire input
                task_text = str(task_input)
        else:
            task_text = str(task_input)
            
        # Construct quality evaluation prompt
        if expected_output:
            quality_prompt = f"""
            Task: {task_name}
            
            Original Task:
            {task_text}
            
            Expected Output:
            {expected_output}
            
            Actual Result:
            {result_text}
            
            Evaluate the quality of this result on a scale of 0.0 to 1.0. Consider:
            - Accuracy compared to expected output
            - Completeness of the solution
            - Clarity and coherence
            - Appropriate level of detail
            
            Provide only a numeric score without explanation.
            """
        else:
            quality_prompt = f"""
            Task: {task_name}
            
            Original Task:
            {task_text}
            
            Result:
            {result_text}
            
            Evaluate the quality of this result on a scale of 0.0 to 1.0. Consider:
            - Helpfulness and relevance to the task
            - Completeness of the solution
            - Clarity and coherence
            - Appropriate level of detail
            
            Provide only a numeric score without explanation.
            """
        
        try:
            score_text = await self.judge_llm.generate_text(quality_prompt)
            # Extract numeric score
            import re
            match = re.search(r"(\d+\.\d+|\d+)", score_text)
            if match:
                score = float(match.group(1))
                # Ensure score is in range 0-1
                return max(0.0, min(1.0, score))
            return 0.5  # Default to middle if parsing fails
        except Exception as e:
            self.logger.error(f"Error in evaluate_result_quality: {e}")
            return 0.5  # Default to middle on error
            
    async def _add_topology_specific_metrics(self, 
                                           topology: AgentTopologyProvider, 
                                           result: EvaluationResult) -> None:
        """Add topology-specific metrics based on topology type.
        
        Args:
            topology: The topology being evaluated
            result: Evaluation result to add metrics to
        """
        topology_type = topology.__class__.__name__
        
        # MCP Topology specific metrics
        if "MCPTopology" in topology_type:
            if hasattr(topology, "get_system_stats"):
                try:
                    stats = await topology.get_system_stats()
                    
                    # Add resource utilization metrics
                    if "resource_utilization" in stats:
                        result.add_metric(EvaluationMetric(
                            name="resource_utilization",
                            value=stats["resource_utilization"] * 100,  # Convert to percentage
                            description="Resource utilization percentage",
                            category="efficiency"
                        ))
                        
                    # Add task throughput metrics
                    if "tasks_completed" in stats and "total_execution_time" in stats:
                        time_in_seconds = stats["total_execution_time"]
                        if time_in_seconds > 0:
                            throughput = stats["tasks_completed"] / time_in_seconds
                            result.add_metric(EvaluationMetric(
                                name="task_throughput",
                                value=throughput,
                                description="Tasks completed per second",
                                category="performance"
                            ))
                            
                    # Add priority handling metrics if available
                    if "priority_metrics" in stats:
                        priority_metrics = stats["priority_metrics"]
                        if "priority_correlation" in priority_metrics:
                            result.add_metric(EvaluationMetric(
                                name="priority_handling",
                                value=priority_metrics["priority_correlation"],
                                description="Correlation between priority and execution order",
                                category="fairness"
                            ))
                except Exception as e:
                    self.logger.error(f"Error getting MCP system stats: {e}")
                    
        # Observer Topology specific metrics
        elif "ObserverTopology" in topology_type:
            if hasattr(topology, "get_observation_stats"):
                try:
                    stats = await topology.get_observation_stats()
                    
                    # Add intervention metrics
                    if "interventions" in stats:
                        result.add_metric(EvaluationMetric(
                            name="intervention_rate",
                            value=stats["interventions"]["rate"] * 100,  # Convert to percentage
                            description="Percentage of actions that triggered interventions",
                            category="oversight"
                        ))
                        
                    # Add observation coverage
                    if "observation_coverage" in stats:
                        result.add_metric(EvaluationMetric(
                            name="observation_coverage",
                            value=stats["observation_coverage"] * 100,  # Convert to percentage
                            description="Percentage of actions that were observed",
                            category="oversight"
                        ))
                except Exception as e:
                    self.logger.error(f"Error getting Observer stats: {e}")
                    
        # Federation Topology specific metrics
        elif "FederationTopology" in topology_type:
            if hasattr(topology, "_get_federation_status"):
                try:
                    status = await topology._get_federation_status()
                    federation_status = status.get("federation_status", {})
                    
                    # Add cross-domain metrics
                    queries = await topology.get_queries("federated_task")
                    cross_domain_count = len(queries)
                    
                    if cross_domain_count > 0:
                        # Calculate cross-domain success rate
                        success_count = sum(
                            1 for q in queries 
                            if q.get("result_status") == "success"
                        )
                        success_rate = success_count / cross_domain_count
                        
                        result.add_metric(EvaluationMetric(
                            name="cross_domain_success_rate",
                            value=success_rate * 100,  # Convert to percentage
                            description="Success rate of cross-domain communications",
                            category="federation"
                        ))
                        
                    # Add domain metrics
                    if "domain_count" in federation_status:
                        result.metadata["domain_count"] = federation_status["domain_count"]
                        
                except Exception as e:
                    self.logger.error(f"Error getting Federation stats: {e}")
                    
        # Orchestrator Topology specific metrics
        elif "OrchestratorTopology" in topology_type:
            if hasattr(topology, "iterations"):
                # Add iteration metrics
                result.add_metric(EvaluationMetric(
                    name="iteration_count",
                    value=topology.iterations,
                    description="Number of iterations performed",
                    category="convergence"
                ))
                
                # Check if max iterations was reached
                if hasattr(topology, "max_iterations"):
                    if topology.iterations >= topology.max_iterations:
                        result.add_metric(EvaluationMetric(
                            name="reached_max_iterations",
                            value=1.0,  # Boolean as float
                            description="Whether max iterations was reached",
                            category="convergence",
                            weight=0.5  # Lower weight as this is informational
                        ))
                    else:
                        result.add_metric(EvaluationMetric(
                            name="reached_max_iterations",
                            value=0.0,  # Boolean as float
                            description="Whether max iterations was reached",
                            category="convergence",
                            weight=0.5  # Lower weight as this is informational
                        ))
                        
        # Add general topology metrics
        if hasattr(topology, "agents"):
            result.metadata["agent_count"] = len(topology.agents) 