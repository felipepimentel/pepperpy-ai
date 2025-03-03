"""Reasoning capability for agents.

This module provides reasoning capabilities for agents, allowing them to analyze
information, evaluate hypotheses, and generate alternatives.
"""

from pepperpy.agents.capabilities.reasoning.providers import (
    BaseReasoningProvider,
    ReasoningResult,
    ReasoningStep,
    ReasoningType,
)


class ReasoningCapability:
    """Reasoning capability for agents.

    This capability allows agents to analyze information, evaluate hypotheses,
    and generate alternatives.
    """

    def __init__(self, provider: BaseReasoningProvider):
        """Initialize the reasoning capability.

        Args:
            provider: The reasoning provider to use

        """
        self.provider = provider

    def analyze(self, context: str, question: str):
        """Analyze a context to answer a question.

        Args:
            context: The context to analyze
            question: The question to answer

        Returns:
            A reasoning result containing the analysis

        """
        return self.provider.analyze(context, question)

    def evaluate_hypothesis(self, hypothesis: str, evidence):
        """Evaluate a hypothesis against evidence.

        Args:
            hypothesis: The hypothesis to evaluate
            evidence: Evidence to consider

        Returns:
            Evaluation metrics for the hypothesis

        """
        return self.provider.evaluate_hypothesis(hypothesis, evidence)

    def generate_alternatives(self, scenario: str, constraints=None):
        """Generate alternative solutions or explanations.

        Args:
            scenario: The scenario to generate alternatives for
            constraints: Optional constraints to consider

        Returns:
            A list of alternative solutions or explanations

        """
        return self.provider.generate_alternatives(scenario, constraints)


__all__ = [
    "BaseReasoningProvider",
    "ReasoningCapability",
    "ReasoningResult",
    "ReasoningStep",
    "ReasoningType",
]
