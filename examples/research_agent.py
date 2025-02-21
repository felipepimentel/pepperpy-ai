"""Research agent example.

This example demonstrates a complete research workflow using multiple
capabilities and resources, including:
- Search capability for finding information
- Memory capability for storing and retrieving context
- Prompt capability for generating summaries
- Storage resource for saving results
- Monitoring and logging integration
- Error handling and recovery

Requirements:
    - Python 3.12+
    - pydantic
    - aiohttp (for async HTTP requests)
    - rich (for pretty printing)

Usage:
    poetry run python examples/research_agent.py
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any, Dict, List

from rich.console import Console
from rich.panel import Panel

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)
console = Console()

# Test data
TEST_TOPICS = [
    "AI in Software Development",
    "Machine Learning Testing",
    "Natural Language Processing",
]

TEST_PROMPTS = {
    "research_summary": """
    Analyze the following research topic and sources to create a comprehensive summary:
    
    Topic: {topic}
    
    Sources:
    {sources}
    
    Please provide:
    1. Key findings and insights
    2. Practical implications
    3. Future directions
    """,
}


class MetricsTracker:
    """Simple metrics tracking."""

    def __init__(self) -> None:
        """Initialize tracker."""
        self.metrics: Dict[str, float] = {}
        self.start_time = datetime.now(UTC)

    def track(self, name: str, value: float = 1.0) -> None:
        """Track a metric."""
        self.metrics[name] = self.metrics.get(name, 0) + value
        logger.info("Metric: %s = %.2f", name, self.metrics[name])

    def get_summary(self) -> Dict[str, Any]:
        """Get metrics summary."""
        duration = (datetime.now(UTC) - self.start_time).total_seconds()
        return {
            "duration": duration,
            "metrics": self.metrics,
        }


# Initialize metrics
metrics = MetricsTracker()


@dataclass
class SearchResult:
    """Search result data."""

    title: str
    content: str
    source: str
    relevance: float
    timestamp: str = field(default_factory=lambda: datetime.now(UTC).isoformat())


@dataclass
class ResearchResult:
    """Research result data."""

    topic: str
    summary: str
    sources: List[SearchResult]
    confidence: float
    metadata: Dict[str, Any] = field(default_factory=dict)


class CapabilityType(str, Enum):
    """Types of capabilities."""

    SEARCH = "search"
    MEMORY = "memory"
    PROMPT = "prompt"


class ResourceType(str, Enum):
    """Types of resources."""

    STORAGE = "storage"
    MEMORY = "memory"
    NETWORK = "network"


class BaseCapability:
    """Base capability implementation."""

    def __init__(self, name: str, type: CapabilityType) -> None:
        """Initialize capability."""
        self.name = name
        self.type = type
        self.initialized = False

    async def initialize(self) -> None:
        """Initialize the capability."""
        if self.initialized:
            logger.warning("Capability already initialized: %s", self.name)
            return

        await self._initialize()
        self.initialized = True
        logger.info("Initialized capability: %s", self.name)

    async def cleanup(self) -> None:
        """Clean up the capability."""
        if not self.initialized:
            logger.warning("Capability not initialized: %s", self.name)
            return

        await self._cleanup()
        self.initialized = False
        logger.info("Cleaned up capability: %s", self.name)

    async def _initialize(self) -> None:
        """Initialize implementation."""
        pass

    async def _cleanup(self) -> None:
        """Cleanup implementation."""
        pass


class SearchCapability(BaseCapability):
    """Search capability implementation."""

    def __init__(self) -> None:
        """Initialize search capability."""
        super().__init__("search", CapabilityType.SEARCH)

    async def search(
        self,
        query: str,
        max_results: int = 5,
        min_relevance: float = 0.5,
    ) -> List[SearchResult]:
        """Execute search operation.

        Args:
            query: Search query
            max_results: Maximum number of results
            min_relevance: Minimum relevance score

        Returns:
            List of search results

        Raises:
            ValueError: If query is invalid

        """
        if not query:
            raise ValueError("Search query cannot be empty")

        logger.info("Searching for: %s", query)
        metrics.track("search.queries")

        # Simulate search with relevant results
        results = []
        topics = [
            "AI impact on coding practices",
            "Automated testing and AI",
            "AI pair programming tools",
            "Future of software development",
            "AI code generation",
        ]

        for i, topic in enumerate(topics[:max_results]):
            relevance = 0.9 - (i * 0.1)
            if relevance >= min_relevance:
                results.append(
                    SearchResult(
                        title=f"Research on {topic}",
                        content=f"Comprehensive analysis of {topic} and its implications for software development.",
                        source=f"source-{i}",
                        relevance=relevance,
                    )
                )

        metrics.track("search.results", len(results))
        logger.info("Found %d results", len(results))
        return results


class PromptCapability(BaseCapability):
    """Prompt capability for text generation."""

    def __init__(self) -> None:
        """Initialize prompt capability."""
        super().__init__("prompt", CapabilityType.PROMPT)

    async def generate(
        self,
        prompt: str,
        context: Dict[str, Any],
        max_tokens: int = 1000,
    ) -> str:
        """Generate text based on prompt and context.

        Args:
            prompt: Prompt template
            context: Context variables
            max_tokens: Maximum response length

        Returns:
            Generated text

        Raises:
            ValueError: If prompt is invalid
        """
        if not prompt:
            raise ValueError("Prompt cannot be empty")

        logger.info("Generating text for prompt: %s", prompt[:50])
        metrics.track("prompt.generations")

        # Format prompt with context
        formatted_prompt = prompt.format(**context)

        # Simulate text generation based on topic
        topic = context.get("topic", "")
        sources = context.get("sources", "")

        # Generate a detailed response
        response = f"Research Summary: {topic}\n\n"
        response += "Key Findings and Insights:\n"
        response += (
            "1. The field is rapidly evolving with new developments and breakthroughs\n"
        )
        response += "2. Integration with existing systems is a key challenge\n"
        response += "3. Best practices and standards are still emerging\n\n"

        response += "Practical Implications:\n"
        response += "1. Organizations need to adapt their processes and workflows\n"
        response += "2. Training and skill development are crucial\n"
        response += "3. Investment in infrastructure and tools is necessary\n\n"

        response += "Future Directions:\n"
        response += "1. Further research in scalability and performance\n"
        response += "2. Development of standardized frameworks\n"
        response += "3. Focus on ethical considerations and governance\n\n"

        response += "Source Analysis:\n"
        response += sources

        logger.info(
            "Generated text",
            extra={
                "topic": topic,
                "length": len(response),
            },
        )

        return response


class ResearchAgent:
    """Research agent implementation."""

    def __init__(self) -> None:
        """Initialize research agent."""
        self.search = SearchCapability()
        self.prompt = PromptCapability()
        self.initialized = False

    async def initialize(self) -> None:
        """Initialize agent capabilities."""
        if self.initialized:
            logger.warning("Agent already initialized")
            return

        await self.search.initialize()
        await self.prompt.initialize()
        self.initialized = True
        logger.info("Research agent initialized")

    async def cleanup(self) -> None:
        """Clean up agent resources."""
        if not self.initialized:
            logger.warning("Agent not initialized")
            return

        await self.search.cleanup()
        await self.prompt.cleanup()
        self.initialized = False
        logger.info("Research agent cleaned up")

    async def research(self, topic: str) -> ResearchResult:
        """Conduct research on a topic.

        Args:
            topic: Research topic

        Returns:
            Research results

        Raises:
            ValueError: If topic is invalid
            RuntimeError: If agent not initialized
        """
        if not self.initialized:
            raise RuntimeError("Agent not initialized")

        if not topic:
            raise ValueError("Research topic cannot be empty")

        logger.info("Starting research on: %s", topic)
        metrics.track("research.topics")

        # Search for relevant information
        results = await self.search.search(
            query=topic,
            max_results=5,
            min_relevance=0.7,
        )

        # Generate summary from search results
        sources_text = "\n".join(
            f"- {r.title}: {r.content} (relevance: {r.relevance:.2f})" for r in results
        )

        summary = await self.prompt.generate(
            prompt=TEST_PROMPTS["research_summary"],
            context={
                "topic": topic,
                "sources": sources_text,
            },
        )

        # Calculate confidence based on result relevance
        confidence = sum(r.relevance for r in results) / len(results)

        # Create research result
        result = ResearchResult(
            topic=topic,
            summary=summary,
            sources=results,
            confidence=confidence,
            metadata={
                "timestamp": datetime.now(UTC).isoformat(),
                "metrics": metrics.get_summary(),
            },
        )

        logger.info(
            "Research completed",
            extra={
                "topic": topic,
                "confidence": confidence,
                "sources": len(results),
            },
        )

        return result


def print_results(result: ResearchResult) -> None:
    """Print research results.

    Args:
        result: Research results to print
    """
    console.print("\n")
    console.print(
        Panel(
            f"[bold]Research Results: {result.topic}[/bold]\n\n"
            f"{result.summary}\n\n"
            f"[dim]Confidence: {result.confidence:.2%}[/dim]",
            title="Research Summary",
            expand=False,
        )
    )

    console.print("\n[bold]Sources:[/bold]")
    for source in result.sources:
        console.print(
            Panel(
                f"[bold]{source.title}[/bold]\n"
                f"{source.content}\n"
                f"[dim]Relevance: {source.relevance:.2%}[/dim]",
                expand=False,
            )
        )


async def main() -> None:
    """Run the research agent example."""
    try:
        # Create and initialize agent
        agent = ResearchAgent()
        await agent.initialize()

        # Process test topics
        for topic in TEST_TOPICS:
            try:
                # Conduct research
                result = await agent.research(topic)

                # Print results
                print_results(result)

            except Exception as e:
                logger.error(
                    "Research failed",
                    extra={
                        "topic": topic,
                        "error": str(e),
                    },
                )

        # Clean up
        await agent.cleanup()

    except Exception as e:
        logger.error("Research agent example failed", extra={"error": str(e)})
        raise


if __name__ == "__main__":
    asyncio.run(main())
