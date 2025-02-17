"""Collaborative research example.

This example demonstrates a complex workflow with multiple agents working together:
- Research Agent: Finds and collects information
- Analysis Agent: Processes and analyzes the data
- Writing Agent: Generates the final report
- Coordinator Agent: Orchestrates the workflow

Example:
    $ python examples/use_cases/collaborative_research.py

Requirements:
    - Python 3.9+
    - pydantic
    - rich (for pretty printing)

"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any, Dict, List, Set

from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)
console = Console()


class MetricsTracker:
    """Tracks metrics for all agents."""

    def __init__(self) -> None:
        """Initialize tracker."""
        self.metrics: Dict[str, Dict[str, float]] = {}
        self.start_time = datetime.now(UTC)

    def track(self, agent: str, name: str, value: float = 1.0) -> None:
        """Track a metric for an agent."""
        if agent not in self.metrics:
            self.metrics[agent] = {}
        self.metrics[agent][name] = self.metrics[agent].get(name, 0) + value
        logger.info("Metric [%s]: %s = %.2f", agent, name, self.metrics[agent][name])

    def get_summary(self) -> Dict[str, Any]:
        """Get metrics summary."""
        duration = (datetime.now(UTC) - self.start_time).total_seconds()
        return {
            "duration": duration,
            "metrics": self.metrics,
        }


# Initialize global metrics
metrics = MetricsTracker()


@dataclass
class ResearchData:
    """Research data structure."""

    topic: str
    sources: List[Dict[str, Any]]
    timestamp: str = field(default_factory=lambda: datetime.now(UTC).isoformat())


@dataclass
class AnalysisResult:
    """Analysis result structure."""

    key_findings: List[str]
    trends: List[str]
    implications: List[str]
    confidence: float
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Report:
    """Final report structure."""

    title: str
    content: str
    sections: List[Dict[str, Any]]
    references: List[Dict[str, Any]]
    metadata: Dict[str, Any] = field(default_factory=dict)


class AgentState(str, Enum):
    """Agent states."""

    IDLE = "idle"
    INITIALIZING = "initializing"
    READY = "ready"
    WORKING = "working"
    ERROR = "error"
    CLEANED = "cleaned"


class BaseAgent:
    """Base agent implementation."""

    def __init__(self, name: str) -> None:
        """Initialize agent."""
        self.name = name
        self.state = AgentState.IDLE
        self.dependencies: Set[str] = set()
        self.initialized = False

    async def initialize(self) -> None:
        """Initialize the agent."""
        if self.initialized:
            logger.warning("Agent already initialized: %s", self.name)
            return

        self.state = AgentState.INITIALIZING
        metrics.track(self.name, "initialization")

        await self._initialize()
        self.initialized = True
        self.state = AgentState.READY
        logger.info("Agent initialized: %s", self.name)

    async def cleanup(self) -> None:
        """Clean up agent resources."""
        if not self.initialized:
            logger.warning("Agent not initialized: %s", self.name)
            return

        metrics.track(self.name, "cleanup")
        await self._cleanup()
        self.initialized = False
        self.state = AgentState.CLEANED
        logger.info("Agent cleaned up: %s", self.name)

    async def _initialize(self) -> None:
        """Initialize implementation."""
        pass

    async def _cleanup(self) -> None:
        """Cleanup implementation."""
        pass


class ResearchAgent(BaseAgent):
    """Agent responsible for finding information."""

    def __init__(self) -> None:
        """Initialize research agent."""
        super().__init__("research_agent")

    async def research(self, topic: str) -> ResearchData:
        """Perform research on a topic.

        Args:
            topic: Research topic

        Returns:
            Research data

        """
        self.state = AgentState.WORKING
        metrics.track(self.name, "research.started")

        # Simulate research process
        await asyncio.sleep(1)  # Simulated work

        # Generate research data
        sources = [
            {
                "title": "AI in Software Development",
                "content": "Analysis of AI impact on coding practices...",
                "relevance": 0.9,
            },
            {
                "title": "Future of Programming",
                "content": "Trends in software development with AI...",
                "relevance": 0.85,
            },
            {
                "title": "AI Tools Survey",
                "content": "Survey of popular AI development tools...",
                "relevance": 0.8,
            },
        ]

        metrics.track(self.name, "research.completed")
        self.state = AgentState.READY

        return ResearchData(
            topic=topic,
            sources=sources,
        )


class AnalysisAgent(BaseAgent):
    """Agent responsible for analyzing data."""

    def __init__(self) -> None:
        """Initialize analysis agent."""
        super().__init__("analysis_agent")

    async def analyze(self, data: ResearchData) -> AnalysisResult:
        """Analyze research data.

        Args:
            data: Research data to analyze

        Returns:
            Analysis results

        """
        self.state = AgentState.WORKING
        metrics.track(self.name, "analysis.started")

        # Simulate analysis process
        await asyncio.sleep(1.5)  # Simulated work

        # Generate analysis results
        key_findings = [
            "AI tools significantly improve developer productivity",
            "Code quality increases with AI assistance",
            "Learning curve exists for AI tool adoption",
        ]

        trends = [
            "Increased adoption of AI pair programming",
            "Focus on AI-powered code review",
            "Integration of AI in testing workflows",
        ]

        implications = [
            "Need for AI literacy in development teams",
            "Changes in development workflows",
            "Evolution of programming practices",
        ]

        metrics.track(self.name, "analysis.completed")
        self.state = AgentState.READY

        return AnalysisResult(
            key_findings=key_findings,
            trends=trends,
            implications=implications,
            confidence=0.85,
        )


class WritingAgent(BaseAgent):
    """Agent responsible for writing reports."""

    def __init__(self) -> None:
        """Initialize writing agent."""
        super().__init__("writing_agent")

    async def write_report(
        self,
        topic: str,
        data: ResearchData,
        analysis: AnalysisResult,
    ) -> Report:
        """Generate a report.

        Args:
            topic: Report topic
            data: Research data
            analysis: Analysis results

        Returns:
            Generated report

        """
        self.state = AgentState.WORKING
        metrics.track(self.name, "writing.started")

        # Simulate report writing
        await asyncio.sleep(1)  # Simulated work

        # Generate report sections
        sections = [
            {
                "title": "Executive Summary",
                "content": "Overview of findings and implications...",
            },
            {
                "title": "Key Findings",
                "content": "\n".join(f"- {f}" for f in analysis.key_findings),
            },
            {
                "title": "Trends",
                "content": "\n".join(f"- {t}" for t in analysis.trends),
            },
            {
                "title": "Implications",
                "content": "\n".join(f"- {i}" for i in analysis.implications),
            },
        ]

        # Generate references from sources
        references = [
            {
                "title": source["title"],
                "relevance": source["relevance"],
            }
            for source in data.sources
        ]

        metrics.track(self.name, "writing.completed")
        self.state = AgentState.READY

        return Report(
            title=f"Research Report: {topic}",
            content="Comprehensive analysis of AI in software development...",
            sections=sections,
            references=references,
            metadata={
                "confidence": analysis.confidence,
                "generated_at": datetime.now(UTC).isoformat(),
            },
        )


class CoordinatorAgent(BaseAgent):
    """Agent responsible for coordinating the workflow."""

    def __init__(self) -> None:
        """Initialize coordinator agent."""
        super().__init__("coordinator")
        self.research_agent = ResearchAgent()
        self.analysis_agent = AnalysisAgent()
        self.writing_agent = WritingAgent()
        self.dependencies = {"research_agent", "analysis_agent", "writing_agent"}

    async def _initialize(self) -> None:
        """Initialize all managed agents."""
        await self.research_agent.initialize()
        await self.analysis_agent.initialize()
        await self.writing_agent.initialize()

    async def _cleanup(self) -> None:
        """Clean up all managed agents."""
        await self.research_agent.cleanup()
        await self.analysis_agent.cleanup()
        await self.writing_agent.cleanup()

    async def execute_workflow(self, topic: str) -> Report:
        """Execute the complete research workflow.

        Args:
            topic: Research topic

        Returns:
            Final report

        """
        self.state = AgentState.WORKING
        metrics.track(self.name, "workflow.started")

        try:
            # Step 1: Research
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                progress.add_task("Researching...", total=None)
                research_data = await self.research_agent.research(topic)

            # Step 2: Analysis
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                progress.add_task("Analyzing...", total=None)
                analysis_results = await self.analysis_agent.analyze(research_data)

            # Step 3: Report Writing
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                progress.add_task("Writing report...", total=None)
                report = await self.writing_agent.write_report(
                    topic, research_data, analysis_results
                )

            metrics.track(self.name, "workflow.completed")
            self.state = AgentState.READY
            return report

        except Exception as e:
            self.state = AgentState.ERROR
            metrics.track(self.name, "workflow.errors")
            logger.error("Workflow failed: %s", str(e))
            raise


def print_report(report: Report) -> None:
    """Print the report in a formatted way."""
    console.print("\n")
    console.print(Panel(f"[bold blue]{report.title}[/]"))

    # Print sections
    for section in report.sections:
        console.print(f"\n[bold green]{section['title']}[/]")
        console.print(section["content"])

    # Print references
    console.print("\n[bold yellow]References[/]")
    for ref in report.references:
        console.print(f"- {ref['title']} (Relevance: {ref['relevance']:.2f})")

    # Print metadata
    console.print("\n[bold magenta]Metadata[/]")
    for key, value in report.metadata.items():
        console.print(f"{key}: {value}")

    # Print metrics
    console.print("\n[bold cyan]Performance Metrics[/]")
    metrics_data = metrics.get_summary()
    console.print(f"Total Duration: {metrics_data['duration']:.2f} seconds")
    for agent, agent_metrics in metrics_data["metrics"].items():
        console.print(f"\n[bold]{agent}[/]")
        for name, value in agent_metrics.items():
            console.print(f"  {name}: {value}")


async def main() -> None:
    """Run the collaborative research example."""
    coordinator = None

    try:
        # Create and initialize coordinator
        coordinator = CoordinatorAgent()
        await coordinator.initialize()

        # Execute research workflow
        topic = "Impact of AI on Software Development Practices"
        logger.info("Starting research workflow for topic: %s", topic)

        report = await coordinator.execute_workflow(topic)
        print_report(report)

    except KeyboardInterrupt:
        logger.info("Workflow interrupted by user")
    except Exception as e:
        logger.error("Example failed: %s", e)
        raise
    finally:
        if coordinator:
            await coordinator.cleanup()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Example interrupted by user")
    except Exception as e:
        logger.error("Example failed: %s", e)
        raise
