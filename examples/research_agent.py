"""Research agent example.

This example demonstrates a complete research workflow using multiple
capabilities and resources, including:
- Search capability for finding information
- Memory capability for storing and retrieving context
- Prompt capability for generating summaries
- Storage resource for saving results
- Monitoring and logging integration
- Error handling and recovery

Example:
    $ python examples/use_cases/research_agent.py

Requirements:
    - Python 3.9+
    - pydantic
    - aiohttp (for async HTTP requests)
    - rich (for pretty printing)

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

        # Simulate text generation
        topic = context.get("topic", "")
        sources = context.get("sources", [])

        # Generate a more detailed response based on the sources
        response = f"Research Summary: {topic}\n\n"
        response += "Key Findings:\n"

        for i, source in enumerate(sources, 1):
            response += f"\n{i}. {source.title}\n"
            response += f"   {source.content}\n"
            response += (
                f"   Source: {source.source} (Relevance: {source.relevance:.2f})\n"
            )

        response += "\nConclusion:\n"
        response += (
            f"Based on the analyzed sources, {topic} has significant implications "
        )
        response += (
            "for the software development industry. The research indicates multiple "
        )
        response += "transformative trends and potential future developments."

        metrics.track("prompt.tokens", len(response.split()))
        return response


class ResearchAgent:
    """Research agent implementation."""

    def __init__(self) -> None:
        """Initialize the research agent."""
        self.search = SearchCapability()
        self.prompt = PromptCapability()
        self.initialized = False

    async def initialize(self) -> None:
        """Initialize agent capabilities."""
        if self.initialized:
            return

        logger.info("Initializing research agent")
        metrics.track("agent.initialization")

        await self.search.initialize()
        await self.prompt.initialize()
        self.initialized = True

    async def cleanup(self) -> None:
        """Clean up agent resources."""
        if not self.initialized:
            return

        logger.info("Cleaning up research agent")
        metrics.track("agent.cleanup")

        await self.search.cleanup()
        await self.prompt.cleanup()
        self.initialized = False

    async def research(self, topic: str) -> ResearchResult:
        """Execute research workflow.

        Args:
            topic: Research topic

        Returns:
            Research results

        Raises:
            ValueError: If topic is invalid
            RuntimeError: If research fails

        """
        if not self.initialized:
            raise RuntimeError("Agent not initialized")

        if not topic:
            raise ValueError("Research topic cannot be empty")

        logger.info("Starting research on: %s", topic)
        metrics.track("agent.research.started")

        try:
            # Search for information
            search_results = await self.search.search(
                query=topic,
                max_results=5,
                min_relevance=0.7,
            )

            if not search_results:
                raise RuntimeError("No search results found")

            # Generate summary
            summary_prompt = """
            Analyze and summarize research findings about {topic}:

            Sources:
            {sources}

            Provide a comprehensive summary focusing on key insights.
            """

            summary = await self.prompt.generate(
                prompt=summary_prompt,
                context={
                    "topic": topic,
                    "sources": search_results,
                },
            )

            # Create research result
            result = ResearchResult(
                topic=topic,
                summary=summary,
                sources=search_results,
                confidence=0.85,
                metadata={
                    "timestamp": datetime.now(UTC).isoformat(),
                    "metrics": metrics.get_summary(),
                },
            )

            metrics.track("agent.research.completed")
            logger.info("Research completed successfully")

            return result

        except Exception as e:
            metrics.track("agent.research.errors")
            logger.error("Research failed: %s", str(e))
            raise


def print_results(result: ResearchResult) -> None:
    """Print research results in a formatted way."""
    console.print("\n")
    console.print(Panel(f"[bold blue]Research Topic:[/] {result.topic}"))
    console.print("\n[bold green]Summary:[/]")
    console.print(result.summary)

    console.print("\n[bold yellow]Sources:[/]")
    for i, source in enumerate(result.sources, 1):
        console.print(f"\n{i}. [bold]{source.title}[/]")
        console.print(f"   Content: {source.content}")
        console.print(f"   Source: {source.source}")
        console.print(f"   Relevance: {source.relevance:.2f}")

    console.print("\n[bold magenta]Metrics:[/]")
    metrics_data = result.metadata["metrics"]
    console.print(f"Duration: {metrics_data['duration']:.2f} seconds")
    for name, value in metrics_data["metrics"].items():
        console.print(f"{name}: {value}")


async def main() -> None:
    """Run the research agent example."""
    agent = None

    try:
        # Create and initialize agent
        agent = ResearchAgent()
        await agent.initialize()

        # Use a predefined research topic
        topic = "Impact of AI on software development"
        logger.info("Starting research on topic: %s", topic)

        # Execute research
        result = await agent.research(topic)

        # Print results
        print_results(result)

    except KeyboardInterrupt:
        logger.info("Research interrupted by user")
    except Exception as e:
        logger.error("Example failed: %s", e)
        raise
    finally:
        if agent:
            await agent.cleanup()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Example interrupted by user")
    except Exception as e:
        logger.error("Example failed: %s", e)
        raise
