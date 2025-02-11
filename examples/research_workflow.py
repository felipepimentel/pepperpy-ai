#!/usr/bin/env python3
"""Example of using the research workflow.

This example demonstrates how to create and execute a research workflow
that analyzes a topic and finds relevant sources.
"""

import json
from typing import Any, Dict, Optional

from pepperpy.hub.agents import AgentConfig, AgentRegistry, ResearchAssistantAgent
from pepperpy.hub.prompts import PromptRegistry
from pepperpy.hub.workflows import (
    Workflow,
    WorkflowConfig,
    WorkflowRegistry,
    WorkflowStep,
)
from pepperpy.providers import Provider


class OpenRouterProvider(Provider):
    """OpenRouter API provider."""

    async def generate(self, prompt: str, parameters: Optional[Dict[str, Any]] = None) -> str:
        """Generate a response using the OpenRouter API.

        Args:
            prompt: The prompt to generate from.
            parameters: Optional generation parameters.

        Returns:
            The generated response as a JSON string.
        """
        # TODO: Implement actual API call
        if "topic analysis" in prompt.lower():
            return json.dumps({
                "key_concepts": [
                    "Large Language Models (LLMs)",
                    "Natural Language Processing",
                    "Machine Learning",
                    "Scientific Research",
                ],
                "current_state": "LLMs are revolutionizing scientific research...",
                "challenges": [
                    "Reproducibility",
                    "Bias and fairness",
                    "Resource requirements",
                ],
                "future_directions": [
                    "Improved interpretability",
                    "Domain-specific models",
                    "Collaborative research tools",
                ],
            })
        else:
            return json.dumps([
                {
                    "title": "The Impact of Large Language Models on Scientific Discovery",
                    "authors": ["Smith, J.", "Johnson, A."],
                    "summary": "Comprehensive review of LLM applications in science",
                },
                {
                    "title": "Challenges and Opportunities in Scientific LLMs",
                    "authors": ["Brown, R.", "Davis, M."],
                    "summary": "Analysis of current limitations and future potential",
                },
            ])


async def main():
    """Run the research workflow example."""
    # Create a provider
    provider = OpenRouterProvider({
        "model": "gpt-4-turbo-preview",
    })

    # Create an agent
    agent = ResearchAssistantAgent(AgentConfig(provider=provider))
    AgentRegistry.register("research_assistant", agent)

    # Create prompts
    PromptRegistry.register(
        "analyze_topic",
        """Analyze the following research topic: {topic}

        Provide a structured analysis including:
        1. Key concepts and definitions
        2. Current state of research
        3. Major challenges and open questions
        4. Future research directions

        Format your response as a JSON object with these sections as keys.
        """,
    )

    PromptRegistry.register(
        "find_sources",
        """Find relevant sources for the research topic: {topic}

        Consider the following aspects:
        1. Recent academic papers
        2. Review articles
        3. Technical reports
        4. Expert opinions

        List up to {max_sources} sources.
        Format your response as a JSON array of objects with 'title', 'authors', and 'summary' fields.
        """,
    )

    # Create workflow steps
    initial_research = WorkflowStep(
        name="initial_research",
        agent=agent,
        prompt=PromptRegistry.get("analyze_topic"),
        inputs={"topic": "topic"},
        outputs={"analysis": "analysis"},
    )

    source_analysis = WorkflowStep(
        name="source_analysis",
        agent=agent,
        prompt=PromptRegistry.get("find_sources"),
        inputs={"topic": "topic", "max_sources": "max_sources"},
        outputs={"sources": "sources"},
    )

    # Create workflow
    workflow_config = WorkflowConfig(
        name="research_workflow",
        description="Analyze a research topic and find relevant sources",
        steps=[initial_research, source_analysis],
        inputs={"topic": str, "max_sources": int},
        outputs={"analysis": dict, "sources": list},
    )

    workflow = Workflow(workflow_config)
    WorkflowRegistry.register("research", workflow)

    # Execute workflow
    results = await workflow.execute({
    results = await workflow.execute(
        {
            "topic": "Large Language Models and their impact on scientific research",
            "max_sources": 5,
        }
    )

    print("Analysis:", results["analysis"])
    print("\nSources:", results["sources"])


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
