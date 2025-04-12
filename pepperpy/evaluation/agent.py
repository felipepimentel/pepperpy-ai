"""
Agent evaluator for PepperPy.

This module provides evaluators for measuring agent performance.
"""

from typing import Any, Dict, List, Optional, Set, Tuple
import time
import statistics
from datetime import datetime

from pepperpy.agent.base import BaseAgentProvider
from .base import BaseEvaluator, EvaluationMetric, EvaluationResult


class AgentEvaluator(BaseEvaluator):
    """Evaluator for agent performance."""
    
    def __init__(self, **kwargs):
        """Initialize agent evaluator.
        
        Args:
            **kwargs: Configuration options including:
                - metrics: List of metrics to include in evaluation
                - reference_agent: Optional reference agent to compare against
        """
        super().__init__(**kwargs)
        
        self.metrics = kwargs.get("metrics", [
            "response_quality",
            "response_time",
            "accuracy",
            "completeness",
            "hallucination"
        ])
        
        self.reference_agent = kwargs.get("reference_agent")
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
        """Evaluate agent performance.
        
        Args:
            input_data: Input data including:
                - agent: Agent to evaluate or agent_id/config to create one
                - tasks: List of tasks to evaluate
                - evaluation_name: Name for this evaluation
                - ground_truth: Optional ground truth data for accuracy
                - metrics: Optional override of metrics to evaluate
                
        Returns:
            Evaluation result with metrics
        """
        if not self.initialized:
            await self.initialize()
            
        eval_name = input_data.get("evaluation_name", "Agent Evaluation")
        agent = input_data.get("agent")
        tasks = input_data.get("tasks", [])
        ground_truth = input_data.get("ground_truth", self.ground_truth)
        metrics = input_data.get("metrics", self.metrics)
        
        # Check if we need to create the agent
        if not isinstance(agent, BaseAgentProvider) and isinstance(agent, dict):
            from pepperpy.agent import create_agent
            
            agent_type = agent.get("agent_type", "assistant") 
            agent = create_agent(agent_type, **agent)
            
            # Initialize the agent
            await agent.initialize()
            cleanup_agent = True
        else:
            cleanup_agent = False
            
        # Create evaluation result
        result = EvaluationResult(
            name=eval_name,
            metadata={
                "agent_type": agent.__class__.__name__,
                "task_count": len(tasks),
                "timestamp": datetime.now().isoformat()
            }
        )
        
        # Track metrics for each task
        response_times = []
        response_qualities = []
        accuracies = []
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
                response = await agent.process_message(task_input)
                end_time = time.time()
                response_time = end_time - start_time
                
                # Record response time
                response_times.append(response_time)
                
                # Store task result
                task_result = {
                    "task_name": task_name,
                    "input": task_input,
                    "response": response,
                    "response_time": response_time
                }
                
                # Evaluate accuracy if ground truth available
                if expected_output:
                    accuracy = await self._calculate_accuracy(
                        response, expected_output, task_name
                    )
                    accuracies.append(accuracy)
                    task_result["accuracy"] = accuracy
                    
                # Evaluate response quality if judge enabled
                if self.judge_llm and "response_quality" in metrics:
                    quality = await self._evaluate_response_quality(
                        task_input, response, task_name
                    )
                    response_qualities.append(quality)
                    task_result["quality"] = quality
                    
                # Check for hallucinations if enabled
                if "hallucination" in metrics and expected_output:
                    hallucination_score = await self._evaluate_hallucination(
                        response, task_input, expected_output
                    )
                    task_result["hallucination"] = hallucination_score
                
                task_results.append(task_result)
                
            # Create metrics from collected data
            if response_times:
                result.add_metric(EvaluationMetric(
                    name="avg_response_time",
                    value=statistics.mean(response_times),
                    description="Average response time in seconds",
                    category="performance"
                ))
                
                result.add_metric(EvaluationMetric(
                    name="max_response_time",
                    value=max(response_times),
                    description="Maximum response time in seconds",
                    category="performance"
                ))
                
            if response_qualities:
                result.add_metric(EvaluationMetric(
                    name="avg_response_quality",
                    value=statistics.mean(response_qualities),
                    description="Average response quality (0-10)",
                    category="quality",
                    weight=2.0  # Give more weight to quality
                ))
                
            if accuracies:
                result.add_metric(EvaluationMetric(
                    name="avg_accuracy",
                    value=statistics.mean(accuracies),
                    description="Average response accuracy",
                    category="accuracy",
                    weight=3.0  # Give more weight to accuracy
                ))
                
            # Save raw data
            result.raw_data = {
                "task_results": task_results,
                "agent_config": input_data.get("agent")
            }
            
            # Calculate overall score
            result.calculate_score()
            
        except Exception as e:
            self.logger.error(f"Error during agent evaluation: {e}")
            result.success = False
            result.metadata["error"] = str(e)
            
        finally:
            # Clean up agent if we created it
            if cleanup_agent:
                try:
                    await agent.cleanup()
                except Exception as e:
                    self.logger.error(f"Error cleaning up agent: {e}")
            
        return result
    
    async def _calculate_accuracy(self, response: str, expected: Any, task_name: str) -> float:
        """Calculate accuracy of response compared to expected output.
        
        Args:
            response: Agent response
            expected: Expected output
            task_name: Name of the task
            
        Returns:
            Accuracy score (0.0 to 1.0)
        """
        # If judge LLM is available, use it for accuracy
        if self.judge_llm:
            return await self._judge_accuracy(response, expected, task_name)
            
        # Basic string comparison (fallback)
        if isinstance(expected, str) and isinstance(response, str):
            from difflib import SequenceMatcher
            
            # Use sequence matcher to get a similarity ratio
            similarity = SequenceMatcher(None, response.lower(), expected.lower()).ratio()
            return similarity
            
        # For non-string comparisons, use exact match (0 or 1)
        return 1.0 if response == expected else 0.0
        
    async def _judge_accuracy(self, 
                             response: str, 
                             expected: Any, 
                             task_name: str) -> float:
        """Use judge LLM to evaluate response accuracy.
        
        Args:
            response: Agent response
            expected: Expected output
            task_name: Name of the task
            
        Returns:
            Accuracy score (0.0 to 1.0)
        """
        if not self.judge_llm:
            return 0.0
            
        # Convert expected to string if needed
        expected_str = expected if isinstance(expected, str) else str(expected)
        
        prompt = f"""
        Task: {task_name}
        
        Expected Answer:
        {expected_str}
        
        Actual Response:
        {response}
        
        On a scale of 0.0 to 1.0, how accurately does the response match the expected answer?
        Consider both factual accuracy and completeness. Provide only a numeric score without explanation.
        """
        
        try:
            score_text = await self.judge_llm.generate_text(prompt)
            # Extract numeric score
            import re
            match = re.search(r"(\d+\.\d+|\d+)", score_text)
            if match:
                score = float(match.group(1))
                # Ensure score is in range 0-1
                return max(0.0, min(1.0, score))
            return 0.5  # Default to middle if parsing fails
        except Exception as e:
            self.logger.error(f"Error in judge_accuracy: {e}")
            return 0.5  # Default to middle on error
    
    async def _evaluate_response_quality(self, 
                                        prompt: str, 
                                        response: str, 
                                        task_name: str) -> float:
        """Evaluate the quality of a response using a judge LLM.
        
        Args:
            prompt: Original prompt/task
            response: Agent response
            task_name: Name of the task
            
        Returns:
            Quality score (0.0 to 1.0)
        """
        if not self.judge_llm:
            return 0.5  # Default to middle when no judge available
            
        quality_prompt = f"""
        Task: {task_name}
        
        Original Prompt:
        {prompt}
        
        Response:
        {response}
        
        Evaluate the quality of this response on a scale of 0.0 to 1.0. Consider:
        - Helpfulness and relevance to the prompt
        - Clarity and coherence
        - Correctness of information (if applicable)
        - Completeness
        
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
            self.logger.error(f"Error in evaluate_response_quality: {e}")
            return 0.5  # Default to middle on error
            
    async def _evaluate_hallucination(self, 
                                     response: str, 
                                     prompt: str, 
                                     ground_truth: str) -> float:
        """Evaluate hallucination in response.
        
        Args:
            response: Agent response
            prompt: Original prompt
            ground_truth: Ground truth for comparison
            
        Returns:
            Hallucination score (0.0 = no hallucination, 1.0 = complete hallucination)
        """
        if not self.judge_llm:
            return 0.0  # Cannot evaluate without judge
            
        hallucination_prompt = f"""
        Original Prompt:
        {prompt}
        
        Ground Truth Information:
        {ground_truth}
        
        Response to Evaluate:
        {response}
        
        On a scale of 0.0 to 1.0, how much hallucination (made-up or incorrect information) 
        does the response contain compared to the ground truth?
        
        0.0 = No hallucination, perfectly factual
        1.0 = Complete hallucination, entirely made-up
        
        Provide only a numeric score without explanation.
        """
        
        try:
            score_text = await self.judge_llm.generate_text(hallucination_prompt)
            # Extract numeric score
            import re
            match = re.search(r"(\d+\.\d+|\d+)", score_text)
            if match:
                score = float(match.group(1))
                # Ensure score is in range 0-1
                return max(0.0, min(1.0, score))
            return 0.0  # Default to no hallucination if parsing fails
        except Exception as e:
            self.logger.error(f"Error in evaluate_hallucination: {e}")
            return 0.0  # Default on error 