"""
Response evaluator for PepperPy.

This module provides evaluators for measuring the quality of responses.
"""

import re
from datetime import datetime
from typing import Any

from .base import BaseEvaluator, EvaluationMetric, EvaluationResult


class ResponseEvaluator(BaseEvaluator):
    """Evaluator for response quality."""

    def __init__(self, **kwargs):
        """Initialize response evaluator.

        Args:
            **kwargs: Configuration options including:
                - metrics: List of metrics to include in evaluation
                - evaluation_llm: Configuration for the evaluation LLM
                - criteria: Custom evaluation criteria
        """
        super().__init__(**kwargs)

        self.metrics = kwargs.get(
            "metrics",
            [
                "relevance",
                "accuracy",
                "coherence",
                "completeness",
                "conciseness",
                "hallucination",
            ],
        )

        self.eval_llm_config = kwargs.get(
            "evaluation_llm", {"provider": "openai", "model": "gpt-4"}
        )

        self.eval_llm = None

        # Custom evaluation criteria
        self.criteria = kwargs.get("criteria", {})
        self.criteria_weights = kwargs.get("criteria_weights", {})

        # Evaluation prompts
        self.evaluation_prompts = kwargs.get("evaluation_prompts", {})

    async def initialize(self) -> None:
        """Initialize the evaluator."""
        if self.initialized:
            return

        await super().initialize()

        # Initialize evaluation LLM
        if not self.eval_llm:
            from pepperpy.llm import create_provider

            provider = self.eval_llm_config.get("provider", "openai")
            model = self.eval_llm_config.get("model", "gpt-4")

            self.eval_llm = create_provider(
                provider, model=model, **self.eval_llm_config.get("config", {})
            )

            await self.eval_llm.initialize()
            self.logger.debug(f"Initialized evaluation LLM: {provider}/{model}")

    async def cleanup(self) -> None:
        """Clean up resources."""
        if not self.initialized:
            return

        # Clean up evaluation LLM
        if self.eval_llm:
            await self.eval_llm.cleanup()
            self.eval_llm = None

        await super().cleanup()

    async def evaluate(self, input_data: dict[str, Any]) -> EvaluationResult:
        """Evaluate response quality.

        Args:
            input_data: Input data including:
                - prompt: Original prompt/question
                - response: Response to evaluate
                - reference: Optional reference/ground truth
                - evaluation_name: Name for this evaluation
                - metrics: Optional metrics to evaluate
                - criteria: Optional custom criteria

        Returns:
            Evaluation result with metrics
        """
        if not self.initialized:
            await self.initialize()

        eval_name = input_data.get("evaluation_name", "Response Evaluation")
        prompt = input_data.get("prompt", "")
        response = input_data.get("response", "")
        reference = input_data.get("reference", "")
        metrics = input_data.get("metrics", self.metrics)
        criteria = input_data.get("criteria", self.criteria)

        # Create evaluation result
        result = EvaluationResult(
            name=eval_name,
            metadata={
                "prompt_length": len(prompt),
                "response_length": len(response),
                "timestamp": datetime.now().isoformat(),
            },
        )

        # Save raw data
        result.raw_data = {
            "prompt": prompt,
            "response": response,
            "reference": reference,
        }

        try:
            # Evaluate standard metrics if specified
            for metric in metrics:
                if metric == "relevance":
                    score = await self._evaluate_relevance(prompt, response)
                    result.add_metric(
                        EvaluationMetric(
                            name="relevance",
                            value=score,
                            description="How relevant the response is to the prompt",
                            category="quality",
                            weight=self.criteria_weights.get("relevance", 1.0),
                        )
                    )

                elif metric == "accuracy" and reference:
                    score = await self._evaluate_accuracy(response, reference)
                    result.add_metric(
                        EvaluationMetric(
                            name="accuracy",
                            value=score,
                            description="Factual accuracy compared to reference",
                            category="accuracy",
                            weight=self.criteria_weights.get("accuracy", 1.5),
                        )
                    )

                elif metric == "coherence":
                    score = await self._evaluate_coherence(response)
                    result.add_metric(
                        EvaluationMetric(
                            name="coherence",
                            value=score,
                            description="Logical flow and clarity of response",
                            category="quality",
                            weight=self.criteria_weights.get("coherence", 1.0),
                        )
                    )

                elif metric == "completeness":
                    score = await self._evaluate_completeness(
                        prompt, response, reference
                    )
                    result.add_metric(
                        EvaluationMetric(
                            name="completeness",
                            value=score,
                            description="How completely the response addresses the prompt",
                            category="quality",
                            weight=self.criteria_weights.get("completeness", 1.0),
                        )
                    )

                elif metric == "conciseness":
                    score = await self._evaluate_conciseness(prompt, response)
                    result.add_metric(
                        EvaluationMetric(
                            name="conciseness",
                            value=score,
                            description="How concise and to-the-point the response is",
                            category="quality",
                            weight=self.criteria_weights.get("conciseness", 0.7),
                        )
                    )

                elif metric == "hallucination" and reference:
                    score = await self._evaluate_hallucination(response, reference)
                    result.add_metric(
                        EvaluationMetric(
                            name="hallucination",
                            value=score,
                            description="Presence of made-up or incorrect information",
                            category="accuracy",
                            weight=self.criteria_weights.get("hallucination", 2.0),
                        )
                    )

            # Evaluate custom criteria
            for criterion, description in criteria.items():
                if (
                    criterion not in metrics
                ):  # Skip if already evaluated as standard metric
                    score = await self._evaluate_custom_criterion(
                        prompt, response, reference, criterion, description
                    )
                    result.add_metric(
                        EvaluationMetric(
                            name=criterion,
                            value=score,
                            description=description,
                            category="custom",
                            weight=self.criteria_weights.get(criterion, 1.0),
                        )
                    )

            # Calculate overall score
            result.calculate_score()

        except Exception as e:
            self.logger.error(f"Error during response evaluation: {e}")
            result.success = False
            result.metadata["error"] = str(e)

        return result

    async def _evaluate_relevance(self, prompt: str, response: str) -> float:
        """Evaluate relevance of the response to the prompt.

        Args:
            prompt: Original prompt
            response: Response to evaluate

        Returns:
            Relevance score (0.0 to 1.0)
        """
        if not self.eval_llm:
            return 0.5

        # Use custom prompt if available
        eval_prompt = self.evaluation_prompts.get("relevance")
        if not eval_prompt:
            eval_prompt = f"""
            Evaluate the relevance of the following response to the given prompt.
            
            Prompt:
            {prompt}
            
            Response:
            {response}
            
            On a scale of 0.0 to 1.0, how relevant is this response to the prompt?
            Consider whether the response directly addresses what was asked and stays on topic.
            
            Provide only a numeric score without explanation.
            """

        score_text = await self.eval_llm.generate_text(eval_prompt)
        return self._extract_score(score_text)

    async def _evaluate_accuracy(self, response: str, reference: str) -> float:
        """Evaluate factual accuracy of the response against a reference.

        Args:
            response: Response to evaluate
            reference: Reference/ground truth

        Returns:
            Accuracy score (0.0 to 1.0)
        """
        if not self.eval_llm:
            return 0.5

        # Use custom prompt if available
        eval_prompt = self.evaluation_prompts.get("accuracy")
        if not eval_prompt:
            eval_prompt = f"""
            Evaluate the factual accuracy of the following response against the reference information.
            
            Reference Information:
            {reference}
            
            Response to Evaluate:
            {response}
            
            On a scale of 0.0 to 1.0, how factually accurate is this response compared to the reference?
            Consider whether the facts, data, and information in the response match the reference.
            
            Provide only a numeric score without explanation.
            """

        score_text = await self.eval_llm.generate_text(eval_prompt)
        return self._extract_score(score_text)

    async def _evaluate_coherence(self, response: str) -> float:
        """Evaluate logical coherence and clarity of the response.

        Args:
            response: Response to evaluate

        Returns:
            Coherence score (0.0 to 1.0)
        """
        if not self.eval_llm:
            return 0.5

        # Use custom prompt if available
        eval_prompt = self.evaluation_prompts.get("coherence")
        if not eval_prompt:
            eval_prompt = f"""
            Evaluate the coherence and clarity of the following response.
            
            Response:
            {response}
            
            On a scale of 0.0 to 1.0, how coherent, well-structured, and clear is this response?
            Consider logical flow, organization, and readability.
            
            Provide only a numeric score without explanation.
            """

        score_text = await self.eval_llm.generate_text(eval_prompt)
        return self._extract_score(score_text)

    async def _evaluate_completeness(
        self, prompt: str, response: str, reference: str = ""
    ) -> float:
        """Evaluate completeness of the response in addressing the prompt.

        Args:
            prompt: Original prompt
            response: Response to evaluate
            reference: Optional reference for completeness comparison

        Returns:
            Completeness score (0.0 to 1.0)
        """
        if not self.eval_llm:
            return 0.5

        # Use custom prompt if available
        eval_prompt = self.evaluation_prompts.get("completeness")
        if not eval_prompt:
            if reference:
                eval_prompt = f"""
                Evaluate how completely the following response addresses the prompt compared to the reference.
                
                Prompt:
                {prompt}
                
                Reference Information:
                {reference}
                
                Response to Evaluate:
                {response}
                
                On a scale of 0.0 to 1.0, how completely does this response address all aspects of the prompt?
                Consider whether all parts of the question are answered and if important information is missing.
                
                Provide only a numeric score without explanation.
                """
            else:
                eval_prompt = f"""
                Evaluate how completely the following response addresses the prompt.
                
                Prompt:
                {prompt}
                
                Response:
                {response}
                
                On a scale of 0.0 to 1.0, how completely does this response address all aspects of the prompt?
                Consider whether all parts of the question are answered and if important information is missing.
                
                Provide only a numeric score without explanation.
                """

        score_text = await self.eval_llm.generate_text(eval_prompt)
        return self._extract_score(score_text)

    async def _evaluate_conciseness(self, prompt: str, response: str) -> float:
        """Evaluate conciseness and brevity of the response.

        Args:
            prompt: Original prompt
            response: Response to evaluate

        Returns:
            Conciseness score (0.0 to 1.0)
        """
        if not self.eval_llm:
            return 0.5

        # Use custom prompt if available
        eval_prompt = self.evaluation_prompts.get("conciseness")
        if not eval_prompt:
            eval_prompt = f"""
            Evaluate the conciseness of the following response.
            
            Prompt:
            {prompt}
            
            Response:
            {response}
            
            On a scale of 0.0 to 1.0, how concise and to-the-point is this response?
            Consider whether the response is appropriately brief while still addressing the prompt,
            without unnecessary verbosity or redundant information.
            
            Provide only a numeric score without explanation.
            """

        score_text = await self.eval_llm.generate_text(eval_prompt)
        return self._extract_score(score_text)

    async def _evaluate_hallucination(self, response: str, reference: str) -> float:
        """Evaluate presence of hallucination (made-up information) in the response.

        Args:
            response: Response to evaluate
            reference: Reference/ground truth

        Returns:
            Hallucination score (0.0 to 1.0, where 0.0 is no hallucination)
        """
        if not self.eval_llm:
            return 0.0

        # Use custom prompt if available
        eval_prompt = self.evaluation_prompts.get("hallucination")
        if not eval_prompt:
            eval_prompt = f"""
            Evaluate hallucination in the following response compared to the reference information.
            
            Reference Information:
            {reference}
            
            Response to Evaluate:
            {response}
            
            On a scale of 0.0 to 1.0, how much hallucination (made-up or incorrect information) does this response contain?
            0.0 = No hallucination at all, completely factual
            1.0 = Severe hallucination, mostly made-up information
            
            Provide only a numeric score without explanation.
            """

        score_text = await self.eval_llm.generate_text(eval_prompt)
        return self._extract_score(score_text)

    async def _evaluate_custom_criterion(
        self,
        prompt: str,
        response: str,
        reference: str,
        criterion: str,
        description: str,
    ) -> float:
        """Evaluate a custom criterion.

        Args:
            prompt: Original prompt
            response: Response to evaluate
            reference: Optional reference/ground truth
            criterion: Name of the criterion
            description: Description of the criterion

        Returns:
            Score for the criterion (0.0 to 1.0)
        """
        if not self.eval_llm:
            return 0.5

        # Check for custom prompt
        eval_prompt = self.evaluation_prompts.get(criterion)
        if not eval_prompt:
            # Build a generic evaluation prompt
            eval_prompt = f"""
            Evaluate the following response based on this criterion: {criterion} - {description}
            
            Prompt:
            {prompt}
            
            """

            if reference:
                eval_prompt += f"""
                Reference Information:
                {reference}
                
                """

            eval_prompt += f"""
            Response to Evaluate:
            {response}
            
            On a scale of 0.0 to 1.0, how well does this response meet the criterion of "{criterion}"?
            Consider the following description of this criterion: {description}
            
            Provide only a numeric score without explanation.
            """

        score_text = await self.eval_llm.generate_text(eval_prompt)
        return self._extract_score(score_text)

    def _extract_score(self, text: str) -> float:
        """Extract a numeric score from evaluation text.

        Args:
            text: Text containing a score

        Returns:
            Extracted score (0.0 to 1.0)
        """
        # Try to extract a score between 0 and 1
        match = re.search(r"(\d+\.\d+|\d+)", text)
        if match:
            score = float(match.group(1))
            return max(0.0, min(1.0, score))

        # Fallback to middle value if no score found
        return 0.5
