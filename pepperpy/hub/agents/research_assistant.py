"""Research assistant agent implementation.

This module provides a specialized agent for conducting research tasks, including
topic analysis, source discovery, and information synthesis.
"""

from typing import Any, Dict, List, Optional
from uuid import uuid4

from pydantic import BaseModel

from pepperpy.core.client import PepperpyClient
from pepperpy.monitoring import logger

log = logger.bind(agent="research_assistant")


class ResearchAssistantConfig(BaseModel):
    """Configuration for the research assistant agent."""

    name: str
    description: str
    version: str
    max_sources: int = 5
    min_confidence: float = 0.7


class ResearchAssistantAgent:
    """Agent specialized in conducting research tasks.

    This agent can analyze topics, find relevant sources, and synthesize information
    to provide comprehensive research outputs.
    """

    def __init__(self, client: PepperpyClient, config: Dict[str, Any]) -> None:
        """Initialize the research assistant agent.

        Args:
        ----
            client: The Pepperpy client instance
            config: Agent configuration

        """
        self.id = uuid4()
        self.client = client
        self.config = ResearchAssistantConfig(**config)

    async def research(
        self,
        topic: str,
        max_sources: Optional[int] = None,
        report_progress: bool = True,
    ) -> Dict[str, Any]:
        """Conduct comprehensive research on a topic.

        This high-level method orchestrates the entire research workflow, including
        topic analysis, source discovery, and synthesis.

        Args:
        ----
            topic: The research topic to analyze
            max_sources: Maximum number of sources to find (overrides config)
            report_progress: Whether to report progress during execution

        Returns:
        -------
            Dictionary containing research outputs (summary, sources, recommendations)

        """
        outputs = {}
        max_sources = max_sources or self.config.max_sources

        # Step 1: Initial research
        if report_progress:
            log.info("Performing initial research...")
        analysis = await self.analyze_topic(topic=topic)
        outputs["summary"] = analysis
        if report_progress:
            log.info("Topic analysis complete", topic=topic)

        # Step 2: Source analysis
        if report_progress:
            log.info("Finding and analyzing sources...")
        sources = await self.find_sources(topic=topic, max_sources=max_sources)
        outputs["sources"] = sources
        if report_progress:
            log.info("Source analysis complete", num_sources=len(sources))

        # Step 3: Synthesize findings
        if sources:
            if report_progress:
                log.info("Synthesizing findings...")
            synthesis = await self.analyze_sources(sources=sources)
            outputs["recommendations"] = synthesis
            if report_progress:
                log.info("Synthesis complete")

        return outputs

    async def analyze_topic(self, topic: str) -> str:
        """Analyze a research topic.

        Args:
        ----
            topic: The topic to analyze

        Returns:
        -------
            Analysis of the topic

        """
        prompt = f"Analyze the following research topic: {topic}"
        response = await self.client.send_message(prompt)
        return response

    async def find_sources(
        self, topic: str, max_sources: Optional[int] = None
    ) -> List[str]:
        """Find relevant sources for a topic.

        Args:
        ----
            topic: The topic to find sources for
            max_sources: Maximum number of sources to find

        Returns:
        -------
            List of relevant sources

        """
        max_sources = max_sources or self.config.max_sources
        prompt = f"Find up to {max_sources} relevant sources for: {topic}"
        response = await self.client.send_message(prompt)
        return response.split("\n")

    async def analyze_sources(self, sources: List[str]) -> str:
        """Analyze and synthesize information from sources.

        Args:
        ----
            sources: List of sources to analyze

        Returns:
        -------
            Synthesis of the information

        """
        sources_text = "\n".join(sources)
        prompt = (
            f"Analyze and synthesize information from these sources:\n{sources_text}"
        )
        response = await self.client.send_message(prompt)
        return response
